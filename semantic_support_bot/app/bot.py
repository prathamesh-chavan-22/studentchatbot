import json
import asyncio
from typing import Any
import numpy as np
from sentence_transformers import SentenceTransformer, util
from loguru import logger
from pathlib import Path
from langdetect import detect, DetectorFactory
import faiss

from app.batcher import AsyncBatcher
from app.exceptions import (
    BotError,
    ModelLoadError,
    CacheError,
    CacheCorruptionError,
    IndexBuildError,
    InferenceError,
    InferenceTimeoutError,
    KnowledgeBaseError,
    KnowledgeBaseEmptyError,
    QAFileError,
    QAFileParseError,
    SearchError,
    FaissIndexError,
    EmptyInputError,
)
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerError
from utils.retry import retry_async, retry_sync

DetectorFactory.seed = 0

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MODEL_LOAD_TIMEOUT = 300  # 5 minutes max for model download/load
_INFERENCE_TIMEOUT = 30  # 30 seconds per inference call
_CACHE_WRITE_RETRY = 3
_CACHE_WRITE_DELAY = 1.0


class SimilarityBot:
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-base",
        qa_json_path: str = "questions_answers.json",
        threshold: float = 0.8750,
        fallback_messages: dict[str, str] | None = None,
    ):
        self.model_name = model_name
        self.qa_json_path = qa_json_path
        self.threshold = threshold
        self.fallback_messages = fallback_messages or {
            "en": "I'm sorry, I couldn't find a close match for your question. Questions? Please contact support at: support@mahafyjcadmissions.in",
            "mr": "क्षमस्व, तुमच्या प्रश्नाशी जुळणारे उत्तर सापडले नाही. काही प्रश्न असल्यास, कृपया या ईमेलवर संपर्क करा: support@mahafyjcadmissions.in",
            "hi": "क्षमा करें, मुझे आपके प्रश्न का कोई सटीक उत्तर नहीं मिला। अधिक जानकारी के लिए कृपया support@mahafyjcadmissions.in पर संपर्क करें।",
            "hinglish": "Maaf karna, mujhe aapke sawaal ka sahi jawab nahi mila. Agar aapko madad chahiye toh email karein: support@mahafyjcadmissions.in"
        }
        self.base_dir = Path(__file__).resolve().parent.parent
        self.full_qa_path = self.base_dir / self.qa_json_path

        # Circuit breakers for external dependencies
        self._model_cb = CircuitBreaker(
            name="model_inference", failure_threshold=5, recovery_timeout=60.0
        )
        self._faiss_cb = CircuitBreaker(
            name="faiss_search", failure_threshold=10, recovery_timeout=30.0
        )

        # State — intentionally None until loaded
        self.model: SentenceTransformer | None = None
        self.knowledge_base: list[dict] = []
        self.question_pool: list[str] = []
        self.answers_map: list[dict] = []
        self.index: faiss.IndexFlatIP | None = None
        self.question_embeddings: Any = None
        self.supported_langs = ["en", "mr", "hi", "hinglish"]
        self._is_initialized = False  # tracks successful init

        self.cache_dir = self.base_dir / ".bot_cache"
        self.index_path = self.cache_dir / "faiss_index.bin"
        self.map_path = self.cache_dir / "answers_map.json"
        self.metadata_path = self.cache_dir / "metadata.json"

        self.batcher: AsyncBatcher | None = None
        self._load_model()
        self._init_batcher()
        self.load_qa()

    # ------------------------------------------------------------------
    # Model loading (with retry)
    # ------------------------------------------------------------------

    def _load_model(self):
        """Load the sentence-transformer model with retry logic."""
        logger.info(f"Loading model: {self.model_name} (timeout={_MODEL_LOAD_TIMEOUT}s)")

        def _do_load():
            return SentenceTransformer(self.model_name)

        try:
            self.model = retry_sync(
                _do_load,
                max_retries=2,
                base_delay=2.0,
                max_delay=30.0,
                operation_name="model_load",
            )
            logger.success(f"Model '{self.model_name}' loaded successfully.")
        except Exception as exc:
            logger.critical(
                f"Failed to load model '{self.model_name}' after retries: {exc}"
            )
            raise ModelLoadError(
                f"Unable to load embedding model '{self.model_name}'", original=exc
            ) from exc

    # ------------------------------------------------------------------
    # Batcher lifecycle
    # ------------------------------------------------------------------

    def _init_batcher(self):
        """Initialize and start the async batcher."""
        if self.model is None:
            logger.error("Cannot start batcher: model not loaded")
            return

        try:
            self.batcher = AsyncBatcher(self.model, max_batch_size=32, wait_seconds=0.05)
            self.batcher.start()
            logger.info("AsyncBatcher started.")
        except Exception as exc:
            logger.error(f"Failed to start AsyncBatcher: {exc}")
            # Continue without batcher — fallback to sync inference
            self.batcher = None

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _get_cache_metadata(self) -> dict:
        stat = self.full_qa_path.stat() if self.full_qa_path.exists() else None
        return {
            "model_name": self.model_name,
            "qa_json_mtime": stat.st_mtime if stat else 0,
            "qa_json_size": stat.st_size if stat else 0,
            "total_questions": len(self.answers_map),
        }

    def _is_cache_valid(self) -> bool:
        if not all(p.exists() for p in (self.index_path, self.map_path, self.metadata_path)):
            logger.debug("Cache files incomplete — at least one missing")
            return False
        try:
            with open(self.metadata_path, encoding="utf-8") as f:
                cached = json.load(f)
            current = self._get_cache_metadata()
            valid = all(
                cached.get(k) == current[k]
                for k in ("model_name", "qa_json_mtime", "qa_json_size")
            )
            if valid:
                logger.debug("Cache validation passed")
            else:
                logger.debug("Cache invalidated: metadata mismatch")
            return valid
        except json.JSONDecodeError as exc:
            logger.warning(f"Cache metadata file is corrupted (bad JSON): {exc}")
            return False
        except OSError as exc:
            logger.warning(f"Error reading cache metadata: {exc}")
            return False
        except Exception as exc:
            logger.warning(f"Unexpected error validating cache: {exc}")
            return False

    def _save_cache(self):
        """Persist FAISS index, answers map, and metadata with retry."""
        if self.index is None:
            logger.warning("Cannot save cache: FAISS index is None")
            return

        for attempt in range(_CACHE_WRITE_RETRY):
            try:
                logger.info("Saving SimilarityBot data to cache...")
                faiss.write_index(self.index, str(self.index_path))
                with open(self.map_path, "w", encoding="utf-8") as f:
                    json.dump(self.answers_map, f, ensure_ascii=False, indent=2)
                with open(self.metadata_path, "w", encoding="utf-8") as f:
                    json.dump(self._get_cache_metadata(), f, indent=2)
                logger.success("Cache saved successfully.")
                return
            except OSError as exc:
                logger.warning(
                    f"Cache write attempt {attempt + 1}/{_CACHE_WRITE_RETRY} failed: {exc}"
                )
                if attempt < _CACHE_WRITE_RETRY - 1:
                    import time
                    time.sleep(_CACHE_WRITE_DELAY)
            except Exception as exc:
                logger.error(f"Unexpected error saving cache: {exc}")
                raise CacheError(f"Failed to save cache", original=exc) from exc

        logger.error("Cache save failed after all retries")

    # ------------------------------------------------------------------
    # QA loading & index building
    # ------------------------------------------------------------------

    def load_qa(self):
        """Load QA data from cache or rebuild the index."""
        if not self.full_qa_path.exists():
            logger.error(f"QA JSON file not found at: {self.full_qa_path}")
            raise QAFileError(f"QA JSON file not found: {self.full_qa_path}")

        if self._is_cache_valid():
            try:
                logger.info("Loading SimilarityBot data from cache...")
                self._load_qa_json()
                self._load_faiss_index()
                self._load_answers_map()
                logger.success(
                    f"Loaded {len(self.knowledge_base)} FAQ sets and "
                    f"{self.index.ntotal} vectors from cache."
                )
                self._is_initialized = True
                return
            except (CacheError, CacheCorruptionError) as exc:
                logger.warning(f"Failed to load cache: {exc}. Recomputing...")
            except Exception as exc:
                logger.warning(f"Unexpected cache load failure: {exc}. Recomputing...")

        self._build_index_from_scratch()

    def _load_qa_json(self):
        """Load and validate the QA JSON file."""
        try:
            with open(self.full_qa_path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise QAFileParseError("QA JSON root is not a list")
            self.knowledge_base = data
        except json.JSONDecodeError as exc:
            raise QAFileParseError(
                f"Failed to parse QA JSON: {exc}", original=exc
            ) from exc
        except OSError as exc:
            raise QAFileError(
                f"Failed to read QA JSON file: {exc}", original=exc
            ) from exc

    def _load_faiss_index(self):
        """Load the FAISS index from disk."""
        try:
            self.index = faiss.read_index(str(self.index_path))
        except Exception as exc:
            logger.error(f"Failed to load FAISS index: {exc}")
            raise CacheCorruptionError(
                f"FAISS index file is corrupted: {exc}", original=exc
            ) from exc

    def _load_answers_map(self):
        """Load the answers map from disk."""
        try:
            with open(self.map_path, encoding="utf-8") as f:
                self.answers_map = json.load(f)
        except json.JSONDecodeError as exc:
            raise CacheCorruptionError(
                f"Answers map JSON is corrupted: {exc}", original=exc
            ) from exc
        except OSError as exc:
            raise CacheError(
                f"Failed to read answers map: {exc}", original=exc
            ) from exc

    def _build_index_from_scratch(self):
        """Parse QA JSON, compute embeddings, and build FAISS index."""
        if not self.full_qa_path.exists():
            logger.error(f"QA JSON file not found at: {self.full_qa_path}")
            raise QAFileError(f"QA JSON file not found: {self.full_qa_path}")

        try:
            self._load_qa_json()

            if not self.knowledge_base:
                raise KnowledgeBaseEmptyError("QA JSON file contains no entries")

            flat_questions: list[str] = []
            self.answers_map = []

            for idx, item in enumerate(self.knowledge_base):
                if "id" not in item:
                    logger.warning(f"QA item at index {idx} missing 'id' — skipping")
                    continue
                faq_id = item["id"]
                for variant in item.get("variants", []):
                    lang = variant.get("lang", "en")
                    answer = variant.get("answer", "")
                    for q in variant.get("questions", []):
                        if not q or not q.strip():
                            logger.debug(f"Skipping empty question in FAQ {faq_id}")
                            continue
                        flat_questions.append(f"passage: {q}")
                        self.answers_map.append({
                            "id": faq_id,
                            "lang": lang,
                            "question": q,
                            "answer": answer,
                        })

            if not flat_questions:
                raise KnowledgeBaseEmptyError(
                    "No valid questions found in QA JSON after parsing"
                )

            logger.info(
                f"Loaded {len(self.knowledge_base)} FAQ sets. "
                f"Total questions in pool: {len(flat_questions)}"
            )
            logger.info(
                "Computing embeddings for all question variants... "
                "(this may take a while)"
            )

            # Compute embeddings with timeout guard
            if self.model is None:
                raise ModelLoadError("Model is not loaded — cannot compute embeddings")

            self.question_embeddings = self.model.encode(
                flat_questions,
                convert_to_tensor=True,
                normalize_embeddings=True,
                show_progress_bar=True,
            )

            dimension = int(self.question_embeddings.shape[1])
            self.index = faiss.IndexFlatIP(dimension)
            embeddings_np = (
                self.question_embeddings.cpu()
                .detach()
                .numpy()
                .astype("float32")
            )
            self.index.add(embeddings_np)
            self._save_cache()
            self._is_initialized = True
            logger.success(f"FAISS index built with {self.index.ntotal} vectors.")
            logger.success("Multilingual embeddings computed and bot is ready.")

        except KnowledgeBaseEmptyError:
            raise
        except QAFileError:
            raise
        except Exception as exc:
            logger.error(f"Error building index: {exc}")
            import traceback
            logger.error(traceback.format_exc())
            raise IndexBuildError(
                f"Failed to build question index: {exc}", original=exc
            ) from exc

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------

    def detect_language(self, text: str) -> str:
        if not text or not text.strip():
            return "en"

        try:
            lang = detect(text)
            logger.debug(f"Detected language for '{text[:30]}...': {lang}")

            hinglish_keywords = [
                "kaise", "kya", "hai", "kahan", "kab", "kyun", "kaun",
                "karna", "karun", "karte", "karo", "hoga", "tha",
                "mera", "tera", "uska", "yeh", "woh",
                "mein", "pe", "se", "ko", "ke", "ki",
                "nahi", "mat", "sirf", "bhi", "hi",
                "chahiye", "sakta", "sakte", "hoti", "hote",
            ]
            text_lower = text.lower()
            hinglish_score = sum(
                1 for word in hinglish_keywords if word in text_lower
            )

            if hinglish_score >= 2:
                logger.debug(f"Hinglish detected (score: {hinglish_score})")
                return "hinglish"
            if lang in self.supported_langs:
                return lang
            if lang in ["ne", "gu", "pa", "sa"]:
                return "mr"
            if lang in ["id", "ms", "sw", "fi"]:
                return "hinglish"
            return "en"
        except Exception as exc:
            logger.warning(f"Language detection failed for '{text[:50]}': {exc}. Defaulting to 'en'.")
            return "en"

    # ------------------------------------------------------------------
    # Public API — answer
    # ------------------------------------------------------------------

    async def answer(self, query: str, history: list | None = None) -> dict:
        """
        Answer a user query using semantic similarity search.

        Returns a dict with keys: answer, score, detected_lang, match_id
        """
        # Guard: empty input
        if not query or not query.strip():
            raise EmptyInputError("Query is empty")

        # Guard: bot not initialized
        if not self._is_initialized or self.model is None:
            logger.error("Bot not fully initialized — model or knowledge base missing")
            return {
                "answer": "I'm sorry, the bot is still initializing. Please try again in a moment.",
                "score": 0,
                "detected_lang": "en",
            }

        if not self.knowledge_base or self.index is None:
            logger.error("Knowledge base or FAISS index is empty — cannot answer")
            return {
                "answer": "I'm sorry, my knowledge base is currently empty or loading.",
                "score": 0,
                "detected_lang": "en",
            }

        try:
            detected_lang = self.detect_language(query)
            query_prefixed = f"query: {query}"

            # Get embedding with circuit breaker + timeout
            query_embedding = await self._get_embedding_with_circuit_breaker(
                query_prefixed
            )

            # Normalise to numpy
            query_embedding_np = self._to_numpy(query_embedding).astype("float32")
            if query_embedding_np.ndim == 1:
                query_embedding_np = query_embedding_np.reshape(1, -1)

            # FAISS search with circuit breaker
            D, I = await self._faiss_search(query_embedding_np, k=1)
            best_idx, best_score = int(I[0][0]), float(D[0][0])

            # Guard: invalid index (FAISS returns -1 for no results)
            if best_idx == -1 or best_idx >= len(self.answers_map):
                logger.warning(
                    f"FAISS returned invalid index {best_idx} for query '{query[:50]}'"
                )
                return {
                    "answer": self._get_unmatched_answer(detected_lang),
                    "score": 0,
                    "detected_lang": detected_lang,
                    "match_id": None,
                }

            best_match_info = self.answers_map[best_idx]
            best_id = best_match_info["id"]
            logger.info(
                f"Query: '{query}' ({detected_lang}) -> "
                f"Best ID: {best_id} (Score: {best_score:.4f})"
            )

            if best_score < self.threshold:
                return {
                    "answer": self._get_unmatched_answer(detected_lang),
                    "score": best_score,
                    "detected_lang": detected_lang,
                    "match_id": None,
                }

            # Resolve the answer from the knowledge base
            final_answer = self._resolve_answer(best_id, detected_lang, best_match_info)

            return {
                "answer": final_answer,
                "score": best_score,
                "match_id": best_id,
                "detected_lang": detected_lang,
            }

        except EmptyInputError:
            raise  # propagate — caller should handle
        except CircuitBreakerError as exc:
            logger.error(f"Circuit breaker tripped during answer: {exc}")
            return {
                "answer": "The answer service is temporarily unavailable. Please try again in a moment.",
                "score": 0,
                "detected_lang": "en",
            }
        except InferenceError as exc:
            logger.error(f"Inference error during answer: {exc}")
            return {
                "answer": "Unable to process your question right now. Please try again.",
                "score": 0,
                "detected_lang": "en",
            }
        except SearchError as exc:
            logger.error(f"Search error during answer: {exc}")
            return {
                "answer": "Unable to search for an answer right now. Please try again later.",
                "score": 0,
                "detected_lang": "en",
            }
        except Exception as exc:
            logger.error(f"Unexpected error during answer for query '{query[:50]}': {exc}")
            import traceback
            logger.debug(traceback.format_exc())
            return {
                "answer": "An unexpected error occurred while processing your question. Please try again.",
                "score": 0,
                "detected_lang": "en",
            }

    async def _get_embedding_with_circuit_breaker(
        self, query_prefixed: str
    ) -> Any:
        """Get embedding through batcher with circuit breaker protection."""
        if self.batcher is not None and self.batcher.is_running:
            try:
                return await asyncio.wait_for(
                    self._model_cb.call(self.batcher.get_embedding, query_prefixed),
                    timeout=_INFERENCE_TIMEOUT,
                )
            except asyncio.TimeoutError as exc:
                logger.warning(
                    f"Inference timed out after {_INFERENCE_TIMEOUT}s for "
                    f"'{query_prefixed[:50]}'"
                )
                raise InferenceTimeoutError(
                    f"Inference timed out after {_INFERENCE_TIMEOUT}s", original=exc
                ) from exc
            except CircuitBreakerError:
                raise
            except Exception as exc:
                logger.error(f"Model inference failed: {exc}")
                raise InferenceError(
                    f"Model inference failed: {exc}", original=exc
                ) from exc
        else:
            # Fallback: synchronous inference
            logger.warning("Batcher unavailable — falling back to sync inference")
            return await self._fallback_inference(query_prefixed)

    async def _fallback_inference(self, query_prefixed: str) -> Any:
        """Synchronous inference fallback when batcher is unavailable."""
        if self.model is None:
            raise ModelLoadError("Model not loaded — cannot perform fallback inference")

        def _encode():
            return self.model.encode(
                query_prefixed, convert_to_tensor=True, normalize_embeddings=True
            )

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_encode), timeout=_INFERENCE_TIMEOUT
            )
        except asyncio.TimeoutError as exc:
            raise InferenceTimeoutError(
                f"Fallback inference timed out after {_INFERENCE_TIMEOUT}s",
                original=exc,
            ) from exc

    async def _faiss_search(
        self, query_embedding_np: np.ndarray, k: int = 1
    ) -> tuple:
        """FAISS search with circuit breaker protection."""
        if self.index is None:
            raise FaissIndexError("FAISS index is not initialized")

        def _do_search():
            return self.index.search(query_embedding_np, k)

        try:
            return await self._faiss_cb.call(_do_search)
        except CircuitBreakerError:
            raise
        except Exception as exc:
            logger.error(f"FAISS search failed: {exc}")
            raise FaissIndexError(
                f"FAISS search failed: {exc}", original=exc
            ) from exc

    def _to_numpy(self, embedding: Any) -> np.ndarray:
        """Convert a tensor or array to numpy safely."""
        if hasattr(embedding, "cpu"):
            return embedding.cpu().detach().numpy()
        return np.array(embedding)

    def _resolve_answer(
        self, best_id: str, detected_lang: str, best_match_info: dict
    ) -> str:
        """
        Resolve the best answer from the knowledge base, with fallback chain.

        Priority: detected_lang -> en -> mr -> hi -> hinglish -> answers_map
        """
        faq_entry = next(
            (item for item in self.knowledge_base if item["id"] == best_id), None
        )
        if faq_entry:
            # Try detected language first
            for variant in faq_entry.get("variants", []):
                if variant.get("lang") == detected_lang:
                    ans = variant.get("answer")
                    if ans:
                        return ans

            # Fallback chain
            for fallback_lang in ["en", "mr", "hi", "hinglish"]:
                for variant in faq_entry.get("variants", []):
                    if variant.get("lang") == fallback_lang:
                        ans = variant.get("answer")
                        if ans:
                            return ans

        # Last resort: the answer from the flat answers_map
        answer = best_match_info.get("answer", "")
        if answer:
            return answer

        logger.warning(
            f"No answer found for match_id={best_id}, lang={detected_lang}"
        )
        return "Sorry, no answer available for this question."

    def _get_unmatched_answer(self, lang: str) -> str:
        return self.fallback_messages.get(
            lang,
            self.fallback_messages.get(
                "en", "I'm sorry, no direct match found."
            ),
        )

    def get_top_matches(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Return the top-k matches for a query (sync, for debugging/testing).

        This bypasses the batcher and uses direct model inference.
        """
        if not self.knowledge_base or self.index is None or self.model is None:
            logger.warning(
                "get_top_matches called but knowledge base / index / model not ready"
            )
            return []

        if not query or not query.strip():
            return []

        try:
            query_embedding = self.model.encode(
                f"query: {query}",
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            query_embedding_np = (
                query_embedding.cpu().detach().numpy().astype("float32").reshape(1, -1)
            )
            D, I = self.index.search(query_embedding_np, top_k)

            matches: list[dict] = []
            for score, idx in zip(D[0], I[0]):
                idx = int(idx)
                if idx == -1:
                    continue
                if idx >= len(self.answers_map):
                    logger.warning(
                        f"FAISS returned out-of-bounds index {idx}"
                    )
                    continue
                match_info = self.answers_map[idx]
                matches.append({
                    "id": match_info["id"],
                    "lang": match_info["lang"],
                    "question": match_info["question"],
                    "answer": match_info["answer"],
                    "score": float(score),
                })
            return matches
        except Exception as exc:
            logger.error(f"Error in get_top_matches: {exc}")
            return []

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    async def shutdown(self):
        """Gracefully shut down the batcher."""
        if self.batcher is not None:
            await self.batcher.stop()
            logger.info("SimilarityBot batcher shut down.")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

async def run_tests():
    from rich.console import Console
    from rich.table import Table

    console = Console()
    print("\n" + "=" * 60)
    print("Testing Multilingual Semantic Bot")
    print("=" * 60 + "\n")

    bot = SimilarityBot()
    test_queries = [
        ("What is FYJC?", "English"),
        ("FYJC admission kaise hota hai?", "Hinglish"),
        ("नोंदणी कशी करावी?", "Marathi"),
        ("पंजीकरण कैसे करें?", "Hindi"),
        ("Online registration compulsory hai kya?", "Hinglish"),
        ("Documents kya chahiye?", "Hinglish"),
        ("कौन से दस्तावेज चाहिए?", "Hindi"),
    ]

    for query, lang_name in test_queries:
        print(f"\n[bold blue]Query ({lang_name}):[/bold blue] {query}")
        result = await bot.answer(query)

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        answer = result.get("answer", "N/A")
        table.add_row("Detected Language", result.get("detected_lang", "N/A"))
        table.add_row("Match ID", result.get("match_id", "N/A"))
        table.add_row("Confidence Score", f"{result.get('score', 0):.4f}")
        table.add_row(
            "Answer",
            answer[:200] + "..." if len(answer) > 200 else answer,
        )
        console.print(table)

        print("\n[bold]Top 3 Matches:[/bold]")
        for i, match in enumerate(bot.get_top_matches(query, top_k=3), 1):
            print(
                f"  {i}. [{match['lang']}] {match['question'][:60]}... "
                f"(score: {match['score']:.4f})"
            )
        print("-" * 60)

    await bot.shutdown()


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_tests())
