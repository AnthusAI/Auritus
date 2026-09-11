"""Behave steps for player display metadata scenarios."""

from __future__ import annotations

from behave import given, then, when


class _Script:
    def __init__(self, attrs: dict[str, str]) -> None:
        self._attrs = attrs

    def getAttribute(self, name: str) -> str | None:
        return self._attrs.get(name)


@given('an embed script with data-auritus-name "{name}"')
def step_script_name(context, name: str) -> None:
    context.script_attrs = {"data-auritus-name": name}


@given('data-auritus-byline "{byline}"')
def step_script_byline(context, byline: str) -> None:
    context.script_attrs["data-auritus-byline"] = byline


@given("an embed script without name or byline attributes")
def step_script_empty(context) -> None:
    context.script_attrs = {}


@given('document title "{title}"')
def step_doc_title(context, title: str) -> None:
    context.document_title = title


@given('page hostname "{hostname}"')
def step_hostname(context, hostname: str) -> None:
    context.hostname = hostname


@when("player metadata is read from the script")
def step_read_metadata(context) -> None:
    script = _Script(context.script_attrs)

    name = (script.getAttribute("data-auritus-name") or "").strip()
    if not name:
        name = (context.document_title or "").strip()

    byline = (script.getAttribute("data-auritus-byline") or "").strip()
    if not byline:
        byline = context.hostname or ""

    context.player_name = name
    context.player_byline = byline


@then('the player title is "{title}"')
def step_player_title(context, title: str) -> None:
    assert context.player_name == title


@then('the player byline is "{byline}"')
def step_player_byline(context, byline: str) -> None:
    assert context.player_byline == byline
