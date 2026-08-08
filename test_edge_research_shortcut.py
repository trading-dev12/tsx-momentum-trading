from mobile_dashboard.edge_research_shortcut import (
    inject_edge_research_shortcut,
)


def test_inject_edge_research_shortcut():
    html = (
        "<html>"
        "<body>"
        "<h1>Northstar</h1>"
        "</body>"
        "</html>"
    )

    result = (
        inject_edge_research_shortcut(
            html
        )
    )

    assert (
        'id="edge-research-shortcut"'
        in result
    )

    assert (
        'href="/edge-research"'
        in result
    )

    assert (
        "Edge Research"
        in result
    )


def test_shortcut_is_not_duplicated():
    html = (
        "<html>"
        "<body>"
        '<a id="edge-research-shortcut">'
        "Edge Research"
        "</a>"
        "</body>"
        "</html>"
    )

    result = (
        inject_edge_research_shortcut(
            html
        )
    )

    assert (
        result.count(
            'id="edge-research-shortcut"'
        )
        == 1
    )


def test_shortcut_leaves_non_html_unchanged():
    text = "NOT HTML"

    assert (
        inject_edge_research_shortcut(
            text
        )
        == text
    )
