import mobile_dashboard.app as dashboard_module


def test_mobile_home_injects_edge_research_shortcut():
    with (
        dashboard_module
        .app
        .test_request_context("/")
    ):
        response = (
            dashboard_module
            .app
            .response_class(
                (
                    "<html>"
                    "<body>"
                    "HOME"
                    "</body>"
                    "</html>"
                ),
                mimetype="text/html",
            )
        )

        result = (
            dashboard_module
            .add_edge_research_shortcut_to_dashboard(
                response
            )
        )

    html = result.get_data(
        as_text=True
    )

    assert (
        'id="edge-research-shortcut"'
        in html
    )

    assert (
        'href="/edge-research"'
        in html
    )


def test_edge_research_page_does_not_get_shortcut():
    with (
        dashboard_module
        .app
        .test_request_context(
            "/edge-research"
        )
    ):
        response = (
            dashboard_module
            .app
            .response_class(
                (
                    "<html>"
                    "<body>"
                    "EDGE PAGE"
                    "</body>"
                    "</html>"
                ),
                mimetype="text/html",
            )
        )

        result = (
            dashboard_module
            .add_edge_research_shortcut_to_dashboard(
                response
            )
        )

    html = result.get_data(
        as_text=True
    )

    assert (
        'id="edge-research-shortcut"'
        not in html
    )
