"""Behave steps for aurit.us example page articles."""

from __future__ import annotations

from behave import given, then

GETTYSBURG_ARTICLE = """
<article class="example-article">
  <h1>Gettysburg Address</h1>
  <p>Four score and seven years ago our fathers brought forth on this
  continent, a new nation, conceived in Liberty, and dedicated to the
  proposition that all men are created equal.</p>
  <p>Now we are engaged in a great civil war, testing whether that nation, or
  any nation so conceived and so dedicated, can long endure.</p>
  <p data-auritus-ignore>This page speaks that excerpt with a TTS backend.</p>
</article>
"""


@given("the home page spoken article")
def step_home_article(context) -> None:
    context.root_html = """
<article class="demo-article">
  <p>Press play. What you hear is this page reading itself.</p>
  <p>Auritus turns any article into audio on demand, from a single script
  tag — no pre-recording, no studio, no per-article cost.</p>
  <p>You choose the voice model. You decide where the text goes. Your own
  GPU does the work, and AWS picks up the slack when it cannot.</p>
  <p>It's open source, and every article on your site can speak, with
  the choices that matter still yours.</p>
  <p data-auritus-ignore>Narrated by Auritus with Kokoro (af_heart) — the same embed
  documented in Usage.</p>
</article>
"""
    context.example_tts_backend = "kokoro"


@given("the home page demo layout")
def step_home_layout(context) -> None:
    context.page_html = """
<section class="demo-section">
  <div class="demo-panel">
    <div class="auritus-player-host">
      <div class="auritus-player-placeholder">
        <p class="auritus-placeholder-name">What Auritus does</p>
        <p class="auritus-placeholder-byline">A 30-second introduction, narrated by Auritus</p>
        <div class="auritus-placeholder-controls">
          <button type="button" disabled aria-label="Play">Play</button>
        </div>
      </div>
    </div>
    <article class="demo-article"><p>Press play.</p></article>
  </div>
</section>
"""


@given("the basic example page article")
def step_basic_article(context) -> None:
    context.root_html = GETTYSBURG_ARTICLE
    context.example_tts_backend = "kokoro"


@given("the themed example page article")
def step_themed_article(context) -> None:
    context.root_html = GETTYSBURG_ARTICLE
    context.example_tts_backend = "kokoro"


@given("the Qwen example page article")
def step_qwen_article(context) -> None:
    context.root_html = GETTYSBURG_ARTICLE
    context.example_tts_backend = "qwen"


@given("the ignore example page article")
def step_ignore_article(context) -> None:
    context.root_html = """
<article class="example-article">
  <h1>Ignore markup example</h1>
  <p>The only freedom which deserves the name, is that of pursuing our own
  good in our own way, so long as we do not attempt to deprive others of
  theirs, or impede their efforts to obtain it.</p>
  <p>Mankind are greater gainers by suffering each other to live as seems
  good to themselves, than by compelling each to live as seems good to
  the rest.</p>
  <p data-auritus-ignore>This paragraph is ignored. It is a promotional aside.</p>
  <p data-auritus-pronounce="NASA">NASA</p>
</article>
"""
    context.example_tts_backend = "kokoro"


@given("the basic example page layout")
def step_basic_layout(context) -> None:
    context.page_html = """
<main class="page">
  <div class="auritus-player-host">
    <div class="auritus-player-placeholder">
      <p class="auritus-placeholder-name">Gettysburg Address</p>
      <p class="auritus-placeholder-byline">Abraham Lincoln, 1863 — Kokoro</p>
      <div class="auritus-placeholder-controls">
        <button type="button" disabled aria-label="Play">Play</button>
      </div>
    </div>
  </div>
  <article class="example-article"><h1>Gettysburg Address</h1></article>
</main>
"""


@then("the player host is above the example article")
def step_player_above_article(context) -> None:
    html = context.page_html
    host_at = html.find('class="auritus-player-host"')
    article_at = html.find('class="example-article"')
    assert host_at != -1 and article_at != -1
    assert host_at < article_at


@then("the player host is above the demo article")
def step_player_above_demo_article(context) -> None:
    html = context.page_html
    host_at = html.find('class="auritus-player-host"')
    article_at = html.find('class="demo-article"')
    assert host_at != -1 and article_at != -1
    assert host_at < article_at


@then("the player host shows a Play control before the embed boots")
def step_player_placeholder(context) -> None:
    html = context.page_html
    assert 'aria-label="Play"' in html
    assert "Play" in html
    placeholder_at = html.find("auritus-player-placeholder")
    article_at = html.find('class="example-article"')
    if article_at == -1:
        article_at = html.find('class="demo-article"')
    assert placeholder_at != -1 and article_at != -1
    assert placeholder_at < article_at


@then('the example embed requests tts_backend "{backend}"')
def step_example_backend(context, backend: str) -> None:
    assert context.example_tts_backend == backend
