import mobile_dashboard.app as dashboard_module


def test_edge_research_route(
    monkeypatch,
):
    captured = {}

    fake_data = {
        "strategy": "Momentum",
    }

    def fake_build(
        journal_path,
        strategy_name="Momentum",
    ):
        captured[
            "journal_path"
        ] = journal_path

        captured[
            "strategy_name"
        ] = strategy_name

        return fake_data

    monkeypatch.setattr(
        dashboard_module,
        "build_edge_research_dashboard_data",
        fake_build,
    )

    monkeypatch.setattr(
        dashboard_module,
        "render_edge_research_page",
        lambda data: (
            "<html>"
            "<body>"
            "EDGE ROUTE OK"
            "</body>"
            "</html>"
        ),
    )

    client = (
        dashboard_module
        .app
        .test_client()
    )

    response = client.get(
        "/edge-research"
    )

    assert response.status_code == 200

    assert (
        "EDGE ROUTE OK"
        in response.get_data(
            as_text=True
        )
    )

    assert (
        captured[
            "journal_path"
        ].name
        == "paper_trade_journal.csv"
    )

    assert (
        captured[
            "strategy_name"
        ]
        == "Momentum"
    )

    assert (
        response.mimetype
        == "text/html"
    )
