"""Generate a self-contained HTML dashboard from data/swear_counts.csv.

Writes a single HTML file with inline CSS and vanilla JS (no external
dependencies). Run as:  python generate_page.py
"""

import csv
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_CSV = ROOT / "data" / "swear_counts.csv"
OUTPUT_HTML = ROOT / "data" / "swear_counts.html"

INTENSITY = "rgba(220, 38, 38, {alpha:.2f})"


def _fmt(a) -> int:
    return int(float(a)) if str(a).strip() else 0


def build_dashboard(rows: list[dict], fields: list[str]):
    """Return the full HTML document as a string."""
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

    by_total = sorted(rows, key=lambda r: r["_total"], reverse=True)
    top_songs = by_total[:10]

    chart_songs = [
        (f"{r[fields[0]]} — {r[fields[1]]} ({r[fields[2]]})", r["_total"])
        for r in by_total[:20]
        if r["_total"] > 0
    ]
    chart_words = sorted(word_totals.items(), key=lambda kv: kv[1], reverse=True)

    decade_totals = {}
    for r in rows:
        yr = r[fields[2]].strip()
        if yr.isdigit():
            decade = int(yr) // 10 * 10
            decade_totals[decade] = decade_totals.get(decade, 0) + r["_total"]
    chart_decades = [
        (f"{decade}s", decade_totals[decade]) for decade in sorted(decade_totals)
    ]

    col_max = {stem: max((r[f"_c_{stem}"] for r in rows), default=0) for stem in stems}

    leaders = []
    for stem in sorted(word_totals):
        best = max(r[f"_c_{stem}"] for r in rows)
        songs = [r for r in rows if r[f"_c_{stem}"] == best]
        leaders.append((stem, best, songs))

    css = _css()
    summary = _summary_cards(len(rows), with_swears, total_swears, top_words)
    charts = _charts_section(chart_songs, chart_words, chart_decades)
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
{charts}
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
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 8px; }
.chart { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
.chart.span2 { grid-column: 1 / -1; }
.chart h3 { margin: 0 0 10px; font-size: 15px; color: var(--muted); font-weight: 600; }
.chart svg { width: 100%; height: auto; display: block; }
svg.chart-svg text { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; }
.hl { fill: var(--muted); font-size: 13px; }
.hv { fill: var(--text); font-size: 14px; font-weight: 700; font-variant-numeric: tabular-nums; }
.bar { fill: var(--accent); transition: fill 0.15s; }
.bar:hover { fill: #f87171; }
.tooltip {
  position: fixed; display: none; pointer-events: none; z-index: 50;
  background: #0b0d12; border: 1px solid var(--border); color: var(--text);
  padding: 6px 10px; border-radius: 6px; font-size: 13px; max-width: 320px;
}
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


def _truncate(text: str, limit: int = 24) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _svg_h_bars(items: list[tuple[str, int]]) -> str:
    """Horizontal bar chart from sorted (label, value) pairs, zero-dependency SVG."""
    items = [(label, value) for label, value in items if value > 0]
    if not items:
        return ""
    peak = max(value for _, value in items)
    width, label_w, value_w, row_h = 760, 190, 44, 30
    plot_x, plot_w = label_w, width - label_w - value_w
    height = 24 + row_h * len(items)

    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img">']
    for i, (label, value) in enumerate(items):
        y = 20 + i * row_h
        bar_w = max(int(plot_w * value / peak), 2)
        title = html.escape(f"{label} — {value}")
        parts.append(
            f'<g class="h-bar" data-label="{title}">'
            f'<rect class="bar" x="{plot_x}" y="{y}" width="{bar_w}" height="20" rx="4"/>'
            f'<text x="{plot_x - 8}" y="{y + 15}" text-anchor="end" class="hl">'
            f"{html.escape(_truncate(label))}</text>"
            f'<text x="{plot_x + bar_w + 8}" y="{y + 15}" class="hv">{value}</text>'
            f"<title>{title}</title>"
            f"</g>"
        )
    parts.append("</svg>")
    return "".join(parts)


def _svg_v_bars(buckets: list[tuple[str, int]]) -> str:
    """Vertical bar chart for decade buckets."""
    if not buckets:
        return ""
    peak = max(value for _, value in buckets) or 1
    width, height = 400, 190
    plot_l, plot_r, plot_t, plot_b = 30, width - 20, 22, 150
    slot = (plot_r - plot_l) / len(buckets)
    bar_w = slot * 0.5

    parts = [f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img">']
    parts.append(
        f'<line x1="{plot_l}" y1="{plot_b}" x2="{plot_r}" y2="{plot_b}"'
        ' stroke="var(--border)"'
        f'/>'
    )
    for i, (label, value) in enumerate(buckets):
        centre = plot_l + slot * i + slot / 2
        bar_h = int((plot_b - plot_t) * value / peak)
        y = plot_b - bar_h
        title = html.escape(f"{label} — {value}")
        parts.append(
            f'<g class="v-bar" data-label="{title}">'
            f'<rect class="bar" x="{centre - bar_w / 2:.1f}" y="{y}" '
            f'width="{bar_w:.1f}" height="{bar_h}" rx="4"/>'
            f'<text x="{centre:.1f}" y="{max(y - 6, 12)}" text-anchor="middle" class="hv">{value}</text>'
            f'<text x="{centre:.1f}" y="{plot_b + 16}" text-anchor="middle" class="hl">'
            f"{html.escape(label)}</text>"
            f"<title>{title}</title>"
            f"</g>"
        )
    parts.append("</svg>")
    return "".join(parts)


def _charts_section(songs, words, decades) -> str:
    return f"""<section class="charts">
  <div class="chart span2"><h3>Top songs by total swears</h3>{_svg_h_bars(songs)}</div>
  <div class="chart"><h3>Most frequent swear words</h3>{_svg_h_bars(words)}</div>
  <div class="chart"><h3>Swears per decade</h3>{_svg_v_bars(decades)}</div>
</section>
<div id="tip" class="tooltip"></div>
"""


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

  var tip = document.getElementById("tip");
  var svgs = Array.prototype.slice.call(document.querySelectorAll("svg.chart-svg"));
  svgs.forEach(function (svg) {
    svg.addEventListener("mouseover", function (e) {
      var bar = e.target.closest ? e.target.closest(".h-bar, .v-bar") : null;
      if (bar) { tip.textContent = bar.getAttribute("data-label"); tip.style.display = "block"; }
    });
    svg.addEventListener("mousemove", function (e) {
      tip.style.left = (e.clientX + 12) + "px";
      tip.style.top = (e.clientY + 12) + "px";
    });
    svg.addEventListener("mouseleave", function () { tip.style.display = "none"; });
  });
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