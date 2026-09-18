"""Behave steps for DOM content extraction rules."""

from __future__ import annotations

from html.parser import HTMLParser

from behave import given, then, when

SKIP_TAGS = frozenset({"script", "style", "noscript", "template"})


class _TextExtractor(HTMLParser):
    """Extract visible text while skipping non-narratable tags."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._suppress_stack: list[bool] = []
        self._voice_stack: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        parent_suppressed = bool(self._suppress_stack and self._suppress_stack[-1])
        ignored = any(key == "data-auritus-ignore" for key, _ in attrs)
        suppressed = parent_suppressed or tag.lower() in SKIP_TAGS or ignored
        self._suppress_stack.append(suppressed)

        voice = None
        if not suppressed:
            for key, val in attrs:
                if key in ("data-auritus-voice", "data-auritus-voice-id") and val:
                    voice = val.strip()
                    break
            if voice:
                self.parts.append(f"[[auritus:voice:{voice}]]")
        self._voice_stack.append(voice)

    def handle_endtag(self, tag: str) -> None:
        if self._suppress_stack:
            self._suppress_stack.pop()
        if self._voice_stack:
            voice = self._voice_stack.pop()
            if voice:
                self.parts.append("[[auritus:voice:reset]]")

    def handle_data(self, data: str) -> None:
        if self._suppress_stack and self._suppress_stack[-1]:
            return
        if data.strip():
            self.parts.append(data)


def _extract(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


@given('a page root with visible text "{text}"')
def step_root_text(context, text: str) -> None:
    context.root_html = f"<div id='root'><p>{text}</p></div>"


@given('the root also contains a script element with "{payload}"')
def step_script(context, payload: str) -> None:
    context.root_html = context.root_html.replace(
        "</div>",
        f"<script>{payload}</script></div>",
    )


@given('an example page with nav text "{nav}" and article text "{article}"')
def step_example_page(context, nav: str, article: str) -> None:
    context.full_html = (
        f"<main><nav>{nav}</nav>"
        f"<article class='example-article'><h1>{article}</h1></article></main>"
    )
    context.root_selector = None


@given('the embed root selector is "{selector}"')
def step_root_selector(context, selector: str) -> None:
    context.root_selector = selector
    if selector == ".example-article":
        start = context.full_html.find("<article")
        end = context.full_html.find("</article>") + len("</article>")
        context.root_html = context.full_html[start:end]
    else:
        context.root_html = context.full_html


@given('an article with spoken text "{spoken}"')
def step_article_spoken(context, spoken: str) -> None:
    context.article_html = f"<article><p>{spoken}</p></article>"


@given('the article also contains ignored text "{ignored}"')
def step_article_ignored(context, ignored: str) -> None:
    context.article_html = context.article_html.replace(
        "</article>",
        f"<p data-auritus-ignore>{ignored}</p></article>",
    )


@when("the generator extracts TTS text from that root")
def step_extract(context) -> None:
    context.tts_text = _extract(context.root_html)


@when("the generator extracts TTS text from that article")
def step_extract_article(context) -> None:
    context.tts_text = _extract(context.article_html)


@then('the TTS text includes "{snippet}"')
def step_includes(context, snippet: str) -> None:
    assert snippet in context.tts_text, context.tts_text


@then('the TTS text does not include "{snippet}"')
def step_excludes(context, snippet: str) -> None:
    assert snippet not in context.tts_text, context.tts_text
