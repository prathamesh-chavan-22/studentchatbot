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
        """Load all entries from knowledge_base.txt (one entry per line)."""
        with open(path, "r", encoding="utf-8") as f:
            return [
                line.replace(" [BREAK] ", "\n").strip()
                for line in f
                if line.strip()
            ]

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
            assert len(self._questions) == self._matrix.shape[0], "Questions count mismatch with saved index"
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

    def _fallback_answer(self, query: str, sources: List[RetrievalResult]) -> str:
        top = "\n".join([f"- {s.question}" for s in sources[:3]]) if sources else "- माहिती उपलब्ध नाही"

        if self._looks_marathi(query):
            return (
                "**मराठी**\n"
                "आपल्या प्रश्नासाठी संबंधित FAQ खालीलप्रमाणे आहेत:\n"
                f"{top}\n\n"
                "**English**\n"
                "For your query, these related FAQs were found:\n"
                f"{top}\n\n"
                "अधिक मदतीसाठी हेल्पलाईन: 8530955564"
            )

        return (
            "**English**\n"
            "For your query, these related FAQs were found:\n"
            f"{top}\n\n"
            "**मराठी**\n"
            "आपल्या प्रश्नासाठी संबंधित FAQ खालीलप्रमाणे आहेत:\n"
            f"{top}\n\n"
            "For more help, call helpline: 8530955564"
        )

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
