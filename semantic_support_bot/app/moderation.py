"""
Content moderation — keyword-based filter for inappropriate language.

Error handling improvements:
- Input validation and type safety
- Safe regex compilation with error handling
- Graceful handling of encoding issues
- Structured logging for violations
"""

from __future__ import annotations

import re
from typing import Tuple
from loguru import logger

from app.exceptions import ContentModerationError


class ContentModerator:
    """
    Checks input text against a list of blocked words per language.

    This is a best-effort, keyword-based filter. In a production system
    this should be supplemented with a proper ML-based moderation API.
    """

    def __init__(self):
        # A baseline list of inappropriate words for an educational context.
        # Note: This is an abbreviated illustrative list for demonstration.
        # In a real production system, this would be more extensive or use
        # specialized libraries.
        self.bad_words: dict[str, list[str]] = {
            "en": [
                "fuck", "shit", "bitch", "asshole", "piss", "bastard",
                "dick", "cunt", "pussy",
            ],
            "hi": ["गाली", "बकवास", "हरामी", "कुत्ता", "साला", "कमीना"],
            "mr": ["गाली", "मूर्ख", "बदमाश", "नालायक", "हरामखोर"],
        }

        # Compile patterns for efficiency — do this once at init time
        self.patterns: dict[str, re.Pattern] = {}
        for lang, words in self.bad_words.items():
            try:
                if lang == "en":
                    regex_str = "|".join(
                        [rf"\b{re.escape(word)}\b" for word in words]
                    )
                else:
                    # For Hindi/Marathi, match the words directly without
                    # \b boundaries (word boundaries don't work reliably
                    # with Devanagari script)
                    regex_str = "|".join([re.escape(word) for word in words])

                self.patterns[lang] = re.compile(regex_str, re.IGNORECASE)
            except re.error as exc:
                # This should never happen with the static word lists above,
                # but handle it defensively.
                logger.critical(
                    f"Failed to compile moderation pattern for lang={lang}: {exc}"
                )

    def is_appropriate(self, text: str) -> Tuple[bool, str]:
        """
        Check if the text contains any blocked words.

        Parameters
        ----------
        text : str
            The user input to check.

        Returns
        -------
        tuple[bool, str]
            (is_appropriate, language_of_violation)

        Raises
        ------
        ContentModerationError
            If an unexpected error occurs during moderation.
        """
        if not text or not text.strip():
            return True, ""

        # Guard against non-string input (defensive — Pydantic should catch this)
        if not isinstance(text, str):
            logger.warning(
                f"is_appropriate received non-string input: {type(text).__name__}"
            )
            return True, ""

        try:
            for lang, pattern in self.patterns.items():
                try:
                    if pattern.search(text):
                        logger.info(
                            f"Content moderation: violation detected in '{lang}' "
                            f"for text (length={len(text)})"
                        )
                        return False, lang
                except re.error as exc:
                    # Should not happen with pre-compiled patterns, but guard anyway
                    logger.warning(
                        f"Regex error during moderation (lang={lang}): {exc}"
                    )
                    continue

            return True, ""
        except Exception as exc:
            logger.error(
                f"Unexpected error during content moderation: {exc}",
                exc_info=True,
            )
            raise ContentModerationError(
                "Failed to perform content moderation", original=exc
            ) from exc

    def get_refusal_message(self, lang: str) -> str:
        """
        Return a language-appropriate refusal message.

        Falls back to English for unknown languages.
        """
        messages: dict[str, str] = {
            "en": "I'm sorry, but I cannot process queries containing inappropriate language. Please maintain a respectful tone.",
            "mr": "क्षमस्व, मी अयोग्य भाषा असलेला प्रश्न स्वीकारू शकत नाही. कृपया सभ्य भाषेत प्रश्न विचारा.",
            "hi": "क्षमा करें, मैं अभद्र भाषा वाले प्रश्नों का उत्तर नहीं दे सकता। कृपया गरिमा बनाए रखें।",
            "hinglish": "Maaf kijiye, par main inappropriate language wale sawal handle nahi kar sakta. Please respect maintain karein.",
        }
        return messages.get(lang, messages["en"])
