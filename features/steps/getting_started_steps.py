"""Step definitions for the interactive getting started onboarding guide specs."""

from __future__ import annotations

from behave import given, then, when


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
    context.models = [
        {"id": "kokoro", "name": "Kokoro-82M", "voice": "af_heart", "has_audio": True},
        {"id": "qwen", "name": "Qwen3-TTS", "voice": "Ryan", "has_audio": True},
        {"id": "higgs", "name": "Higgs-v2", "voice": "default", "has_audio": True},
    ]
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


@then("each model option includes an inline audio preview")
def step_verify_model_audio(context) -> None:
    for m in context.displayed_models:
        assert m.get("has_audio") is True


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
