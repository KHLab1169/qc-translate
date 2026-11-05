"""Tests for the translation core (translator.py)."""
import deepl
import pytest

from translator import FORMALITY, QcTranslator, friendly_error


# --- Setup --------------------------------------------------------------------

def test_missing_key_is_rejected(fake_client):
    with pytest.raises(ValueError):
        QcTranslator("")


def test_key_is_passed_to_deepl(qc):
    assert qc.fake.auth_key == "test-key:fx"


# --- What gets sent to DeepL --------------------------------------------------

@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_blank_input_returns_empty_without_calling_deepl(qc, text):
    assert qc.translate(text) == ""
    assert qc.fake.calls == []  # no request, no quota used


def test_request_uses_quebec_french_settings(qc):
    qc.translate("Hello")
    call = qc.fake.calls[0]
    assert call["source_lang"] == "EN"       # fixed source language
    assert call["target_lang"] == "FR-CA"    # Canadian French
    assert call["preserve_formatting"] is True


def test_surrounding_whitespace_is_stripped(qc):
    qc.translate("   See you this weekend  \n")
    assert qc.fake.calls[0]["text"] == "See you this weekend"


@pytest.mark.parametrize("register", ["tu", "vous"])
def test_register_sets_formality(qc, register):
    qc.translate("How are you?", register)
    assert qc.fake.calls[0]["formality"] == FORMALITY[register]


def test_default_register_is_tu(qc):
    qc.translate("Thanks")
    assert qc.fake.calls[0]["formality"] == FORMALITY["tu"]


def test_returns_deepl_text(qc):
    assert qc.translate("Email") == "FR[prefer_less]: Email"


# --- Cache ---------------------------------------------------------------------

def test_repeat_text_is_served_from_cache(qc):
    first = qc.translate("Good morning")
    second = qc.translate("Good morning")
    assert first == second
    assert len(qc.fake.calls) == 1  # the second one cost no quota


def test_cache_ignores_surrounding_whitespace(qc):
    qc.translate("Good morning")
    qc.translate("  Good morning  ")
    assert len(qc.fake.calls) == 1


def test_tu_and_vous_are_cached_separately(qc):
    tu = qc.translate("Can you help?", "tu")
    vous = qc.translate("Can you help?", "vous")
    assert tu != vous
    assert len(qc.fake.calls) == 2


def test_cache_drops_least_recently_used(fake_client):
    t = QcTranslator("key", cache_size=2)
    fake = fake_client[0]
    t.translate("one")
    t.translate("two")
    t.translate("one")    # "one" is now the most recently used
    t.translate("three")  # cache is full: "two" gets dropped
    assert len(fake.calls) == 3

    t.translate("one")    # still cached
    assert len(fake.calls) == 3
    t.translate("two")    # was dropped, so DeepL is called again
    assert len(fake.calls) == 4


def test_failed_request_is_not_cached(qc):
    qc.fake.error = deepl.ConnectionException("offline")
    with pytest.raises(deepl.ConnectionException):
        qc.translate("Hello")

    qc.fake.error = None  # back online
    assert qc.translate("Hello") == "FR[prefer_less]: Hello"
    assert len(qc.fake.calls) == 1


# --- Quota ---------------------------------------------------------------------

def test_usage_returns_count_and_limit(qc):
    assert qc.usage() == (1_234, 500_000)


def test_usage_is_none_when_deepl_has_no_figures(qc):
    qc.fake.usage_valid = False
    assert qc.usage() is None


def test_usage_raises_on_bad_key(qc):
    # app.py relies on this to check a key on first run.
    qc.fake.error = deepl.AuthorizationException("bad key")
    with pytest.raises(deepl.AuthorizationException):
        qc.usage()


# --- Error messages ------------------------------------------------------------

@pytest.mark.parametrize(
    "error, expected",
    [
        (deepl.AuthorizationException("x"), "DeepL rejected the key"),
        (deepl.QuotaExceededException("x"), "quota is used up"),
        (deepl.TooManyRequestsException("x"), "DeepL is busy"),
        (deepl.ConnectionException("x"), "Can't reach DeepL"),
    ],
)
def test_friendly_error_messages(error, expected):
    assert expected in friendly_error(error)


def test_unknown_error_still_gets_a_message():
    assert friendly_error(RuntimeError("boom")) == "Unexpected error: boom"
