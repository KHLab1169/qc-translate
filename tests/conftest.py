"""Shared test helpers.

The fake DeepL client below stands in for the real one, so the tests never
touch the network, never need a real key, and never use any DeepL quota.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# Let the tests import app.py, translator.py, etc. from the project folder.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import translator  # noqa: E402


class FakeDeepLClient:
    """Records every call and returns a predictable "translation"."""

    def __init__(self, auth_key):
        self.auth_key = auth_key
        self.calls = []        # one dict per translate_text() call
        self.error = None      # set to an exception to make the next calls fail
        self.usage_count = 1_234
        self.usage_limit = 500_000
        self.usage_valid = True

    def translate_text(self, text, **options):
        if self.error:
            raise self.error
        self.calls.append({"text": text, **options})
        # Tag the output with the formality so tu/vous results are distinguishable.
        return SimpleNamespace(text=f"FR[{options['formality']}]: {text}")

    def get_usage(self):
        if self.error:
            raise self.error
        character = SimpleNamespace(
            valid=self.usage_valid, count=self.usage_count, limit=self.usage_limit
        )
        return SimpleNamespace(character=character)


@pytest.fixture
def fake_client(monkeypatch):
    """Swap deepl.Translator for the fake; returns the fake the translator will use."""
    created = []

    def factory(auth_key):
        client = FakeDeepLClient(auth_key)
        created.append(client)
        return client

    monkeypatch.setattr(translator.deepl, "Translator", factory)
    return created  # created[0] is the client after a QcTranslator is built


@pytest.fixture
def qc(fake_client):
    """A QcTranslator wired to the fake client."""
    t = translator.QcTranslator("test-key:fx")
    t.fake = fake_client[0]  # handy handle for assertions
    return t
