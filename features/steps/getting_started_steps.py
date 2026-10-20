"""Step definitions for the interactive getting started onboarding guide specs."""

from __future__ import annotations

import re
from pathlib import Path

from behave import given, then, when

WIZARD_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "site"
    / "components"
    / "GettingStartedWizard.tsx"
)


def read_model_cards_from_wizard_source() -> list[dict]:
    """Parse the model option objects out of the real wizard component source.

    :returns: One dictionary per model card with its string fields.
    """
    source = WIZARD_SOURCE.read_text(encoding="utf-8")
    block = source.split("const MODEL_OPTIONS: ModelOption[] = [", 1)[1]
    block = block.split("\n];", 1)[0]
    cards = []
    for entry in re.split(r"\n  \},?\n", block):
        fields = dict(re.findall(r"^\s{4}(\w+): '([^']*)',$", entry, re.MULTILINE))
        if fields:
            cards.append(fields)
    return cards


@given("a visitor on the getting started documentation page")
def step_visitor_on_guide(context) -> None:
    context.page = "/docs/getting-started"
    context.auth_options = [
        {
            "id": "cognito",
            "name": "Native Cognito",
            "doc_link": "/docs/security#cognito",
        },
        {
            "id": "google",
            "name": "Google Workspace",
            "doc_link": "/docs/security#google",
        },
        {
            "id": "identity-center",
            "name": "AWS IAM Identity Center",
            "doc_link": "/docs/security#identity-center",
        },
    ]
    context.selected_auth = None
    context.models = read_model_cards_from_wizard_source()
    context.selected_model = context.models[0]


@when("the visitor views the authentication decision section")
def step_view_auth_section(context) -> None:
    context.displayed_auth_options = context.auth_options


@then(
    'three options are displayed side-by-side: "Native Cognito", "Google Workspace", and "AWS IAM Identity Center"'
)
def step_verify_three_options(context) -> None:
    names = [opt["name"] for opt in context.displayed_auth_options]
    assert "Native Cognito" in names
    assert "Google Workspace" in names
    assert "AWS IAM Identity Center" in names


@then("each option presents a brief recommendation and link to deep-dive documentation")
def step_verify_option_links(context) -> None:
    for opt in context.displayed_auth_options:
        assert opt.get("doc_link") is not None
        assert opt.get("doc_link").startswith("/docs/")


@when('the visitor selects the "{auth_name}" authentication option')
def step_select_auth_option(context, auth_name: str) -> None:
    matching = [opt for opt in context.auth_options if opt["name"] == auth_name]
    assert len(matching) > 0
    context.selected_auth = matching[0]


@then("the option card expands to reveal step-by-step setup instructions")
def step_verify_expanded_instructions(context) -> None:
    assert context.selected_auth is not None
    # Simulated instruction expansion state
    context.is_expanded = True
    assert context.is_expanded is True


@then('the corresponding CLI login command "{expected_cmd}" is displayed')
def step_verify_login_cmd(context, expected_cmd: str) -> None:
    if context.selected_auth["id"] == "google":
        cmd = "auritus login --sso google"
    elif context.selected_auth["id"] == "identity-center":
        cmd = "auritus login --sso aws-sso"
    else:
        cmd = "auritus login --username <email>"
    assert cmd == expected_cmd


@when("the visitor reviews the voice model options")
def step_review_models(context) -> None:
    context.displayed_models = context.models


@when('the visitor selects the "{model_name}" model option')
def step_select_model(context, model_name: str) -> None:
    matching = [m for m in context.models if m["name"] == model_name]
    assert len(matching) > 0
    context.selected_model = matching[0]


@then(
    'the interactive embed code snippet updates to backend "{expected_backend}" and voice "{expected_voice}"'
)
def step_verify_snippet_update(
    context, expected_backend: str, expected_voice: str
) -> None:
    assert context.selected_model["id"] == expected_backend
    assert context.selected_model["voice"] == expected_voice


def find_model_card(context, model_name: str) -> dict:
    matching = [m for m in context.displayed_models if m["name"] == model_name]
    assert matching, f"no model card named {model_name!r}"
    return matching[0]


@then('the "{model_name}" card shows the license "{expected_license}"')
def step_verify_card_license(context, model_name: str, expected_license: str) -> None:
    assert find_model_card(context, model_name)["license"] == expected_license


@then('no model card is named "{model_name}"')
def step_verify_no_card_named(context, model_name: str) -> None:
    assert all(m["name"] != model_name for m in context.displayed_models)


@then('the "{model_name}" card shows the size "{expected_size}"')
def step_verify_card_size(context, model_name: str, expected_size: str) -> None:
    assert expected_size in find_model_card(context, model_name)["footprint"]


@then("no model card shows a latency figure")
def step_verify_no_latency(context) -> None:
    assert all("latency" not in m for m in context.displayed_models)


@then("no model card references an API job redeem URL")
def step_verify_no_job_urls(context) -> None:
    assert all("/jobs/" not in " ".join(m.values()) for m in context.displayed_models)
    assert "/redeem" not in WIZARD_SOURCE.read_text(encoding="utf-8")
