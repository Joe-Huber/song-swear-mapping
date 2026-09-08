# Song Swear Mapping

[![Language: Python](https://img.shields.io/badge/language-Python-3776AB.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Unmaintained](https://img.shields.io/badge/status-unmaintained-red.svg)]()

A small tool that maps which bands swear the most by comparing the lyrics of
101 punk/rock songs against a curated list of swear words.

> **Heads up:** this is a small, unmaintained project published for the sake of
> open source. It's shared as-is — no guarantees, no active development. Feel
> free to fork, learn from it, or take whatever pieces are useful.

## What it does

1. Fetches lyrics for every song in `song_list.csv` via the
   [Genius](https://genius.com) API ([lyricsgenius](https://pypi.org/project/lyricsgenius/)).
2. Counts swear words (stemmed: `fuck` covers `fucking`, `motherfucker`, …).
3. Emits `data/swear_counts.csv` and renders a self-contained HTML dashboard
   with summary stats, rankings, sortable table, and SVG charts.

## Usage

```sh
pip install -r requirements.txt

echo "GENIUS_ACCESS_TOKEN=..." > .env        # one-time token from genius.com/api-clients
python fetch_lyrics.py                        # cache lyrics to data/lyrics/
python count_swears.py                        # write data/swear_counts.csv
python generate_page.py                       # write data/swear_counts.html
```

## Files

| File | Purpose |
| --- | --- |
| `fetch_lyrics.py` | Fetch + cache lyrics from Genius |
| `swear_words.py` | Curated swear word stems and variants |
| `count_swears.py` | Count swears, write wide CSV |
| `generate_page.py` | Build the static HTML dashboard |

## License

[MIT](LICENSE)