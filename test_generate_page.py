import csv
from html.parser import HTMLParser

from generate_page import build_dashboard, main


def _sample_rows():
    fields = ["Band", "Song", "Year", "fuck", "shit", "Total"]
    data = [
        {"Band": "Ice Band", "Song": "ICE Fuck You", "Year": "2026", "fuck": "76", "shit": "0", "Total": "76"},
        {"Band": "Clean Band", "Song": "Safe Song", "Year": "2000", "fuck": "0", "shit": "0", "Total": "0"},
        {"Band": "Mid Band", "Song": "Bullshit Town", "Year": "2010", "fuck": "2", "shit": "5", "Total": "7"},
    ]
    return fields, data


def test_build_dashboard_contains_rows():
    fields, data = _sample_rows()
    page = build_dashboard(data, fields)
    assert page.count("<tr") == 4  # header + 3 rows
    assert "ICE Fuck You" in page
    assert "Bullshit Town" in page


def test_build_dashboard_strips_required_chars():
    fields, data = _sample_rows()
    page = build_dashboard(data, fields)
    assert "<script>" in page and "</script>" in page
    assert "<style>" in page and "</style>" in page


class _WellFormed(HTMLParser):
    def error(self, message):  # legacy hook; feed() raises on bad input
        raise AssertionError(message)


def test_generated_file_is_valid_html(tmp_path):
    fields, data = _sample_rows()
    with (tmp_path / "in.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data)

    out = main(tmp_path / "in.csv", tmp_path / "out.html")

    parser = _WellFormed()
    parser.feed(out.read_text(encoding="utf-8"))
    assert out.exists()