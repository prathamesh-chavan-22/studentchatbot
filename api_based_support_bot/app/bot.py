from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Tuple

import faiss
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer


@dataclass
class RetrievalResult:
    question: str
    score: float


class FYJCSupportBot:
    """FAISS + Groq support bot for FYJC FAQs (Marathi/English)."""

    def __init__(self, faq_file: str = None) -> None:
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # base_dir is always the project root (parent of this file's directory)
        self.base_dir = Path(__file__).resolve().parent.parent
        self.index_path = self.base_dir / "faiss_index.bin"
        self.matrix_path = self.base_dir / "embed_matrix.npy"
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.chat_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.search_k = int(os.getenv("SEARCH_K", "5"))
        self.fallback_min_score = float(os.getenv("FALLBACK_MIN_SCORE", "0.55"))

        # Exclusively use knowledge_base.txt — no faq_file fallback
        self.knowledge_file = self.base_dir / "knowledge_base.txt"
        if not self.knowledge_file.exists():
            raise ValueError(f"knowledge_base.txt not found at {self.knowledge_file}")

        self._questions = self._load_kb(self.knowledge_file)
        self.logger.info(f"Loaded {len(self._questions)} entries from knowledge_base.txt")

        self._embedder_instance = SentenceTransformer(self.embedding_model_name)
        self._index, self._matrix = self._load_or_build_index()

        api_key = os.getenv("GROQ_API_KEY", "").strip()
        self._groq_client = Groq(api_key=api_key) if api_key else None

    def _load_kb(self, path: Path) -> List[str]:
        """Load FAQ entries from knowledge_base.txt as Q/A blocks.

        This intentionally ignores noisy scraped metadata lines (e.g., Source: ...)
        so retrieval quality remains focused on FYJC FAQ content.
        """
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.replace(" [BREAK] ", "\n").strip() for line in f if line.strip()]

        entries: List[str] = []
        current_q: str | None = None
        current_a_parts: List[str] = []

        for line in lines:
            if line.startswith("Source:"):
                continue

            if line.startswith("Q:"):
                if current_q:
                    answer = "\n".join(current_a_parts).strip()
                    entries.append(f"{current_q}\n{answer}" if answer else current_q)
                current_q = line
                current_a_parts = []
                continue

            if line.startswith("A:"):
                current_a_parts.append(line)
                continue

            # Continuation lines: attach to the active answer, else ignore.
            if current_q:
                current_a_parts.append(line)

        if current_q:
            answer = "\n".join(current_a_parts).strip()
            entries.append(f"{current_q}\n{answer}" if answer else current_q)

        # Fallback to legacy line-wise entries only if parsing unexpectedly fails.
        if entries:
            return entries
        return lines

    def _embed(self, texts: List[str]) -> np.ndarray:
        model_name = self.embedding_model_name.lower()
        if "e5" in model_name:
            prefixed_texts = [f"query: {text}" for text in texts]
        else:
            prefixed_texts = texts
        
        vectors = self._embedder.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True)
        return vectors.astype("float32")

    def _load_or_build_index(self) -> Tuple[faiss.IndexFlatIP, np.ndarray]:
        """Load persistent index or build and save new one."""
        if self.index_path.exists() and self.matrix_path.exists():
            print(f"Loading persistent index from {self.index_path}")
            self._index = faiss.read_index(str(self.index_path))
            self._matrix = np.load(self.matrix_path)
            if len(self._questions) != self._matrix.shape[0]:
                print("Knowledge base size changed; rebuilding persistent index...")
                self._index, self._matrix = self._build_index(self._questions)
                faiss.write_index(self._index, str(self.index_path))
                np.save(self.matrix_path, self._matrix)
            return self._index, self._matrix
        
        print("Building new index...")
        self._index, self._matrix = self._build_index(self._questions)
        faiss.write_index(self._index, str(self.index_path))
        np.save(self.matrix_path, self._matrix)
        print(f"Saved index to {self.index_path}")
        return self._index, self._matrix

    def _build_index(self, questions: List[str]) -> Tuple[faiss.IndexFlatIP, np.ndarray]:
        matrix = self._embed(questions)
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        return index, matrix

    @property
    def _embedder(self):
        return self._embedder_instance

    def search(self, user_query: str, k: int = None) -> List[RetrievalResult]:
        k = k or self.search_k
        q = self._embed([user_query])
        scores, indices = self._index.search(q, k)
        results: List[RetrievalResult] = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append(RetrievalResult(question=self._questions[idx], score=float(score)))
        return results

    @staticmethod
    def _looks_marathi(text: str) -> bool:
        return bool(re.search(r"[\u0900-\u097F]", text))

    @staticmethod
    def _normalize_for_match(text: str) -> str:
        return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()

    def _is_greeting(self, query: str) -> bool:
        normalized = self._normalize_for_match(query)
        greetings = {
            "hi", "hello", "hey", "good morning", "good afternoon", "good evening",
            "namaste", "namaskar", "hii", "helo", "hy"
        }
        return normalized in greetings

    def _greeting_reply(self, query: str) -> str:
        if self._looks_marathi(query) or "namaste" in query.lower() or "namaskar" in query.lower():
            return "नमस्कार! FYJC महाराष्ट्र प्रवेशाबाबत मी तुमची कशी मदत करू शकतो?"
        if "good morning" in query.lower():
            return "Good morning! How can I help you with FYJC Maharashtra admissions?"
        if "good afternoon" in query.lower():
            return "Good afternoon! How can I help you with FYJC Maharashtra admissions?"
        if "good evening" in query.lower():
            return "Good evening! How can I help you with FYJC Maharashtra admissions?"
        return "Hello! How can I help you with FYJC Maharashtra admissions?"

    @staticmethod
    def _refusal_reply() -> str:
        return (
            "I can only assist with FYJC Maharashtra admission queries based on the official FAQs. "
            "For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564."
        )

    @staticmethod
    def _extract_answer_text(entry: str) -> str:
        match = re.search(r"A:\s*(.*)", entry, flags=re.DOTALL)
        if match:
            return match.group(1).strip()
        return entry.strip()

    def _fallback_answer(self, query: str, sources: List[RetrievalResult]) -> str:
        if self._is_greeting(query):
            return self._greeting_reply(query)

        normalized_query = self._normalize_for_match(query)
        if len(normalized_query) < 4:
            return self._refusal_reply()

        if not sources:
            return self._refusal_reply()

        best = sources[0]
        if best.score < self.fallback_min_score:
            return self._refusal_reply()

        answer_text = self._extract_answer_text(best.question)
        if not answer_text:
            return self._refusal_reply()

        # If user asked in non-Marathi but retrieval answer is Marathi, avoid returning
        # an unrelated cross-language snippet from vector similarity noise.
        if not self._looks_marathi(query) and self._looks_marathi(answer_text):
            return self._refusal_reply()

        return answer_text

    def answer(self, query: str, history: List[Dict[str, str]] = None) -> dict:
        results = self.search(query)
        context = "\n".join([f"{i+1}. {r.question}" for i, r in enumerate(results)])

        if not self._groq_client:
            return {
                "answer": self._fallback_answer(query, results),
                "sources": [r.question for r in results],
                "used_groq": False,
            }

        client = self._groq_client
        system_prompt = (
            "You are the official FYJC Maharashtra Admissions Support Bot. "
            "Your MISSION is to provide accurate, concise information about FYJC online admissions in Maharashtra. "
            "\n\nGUARDRAILS & INSTRUCTIONS:\n"
            "1. REASON FIRST: The provided context might not always be the absolute truth or perfectly align with the user's question. First, write your reasoning inside <think>...</think> tags evaluating if the context actually answers the specific query to avoid hallucination.\n"
            "2. ONLY answer questions related to FYJC Maharashtra admissions using the provided FAQ context. DO NOT hallucinate or make up details not present in the context.\n"
            "3. If the user's input is just a greeting (e.g., 'hi', 'hello', 'namaste'), respond with a friendly greeting and ask how you can help them with FYJC admissions. Do NOT include support contact info for mere greetings.\n"
            "4. If the user's question is NOT about FYJC admissions, or if a confident answer cannot be found in the context after reasoning, you MUST politely refuse to answer. "
            "ONLY in this refusal case, provide the support contact info by using exactly this message: 'I can only assist with FYJC Maharashtra admission queries based on the official FAQs. For more details, please contact support@mahafyjcadmissions.in or call the helpline at 8530955564.'\n"
            "5. DO NOT use any internal knowledge or information outside the provided FAQ context.\n"
            "6. RESPOND ONLY in ONE language: the language of the user's query (Marathi if the query is in Marathi, English if in English). Do NOT provide bilingual responses.\n"
            "7. Use **bold**, *italic*, and bullet points for readability. DO NOT append the helpline or email to regular answers, only use them for the refusal message."
        )

        # Prepare messages including history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add history if provided (limit to last 10)
        if history:
            for msg in history[-10:]:
                role = "assistant" if msg["role"] == "bot" else "user"
                messages.append({"role": role, "content": msg["content"]})

        user_prompt = (
            f"Provided FAQ Context:\n{context}\n\n"
            f"User Query: {query}\n\n"
            f"Assistant, please write your reasoning inside <think> tags first. Then, provide a helpful, concise response strictly following the guardrails. Do NOT provide answers in multiple languages; respond ONLY in the single language of the user's query."
        )
        messages.append({"role": "user", "content": user_prompt})

        try:
            completion = client.chat.completions.create(
                model=self.chat_model,
                temperature=0.2,
                messages=messages,
                max_tokens=131072,
            )

            # Extract usage and calculate cost
            usage = completion.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # Pricing: $0.05/1M input, $0.08/1M output
            input_cost = (prompt_tokens / 1_000_000) * 0.05
            output_cost = (completion_tokens / 1_000_000) * 0.08
            total_cost = input_cost + output_cost

            # Log usage and percentage of TPM limit (250K)
            tpm_limit = 250000
            tpm_percent = (total_tokens / tpm_limit) * 100
            
            self.logger.info(
                f"Groq Usage: {prompt_tokens} prompt, {completion_tokens} completion, "
                f"{total_tokens} total ({tpm_percent:.1f}% of TPM limit). Cost: ${total_cost:.6f}"
            )

            content = completion.choices[0].message.content if completion.choices else "No response"
            # Robustly remove any thought blocks (closed or unclosed)
            content = re.sub(r'<(?:thought|think)>.*?</(?:thought|think)>', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = re.sub(r'<(?:thought|think)>.*$', '', content, flags=re.DOTALL | re.IGNORECASE)
            content = content.strip()
            
            return {
                "answer": content,
                "sources": [r.question for r in results],
                "used_groq": True,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "tpm_limit": tpm_limit,
                    "tpm_utilized_percent": round(tpm_percent, 2),
                    "cost_usd": round(total_cost, 6)
                }
            }
        except Exception as err:
            self.logger.exception(f"Groq API error: {err}")
            return {
                "answer": self._fallback_answer(query, results),
                "sources": [r.question for r in results],
                "used_groq": False,
            }
