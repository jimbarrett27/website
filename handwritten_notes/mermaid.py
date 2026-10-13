"""Mermaid source → PNG, for previewing a redrawn flowchart in the chat.

Obsidian renders the Mermaid in the note itself; this is only so Telegram can show
it too. Mermaid is a JavaScript library, so we render it in headless Chromium via
Playwright. Only the library is fetched from the CDN; the diagram never leaves the
machine. The browser is a one-off install on the server:

    uv run playwright install chromium-headless-shell
"""

from playwright.sync_api import sync_playwright

MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"
PAGE = "<html><body style='margin:0;background:white'><div id='d' style='display:inline-block;padding:16px'></div></body></html>"
RENDER = """async source => {
    mermaid.initialize({startOnLoad: false, theme: "default"});
    const {svg} = await mermaid.render("diagram", source);
    document.getElementById("d").innerHTML = svg;
}"""
TIMEOUT_MS = 30_000


def render_png(source: str) -> bytes:
    """Render a Mermaid diagram at 2x scale; raises if the source doesn't parse."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(device_scale_factor=2)
            page.set_default_timeout(TIMEOUT_MS)
            page.set_content(PAGE)
            page.add_script_tag(url=MERMAID_JS)
            page.evaluate(RENDER, source)
            return page.locator("#d").screenshot()
        finally:
            browser.close()
