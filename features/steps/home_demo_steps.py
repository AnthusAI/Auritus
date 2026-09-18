"""Behave steps for aurit.us home demo and marketing button styling."""

from __future__ import annotations

from pathlib import Path
import re

from behave import given, then

SITE_DIR = Path(__file__).resolve().parents[2] / "site"
GLOBALS_CSS_PATH = SITE_DIR / "app" / "globals.css"


@given("the marketing site styles")
def step_marketing_styles(context) -> None:
    """Load the site global CSS source for style assertions."""
    context.css_source = GLOBALS_CSS_PATH.read_text(encoding="utf-8")


@then("the header call to action and hero call to action share a square border radius")
def step_cta_square_border_radius(context) -> None:
    """Assert that .nav-cta and .button share a crisp, square border radius."""
    nav_cta_match = re.search(
        r"\.nav-cta\s*\{[^}]*border-radius:\s*([^;]+);", context.css_source
    )
    button_match = re.search(
        r"\.button\s*\{[^}]*border-radius:\s*([^;]+);", context.css_source
    )
    assert nav_cta_match is not None, "Could not find border-radius in .nav-cta"
    assert button_match is not None, "Could not find border-radius in .button"

    nav_cta_radius = nav_cta_match.group(1).strip()
    button_radius = button_match.group(1).strip()

    assert (
        nav_cta_radius == button_radius
    ), f".nav-cta radius ({nav_cta_radius}) != .button radius ({button_radius})"
    assert "999" not in nav_cta_radius, f".nav-cta is still a pill: {nav_cta_radius}"
    assert "50%" not in nav_cta_radius, f".nav-cta is still rounded: {nav_cta_radius}"


@then("the marketing hero does not enforce full viewport centering")
def step_hero_not_full_viewport(context) -> None:
    """Assert that .marketing-hero does not enforce full 100vh centering."""
    hero_match = re.search(r"\.marketing-hero\s*\{([^}]+)\}", context.css_source)
    assert hero_match is not None, "Could not find .marketing-hero rules"
    hero_rules = hero_match.group(1)
    assert "100vh" not in hero_rules, ".marketing-hero still enforces 100vh"
    assert (
        "align-items: center" not in hero_rules
    ), ".marketing-hero still centers items"


@then("the marketing hero vertical padding is compact")
def step_hero_compact_padding(context) -> None:
    """Assert that .marketing-hero top padding is at most 2rem."""
    hero_match = re.search(r"\.marketing-hero\s*\{([^}]+)\}", context.css_source)
    assert hero_match is not None, "Could not find .marketing-hero rules"
    hero_rules = hero_match.group(1)
    padding_match = re.search(r"padding-block:\s*([^;]+);", hero_rules)
    assert padding_match is not None, "Could not find padding-block in .marketing-hero"
    padding_val = padding_match.group(1).strip()
    top_padding = padding_val.split()[0]
    assert "4rem" not in top_padding, f"Top padding is still loose: {top_padding}"
