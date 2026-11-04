"""Tests for the colour tokens and stylesheet (theme.py).

These catch the mistakes that are easy to make when editing colours: a typo in a
hex code, an accent missing a colour, or a stylesheet placeholder with no value.
"""
import re

import pytest

import theme

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
MODES = ["light", "dark"]
ACCENT_NAMES = list(theme.ACCENTS)


def test_light_and_dark_bases_define_the_same_colours():
    assert theme.BASE_LIGHT.keys() == theme.BASE_DARK.keys()


@pytest.mark.parametrize("accent", ACCENT_NAMES)
def test_each_accent_has_matching_light_and_dark_colours(accent):
    pair = theme.ACCENTS[accent]
    assert set(pair) == set(MODES)
    assert pair["light"].keys() == pair["dark"].keys()


def test_all_accents_define_the_same_colours():
    first = theme.ACCENTS[ACCENT_NAMES[0]]["light"].keys()
    for name in ACCENT_NAMES:
        assert theme.ACCENTS[name]["light"].keys() == first, name


def test_every_colour_is_a_valid_hex_code():
    palettes = [theme.BASE_LIGHT, theme.BASE_DARK]
    palettes += [theme.ACCENTS[a][m] for a in ACCENT_NAMES for m in MODES]
    for palette in palettes:
        for name, value in palette.items():
            assert HEX.match(value), f"{name} = {value!r}"


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("accent", ACCENT_NAMES)
def test_stylesheet_builds_for_every_accent_and_mode(monkeypatch, accent, mode):
    monkeypatch.setattr(theme, "ACCENT", accent)
    monkeypatch.setattr(theme, "MODE", mode)
    qss = theme.stylesheet()  # a missing colour would raise KeyError here
    assert not re.search(r"\{[a-z_]+\}", qss)  # no placeholder left unfilled
    assert theme.ACCENTS[accent][mode]["panel"] in qss


@pytest.mark.parametrize("mode", MODES)
def test_forced_mode_is_respected(monkeypatch, mode):
    monkeypatch.setattr(theme, "MODE", mode)
    assert theme.is_dark() is (mode == "dark")
    assert theme.tokens()["bg"] == (theme.BASE_DARK if mode == "dark" else theme.BASE_LIGHT)["bg"]


def test_unknown_accent_falls_back_to_quebec_blue(monkeypatch):
    monkeypatch.setattr(theme, "ACCENT", "does-not-exist")
    monkeypatch.setattr(theme, "MODE", "light")
    assert theme.tokens()["accent"] == theme.ACCENTS["quebec"]["light"]["accent"]


def test_chosen_accent_is_a_real_accent():
    assert theme.ACCENT in theme.ACCENTS
