"""Generate a self-contained HTML dashboard from data/swear_counts.csv.

Writes a single HTML file with inline CSS and vanilla JS (no external
dependencies). Run as:  python generate_page.py
"""

import csv
import html
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_CSV = ROOT / "data" / "swear_counts.csv"
OUTPUT_HTML = ROOT / "data" / "swear_counts.html"

INTENSITY = "rgba(220, 38, 38, {alpha:.2f})"


def _fmt(a) -> int:
    return int(float(a)) if str(a).strip() else 0


def build_dashboard(rows: list[dict], fields: list[str]):
    """Return the full HTML document as a string."""
    band, song, year = fields[0], fields[1], fields[2]
    stems = fields[3:-1]
    total_field = fields[-1]

    for row in rows:
        for stem in stems:
            row[f"_c_{stem}"] = _fmt(row.get(stem, 0))
        row["_total"] = _fmt(row.get(total_field, 0))

    total_swears = sum(r["_total"] for r in rows)
    with_swears = sum(1 for r in rows if r["_total"] > 0)

    word_totals = {stem: sum(r[f"_c_{stem}"] for r in rows) for stem in stems}
    word_totals = {k: v for k, v in word_totals.items() if v > 0}
    top_words = sorted(word_totals.items(), key=lambda kv: kv[1], reverse=True)[:5]

    top_songs = sorted(rows, key=lambda r: r["_total"], reverse=True)[:10]

    col_max = {stem: max((r[f"_c_{stem}"] for r in rows), default=0) for stem in stems}

    leaders = []
    for stem in sorted(word_totals):
        best = max(r[f"_c_{stem}"] for r in rows)
        songs = [r for r in rows if r[f"_c_{stem}"] == best]
        leaders.append((stem, best, songs))

    css = _css()
    summary = _summary_cards(len(rows), with_swears, total_swears, top_words)
    rankings = _rankings(top_songs, top_words, leaders, fields)
    table = _table(rows, fields, stems, col_max, total_field)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Swear Song Dashboard</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>Swear Song Dashboard</h1>
  <p class="sub">Built from <code>data/swear_counts.csv</code> · {len(rows)} songs</p>
</header>
{summary}
{rankings}
<main>
  <div class="controls">
    <input id="filter" type="search" placeholder="Filter by band or song…">
    <label><input id="swears-only" type="checkbox"> Only songs with swears</label>
    <button id="reset">Reset</button>
  </div>
  <div class="scroll">
    <table id="songs">
      <thead>{_headers(fields)}</thead>
      <tbody>{table}</tbody>
    </table>
  </div>
</main>
<script>{_js(len(fields) - 1)}</script>
</body>
</html>
"""


def _css() -> str:
    return """\
:root {
  --bg: #101218;
  --panel: #1a1d26;
  --panel2: #21252f;
  --text: #e8eaf0;
  --muted: #9aa1b0;
  --accent: #ef4444;
  --border: #2c313d;
}
* { box-sizing: border-box; }
body {
  margin: 0 auto; max-width: 1100px; padding: 24px 20px 60px;
  background: var(--bg); color: var(--text);
  font: 15px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}
h1 { margin: 0; font-size: 28px; }
.sub { margin: 4px 0 24px; color: var(--muted); }
code { color: var(--accent); font-size: 0.9em; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 24px; }
.card { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
.card .num { font-size: 26px; font-weight: 700; color: var(--accent); }
.card .label { color: var(--muted); font-size: 13px; }
h2 { font-size: 18px; margin: 28px 0 10px; }
.list { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 8px 16px; margin-bottom: 12px; }
.list li { margin: 6px 0; }
.chip { display: inline-block; min-width: 34px; text-align: right; font-weight: 700; color: var(--accent); }
.controls { display: flex; gap: 14px; align-items: center; margin: 20px 0 10px; flex-wrap: wrap; }
.controls input[type="search"] { background: var(--panel2); border: 1px solid var(--border); color: var(--text); border-radius: 6px; padding: 7px 10px; min-width: 240px; }
.controls button { background: var(--panel2); border: 1px solid var(--border); color: var(--text); border-radius: 6px; padding: 7px 12px; cursor: pointer; }
.scroll { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; }
table { border-collapse: collapse; width: 100%; font-size: 14px; }
th, td { padding: 8px 10px; text-align: right; white-space: nowrap; }
th { position: sticky; top: 0; background: var(--panel2); cursor: pointer; user-select: none; }
th.str { text-align: left; }
td.str { text-align: left; }
td.num { font-variant-numeric: tabular-nums; }
tbody tr { border-top: 1px solid var(--border); }
tbody tr.dim { color: #5c6270; }
tbody tr.zero { opacity: 0.45; }
th .dir { color: var(--accent); }
"""


def _summary_cards(total, with_swears, total_swears, top_words) -> str:
    top = top_words[0] if top_words else ("—", 0)
    cards = [
        ("Songs", total),
        ("With swears", with_swears),
        ("Total swears", total_swears),
        (f"Top word · {html.escape(top[0])}", top[1]),
    ]
    body = "".join(
        f'<div class="card"><div class="num">{num}</div>'
        f'<div class="label">{html.escape(label)}</div></div>'
        for label, num in cards
    )
    return f'<section class="cards">{body}</section>'


def _rankings(top_songs, top_words, leaders, fields) -> str:
    songs = "".join(
        f"<li><span class=\"chip\">{r['_total']}</span> "
        f"{html.escape(r[fields[0]])} — {html.escape(r[fields[1]])} "
        f"({html.escape(r[fields[2]])})</li>"
        for r in top_songs
    )
    words = "".join(
        f"<li><span class=\"chip\">{count}</span> {html.escape(stem)}</li>"
        for stem, count in top_words
    )
    leaders_html = ""
    for stem, best, songs_list in leaders:
        who = ", ".join(
            f"{html.escape(s[fields[0]])} — {html.escape(s[fields[1]])}"
            for s in songs_list[:3]
        )
        leaders_html += (
            f"<li><span class=\"chip\">{best}</span> <strong>{html.escape(stem)}</strong>"
            f" · {who}</li>"
        )

    return f"""\
<section>
  <h2>Top songs by total swears</h2>
  <ul class="list">{songs}</ul>
  <h2>Most frequent swear words</h2>
  <ul class="list">{words}</ul>
  <h2>Swear-word leaders</h2>
  <ul class="list">{leaders_html}</ul>
</section>
"""


def _headers(fields) -> str:
    cells = []
    for i, f in enumerate(fields):
        kind = "str" if i < 2 else "num"
        cells.append(
            f'<th class="{kind}" data-col="{i}" data-type="{kind}">'
            f'{html.escape(f)} <span class="dir"></span></th>'
        )
    return "<tr>" + "".join(cells) + "</tr>"


def _table(rows, fields, stems, col_max, total_field) -> str:
    body = []
    for r in rows:
        total = r["_total"]
        cls = "dim" if total > 0 else "zero"
        cells = [
            f'<td class="str" data-sort="{html.escape(r[fields[0]].lower())}">{html.escape(r[fields[0]])}</td>',
            f'<td class="str" data-sort="{html.escape(r[fields[1]].lower())}">{html.escape(r[fields[1]])}</td>',
            f'<td class="num" data-sort="{r[fields[2]]}">{html.escape(r[fields[2]])}</td>',
        ]
        for stem in stems:
            val = r[f"_c_{stem}"]
            mx = col_max[stem]
            style = ""
            if val:
                alpha = 0.12 + 0.72 * (val / mx)
                style = f' style="background:{INTENSITY.format(alpha=alpha)}"'
            cells.append(f'<td class="num" data-sort="{val}"{style}>{val}</td>')
        cells.append(f'<td class="num" data-sort="{total}"><strong>{total}</strong></td>')
        body.append(f'<tr class="{cls}" data-total="{total}">{"".join(cells)}</tr>')
    return "".join(body)


def _js(total_index) -> str:
    return """\
(function () {
  var table = document.getElementById("songs");
  var tbody = table.tBodies[0];
  var heads = table.tHead.rows[0].cells;
  var col = %d;
  var dir = "desc";

  function value(cell, type) {
    var v = cell.getAttribute("data-sort") ||
            cell.textContent.trim().toLowerCase();
    return type === "num" ? (parseFloat(v) || 0) : v;
  }

  function sort(index, type) {
    var rows = Array.from(tbody.rows);
    var m = 1;
    if (col === index) { dir = dir === "asc" ? "desc" : "asc"; }
    else { dir = type === "num" ? "desc" : "asc"; }
    m = dir === "asc" ? 1 : -1;
    col = index;
    rows.sort(function (a, b) {
      var va = value(a.cells[index], type);
      var vb = value(b.cells[index], type);
      return va < vb ? -m : va > vb ? m : 0;
    });
    rows.forEach(function (row) { tbody.appendChild(row); });
    var dirs = Array.prototype.map.call(heads, function () { return ""; });
    dirs[index] = dir === "asc" ? "▲" : "▼";
    Array.prototype.forEach.call(heads, function (th, i) {
      th.querySelector(".dir").textContent = dirs[i];
    });
  }

  Array.prototype.forEach.call(heads, function (th) {
    th.addEventListener("click", function () {
      sort(parseInt(th.dataset.col, 10), th.dataset.type);
    });
  });

  var filter = document.getElementById("filter");
  var only = document.getElementById("swears-only");
  var reset = document.getElementById("reset");

  function apply() {
    var q = filter.value.toLowerCase();
    Array.prototype.forEach.call(tbody.rows, function (row) {
      var match = !q || row.textContent.toLowerCase().indexOf(q) !== -1;
      var swears = only.checked && parseInt(row.getAttribute("data-total"), 10) === 0;
      row.style.display = match && !swears ? "" : "none";
    });
  }
  filter.addEventListener("input", apply);
  only.addEventListener("change", apply);
  reset.addEventListener("click", function () {
    filter.value = ""; only.checked = false; apply();
    sort(col, heads[col].dataset.type);
  });

  sort(col, heads[col].dataset.type);
})();
""" % total_index


def main(input_csv: Path = INPUT_CSV, output_html: Path = OUTPUT_HTML) -> Path:
    with input_csv.open(newline="") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames or []
        rows = list(reader)

    if len(fields) < 5:
        raise ValueError(f"Unexpected columns in {input_csv}: {fields}")

    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(build_dashboard(rows, fields), encoding="utf-8")
    return output_html


if __name__ == "__main__":
    path = main()
    print(f"Wrote {path}")