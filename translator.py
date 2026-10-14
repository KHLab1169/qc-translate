"""Translation core: English -> Quebec French (fr-CA) via DeepL.

This module knows nothing about the UI. It takes text in and gives text back,
so we can test it on its own before building the window around it.
"""
from collections import OrderedDict

import deepl
import deepl.http_client

# The library retries 5 times with 10 s timeouts by default, so going offline
# would freeze the status on "Translating…" for about a minute. Fail fast instead.
deepl.http_client.max_network_retries = 1
deepl.http_client.min_connection_timeout = 5.0

# "prefer_" variants ask DeepL for tu/vous but never error if it can't comply.
FORMALITY = {"tu": "prefer_less", "vous": "prefer_more"}


class QcTranslator:
    def __init__(self, auth_key: str, cache_size: int = 200):
        if not auth_key:
            raise ValueError("A DeepL key is required.")
        # The library picks the free or paid endpoint from the key (":fx" = free).
        self._client = deepl.Translator(auth_key)
        # Small LRU cache: text we've already translated costs no quota and no wait.
        # Keyed on (text, register): the same English gives different French
        # in tu vs vous, so both must be part of the key.
        self._cache: OrderedDict[tuple[str, str], str] = OrderedDict()
        self._cache_size = cache_size

    def translate(self, text: str, register: str = "tu") -> str:
        stripped = text.strip()
        if not stripped:
            return ""

        key = (stripped, register)
        if key in self._cache:
            self._cache.move_to_end(key)  # mark as recently used
            return self._cache[key]

        result = self._client.translate_text(
            stripped,
            source_lang="EN",          # fixed source: short fragments can fool auto-detect
            target_lang="FR-CA",       # Canadian French
            formality=FORMALITY[register],
            preserve_formatting=True,  # keep your capitalization and punctuation
        )
        self._cache[key] = result.text
        if len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)  # drop the least recently used entry
        return result.text

    def usage(self) -> tuple[int, int] | None:
        """Characters used and the monthly limit, or None if unavailable.

        Also a cheap way to test a key: a bad key raises AuthorizationException.
        """
        chars = self._client.get_usage().character
        if not chars.valid:
            return None
        return chars.count, chars.limit


def friendly_error(e: Exception) -> str:
    """Turn a library exception into a message a person can act on."""
    if isinstance(e, deepl.AuthorizationException):
        return "DeepL rejected the key. Check qc-translate.ini."
    if isinstance(e, deepl.QuotaExceededException):
        return "This month's DeepL quota is used up."
    if isinstance(e, deepl.TooManyRequestsException):
        return "DeepL is busy. Pause a moment and keep typing."
    if isinstance(e, deepl.ConnectionException):
        return "Can't reach DeepL. Check your internet connection."
    return f"Unexpected error: {e}"
