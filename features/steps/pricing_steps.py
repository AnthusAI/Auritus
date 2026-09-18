"""Behave steps for marketing site pricing and delegation ladder."""

from __future__ import annotations

from pathlib import Path

from behave import given, then, when

SITE_DIR = Path(__file__).resolve().parents[2] / "site"
PAGE_PATH = SITE_DIR / "app" / "page.tsx"
COMPONENT_PATH = SITE_DIR / "components" / "DelegatedResponsibility.tsx"


@given("the aurit.us home page layout")
def step_home_page_layout(context) -> None:
    context.page_source = PAGE_PATH.read_text(encoding="utf-8")
    if COMPONENT_PATH.exists():
        context.component_source = COMPONENT_PATH.read_text(encoding="utf-8")
    else:
        context.component_source = ""


@when("I look at the delegated responsibility section")
def step_look_at_delegated_responsibility(context) -> None:
    assert (
        "DelegatedResponsibility" in context.page_source
    ), "DelegatedResponsibility component not included in HomePage"
    assert (
        'id="pricing"' in context.component_source
        or 'id="pricing"' in context.page_source
    ), 'Section id="pricing" not found'


@then("it headlines that you choose how much we help")
def step_headline_choose_how_much_we_help(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert (
        "you choose how much we help" in content
    ), "Headline 'You choose how much we help' not found"


@then("it states that you can run it yourself or enlist us")
def step_states_run_yourself_or_enlist(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert (
        "run the whole stack yourself" in content
    ), "Missing 'run the whole stack yourself'"
    assert "operate it" in content, "Missing 'operate it'"
    assert "set it up with you" in content, "Missing 'set it up with you'"
    assert "adapt a deployment" in content, "Missing 'adapt a deployment'"


@then("it offers four rungs:")
@then("it offers four rungs")
def step_offers_four_rungs(context) -> None:
    content = context.component_source + context.page_source
    for row in context.table:
        rung = row["rung"]
        price = row["price"]
        assert rung in content, f"Rung '{rung}' not found"
        assert price in content, f"Price '{price}' for rung '{rung}' not found"


@then('the assisted setup rung mentions a one-time fee of "$100 once"')
def step_assisted_setup_one_time_fee(context) -> None:
    content = context.component_source + context.page_source
    assert "$100 once" in content, "Missing '$100 once'"


@then("the managed rungs state that Anthus keeps the deployment updated")
def step_managed_rungs_keep_updated(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert (
        "keep the deployment updated" in content
        or "keeps the deployment updated" in content
    ), "Missing statement that Anthus keeps the deployment updated"


@then("they state that Anthus updates its own deployments first")
def step_updates_own_first(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert (
        "update our own deployments first" in content
        or "updates its own deployments first" in content
        or "update our own first" in content
    ), "Missing statement that Anthus updates its own deployments first"


@then("it states what happens if you stop paying")
def step_stop_paying(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert "stop paying" in content, "Missing 'stop paying' question"
    assert "in your account" in content, "Missing account retention statement"
    assert (
        "stop operating" in content or "stops operating" in content
    ), "Missing stop operating statement"
    assert "nothing is deleted" in content, "Missing nothing is deleted statement"


@then("it states what managed actually means")
def step_what_managed_means(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert (
        "what does managed actually mean" in content or "what managed means" in content
    ), "Missing 'what managed actually mean' question"
    assert (
        "apply updates" in content or "applies updates" in content
    ), "Missing updates statement"


@then("it states that you can move between self-setup and assisted setup")
def step_move_between_setup(context) -> None:
    content = (context.component_source + context.page_source).lower()
    assert (
        "move to assisted" in content or "move between" in content
    ), "Missing move between setup options"


@then('the navigation header includes a link to "Pricing"')
def step_nav_link_pricing(context) -> None:
    assert (
        'href="/#pricing"' in context.page_source
        or 'href="/pricing"' in context.page_source
    ), "Header nav does not link to pricing"
    assert (
        ">Pricing</Link>" in context.page_source
        or 'label: "Pricing"' in context.page_source
    ), 'Header nav does not have "Pricing" text'


@then('the footer includes a link to "Pricing"')
def step_footer_link_pricing(context) -> None:
    footer_idx = context.page_source.find('className="marketing-footer"')
    assert footer_idx != -1, "marketing-footer not found"
    footer_content = context.page_source[footer_idx:]
    assert (
        'href="/#pricing"' in footer_content or 'href="/pricing"' in footer_content
    ), "Footer does not link to pricing"
    assert (
        ">Pricing</Link>" in footer_content
    ), 'Footer does not have "Pricing" link text'
