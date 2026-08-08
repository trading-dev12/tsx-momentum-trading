"""
Northstar Quant
Mobile Edge Research Shortcut

Provides a small read-only navigation shortcut for the
mobile dashboard.

This module does not modify trading data or strategy logic.
"""


EDGE_RESEARCH_SHORTCUT_HTML = """
<a
    id="edge-research-shortcut"
    href="/edge-research"
    style="
        position: fixed;
        right: max(16px, env(safe-area-inset-right));
        bottom: max(16px, env(safe-area-inset-bottom));
        z-index: 9999;
        display: inline-block;
        padding: 12px 16px;
        border-radius: 999px;
        background: #2563eb;
        color: #ffffff;
        font-family: Arial, sans-serif;
        font-size: 14px;
        font-weight: bold;
        text-decoration: none;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.30);
    "
>
    Edge Research
</a>
"""


def inject_edge_research_shortcut(html):
    """
    Add the Edge Research shortcut before the closing body tag.
    """

    if not isinstance(
        html,
        str,
    ):
        return html

    if (
        'id="edge-research-shortcut"'
        in html
    ):
        return html

    closing_body = "</body>"

    if closing_body not in html:
        return html

    return html.replace(
        closing_body,
        (
            EDGE_RESEARCH_SHORTCUT_HTML
            + closing_body
        ),
        1,
    )
