"""Data processor module."""

import logging
import re

STRIP_CHARS = " \t\n\r"

_log = logging.getLogger(__name__)
_WORD_RE = re.compile(r"\w+")


class DataProcessor:
    """Processes text data."""

    def __init__(self, strip: bool = True) -> None:
        self.strip = strip

    def validate(self, text: str) -> bool:
        """Return True if text contains at least one word character."""
        return bool(text and _WORD_RE.search(text))

    def process(self, text: str) -> str:
        """Process and normalize a text string."""
        _log.debug("process() input: %r", text)
        if not self.validate(text):
            raise ValueError(f"Invalid input: {text!r}")
        if self.strip:
            text = text.strip(STRIP_CHARS)
        result = text.lower()
        _log.debug("process() output: %r", result)
        return result
