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
