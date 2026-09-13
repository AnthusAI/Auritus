"""Behave steps for aurit.us example page articles."""

from __future__ import annotations

from behave import given, then


@given("the basic example page article")
def step_basic_article(context) -> None:
    context.root_html = """
<article class="example-article">
  <h1>Basic narration example</h1>
  <p>Four score and seven years ago our fathers brought forth on this
  continent, a new nation, conceived in Liberty, and dedicated to the
  proposition that all men are created equal.</p>
  <p>Now we are engaged in a great civil war, testing whether that nation, or
  any nation so conceived and so dedicated, can long endure.</p>
</article>
"""
    context.example_tts_backend = "kokoro"


@given("the themed example page article")
def step_themed_article(context) -> None:
    context.root_html = """
<article class="example-article">
  <h1>Themed player example</h1>
  <p>It is a truth universally acknowledged, that a single man in
  possession of a good fortune, must be in want of a wife.</p>
  <p>However little known the feelings or views of such a man may be on
  his first entering a neighbourhood, this truth is so well fixed in the
  minds of the surrounding families, that he is considered the rightful
  property of some one or other of their daughters.</p>
</article>
"""
    context.example_tts_backend = "kokoro"


@given("the Qwen example page article")
def step_qwen_article(context) -> None:
    context.root_html = """
<article class="example-article">
  <h1>Qwen narration example</h1>
  <p>When on board H.M.S. Beagle, as naturalist, I was much struck with
  certain facts in the distribution of the inhabitants of South America.</p>
  <p>On my return home, it occurred to me, in 1837, that something might
  perhaps be made out on this question.</p>
</article>
"""
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
    <p class="auritus-player-placeholder">Loading player</p>
  </div>
  <article class="example-article"><h1>Basic narration example</h1></article>
</main>
"""


@then("the player host is above the example article")
def step_player_above_article(context) -> None:
    html = context.page_html
    host_at = html.find('class="auritus-player-host"')
    article_at = html.find('class="example-article"')
    assert host_at != -1 and article_at != -1
    assert host_at < article_at


@then('the player host shows "{label}" before the embed boots')
def step_player_placeholder(context, label: str) -> None:
    html = context.page_html
    assert label in html
    placeholder_at = html.find("auritus-player-placeholder")
    article_at = html.find('class="example-article"')
    assert placeholder_at != -1 and placeholder_at < article_at


@then('the example embed requests tts_backend "{backend}"')
def step_example_backend(context, backend: str) -> None:
    assert context.example_tts_backend == backend
