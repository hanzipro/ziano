"""The demo's family cards switch variants in pure CSS, which means a hand-written
map in `hero.css` pairs each radio's `value` with a `dl[data-font-name]`. CSS cannot
compare one element's attribute against another's, so that map cannot be derived —
and when a font is renamed and the map isn't, nothing breaks loudly: the selector
just stops matching and the card renders its chips above an empty body.

That is not hypothetical. 0.2.0's rename (`genki-min` → `genki-serif`,
`genki-gothic` → `genki-sans`, `*-tc` → `*-yue`) left the map untouched, so 源起's
four variants and 尚古's two 月 variants showed blank cards until 2026-08-08.

These tests keep the three lists in agreement.
"""

import re
from pathlib import Path

import pytest

DEMO = Path(__file__).resolve().parent.parent / "demo"
INDEX = DEMO / "index.html"
HERO = DEMO / "src" / "css" / "hero.css"


@pytest.fixture(scope="module")
def html() -> str:
    return INDEX.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def hero() -> str:
    return HERO.read_text(encoding="utf-8")


def radio_values(html: str) -> set[str]:
    """Every variant radio's value — `name="fam-*"` is what marks one."""
    return set(re.findall(r'name="fam-[a-z-]+"\s+value="([a-z0-9-]+)"', html))


def card_names(html: str) -> set[str]:
    return set(re.findall(r'<dl\s+data-font-name="([a-z0-9-]+)"', html))


def mapped_pairs(hero: str) -> set[tuple[str, str]]:
    """The (radio value, card name) pairs the CSS map actually spells out."""
    return set(
        re.findall(
            r"input\[value='([a-z0-9-]+)'\]:checked\)\s*dl\[data-font-name='([a-z0-9-]+)'\]",
            hero,
        )
    )


def test_every_variant_radio_has_a_card(html):
    missing = radio_values(html) - card_names(html)
    assert not missing, f"radio values with no matching <dl data-font-name>: {sorted(missing)}"


def test_every_variant_radio_is_in_the_css_map(html, hero):
    """The failure this guards: an unmapped value renders a card with no body."""
    mapped = {value for value, _ in mapped_pairs(hero)}
    missing = radio_values(html) - mapped
    assert not missing, (
        "these variants would render a blank card — add them to hero.css § "
        f"the active-variant map: {sorted(missing)}"
    )


def test_the_css_map_pairs_each_value_with_its_own_card(hero):
    crossed = {(v, n) for v, n in mapped_pairs(hero) if v != n}
    assert not crossed, f"map entries pointing at another font's card: {sorted(crossed)}"


def test_the_css_map_has_no_leftovers(html, hero):
    """A stale entry is dead weight and, worse, reads as proof the pair still exists."""
    stale = {value for value, _ in mapped_pairs(hero)} - card_names(html)
    assert not stale, f"map entries for fonts the page no longer has: {sorted(stale)}"
