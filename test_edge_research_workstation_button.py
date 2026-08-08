import gui.trading_workstation as workstation_module


def test_open_edge_research_dashboard(
    monkeypatch,
):
    captured = {}

    def fake_open_new_tab(url):
        captured["url"] = url
        return True

    monkeypatch.setattr(
        workstation_module.webbrowser,
        "open_new_tab",
        fake_open_new_tab,
    )

    result = (
        workstation_module
        .open_edge_research_dashboard()
    )

    assert result is True

    assert (
        captured["url"]
        == (
            "http://127.0.0.1:5000/"
            "edge-research"
        )
    )


def test_add_edge_research_button(
    monkeypatch,
):
    captured = {}

    class FakeButton:
        def __init__(
            self,
            root,
            **kwargs,
        ):
            captured["root"] = root
            captured["kwargs"] = kwargs

        def place(
            self,
            **kwargs,
        ):
            captured["place"] = kwargs

    monkeypatch.setattr(
        workstation_module.tk,
        "Button",
        FakeButton,
    )

    fake_root = object()

    button = (
        workstation_module
        .add_edge_research_button(
            fake_root
        )
    )

    assert isinstance(
        button,
        FakeButton,
    )

    assert (
        captured["root"]
        is fake_root
    )

    assert (
        captured["kwargs"]["text"]
        == "Edge Research"
    )

    assert (
        captured["kwargs"]["command"]
        is workstation_module
        .open_edge_research_dashboard
    )

    assert (
        captured["place"]["anchor"]
        == "ne"
    )
