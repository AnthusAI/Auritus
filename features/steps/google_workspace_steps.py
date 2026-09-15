"""Step definitions for the Google Workspace SSO guide specification."""

from __future__ import annotations

from pathlib import Path
from behave import given, then, when

DOCS_ROOT = Path(__file__).resolve().parents[2] / "site" / "app" / "docs"
COMPONENTS_ROOT = Path(__file__).resolve().parents[2] / "site" / "components"


@given("an administrator configuring Google Workspace SSO for Auritus")
def step_admin_configuring_google(context) -> None:
    context.target = "google_workspace"


@when("the administrator views the Google Workspace setup documentation")
def step_view_google_documentation(context) -> None:
    guide_path = DOCS_ROOT / "security" / "google-workspace" / "page.tsx"
    assert guide_path.exists(), f"Guide page not found at {guide_path}"
    context.doc_text = guide_path.read_text(encoding="utf-8")


@then(
    'the documentation specifies the authorized redirect URI format "https://<cognito-domain-prefix>.auth.<region>.amazoncognito.com/oauth2/idpresponse"'
)
def step_verify_redirect_uri_format(context) -> None:
    assert "/oauth2/idpresponse" in context.doc_text
    assert "amazoncognito.com/oauth2/idpresponse" in context.doc_text


@then(
    "the documentation specifies the authorized JavaScript origins for Cognito and local developer consoles"
)
def step_verify_js_origins(context) -> None:
    assert "Authorized JavaScript origins" in context.doc_text
    assert "amazoncognito.com" in context.doc_text
    assert "localhost" in context.doc_text


@then(
    "the documentation includes instructions for AWS Secrets Manager credentials structure"
)
def step_verify_secrets_instructions(context) -> None:
    assert "Secrets Manager" in context.doc_text
    assert "client_id" in context.doc_text
    assert "client_secret" in context.doc_text


@then('the documentation provides troubleshooting steps for "{error_name}"')
def step_verify_troubleshooting_steps(context, error_name: str) -> None:
    assert error_name in context.doc_text


@then('the deep-dive documentation link navigates to "{expected_url}"')
def step_verify_wizard_doc_link(context, expected_url: str) -> None:
    wizard_path = COMPONENTS_ROOT / "GettingStartedWizard.tsx"
    assert wizard_path.exists(), f"Wizard not found at {wizard_path}"
    content = wizard_path.read_text(encoding="utf-8")
    assert (
        expected_url in content
    ), f"Expected {expected_url} to be linked in GettingStartedWizard.tsx"


@then(
    "the inline expanding drawer details the authorized redirect URI and javascript origins"
)
def step_verify_inline_drawer_details(context) -> None:
    wizard_path = COMPONENTS_ROOT / "GettingStartedWizard.tsx"
    content = wizard_path.read_text(encoding="utf-8")
    assert "/oauth2/idpresponse" in content
    assert "amazoncognito.com" in content
