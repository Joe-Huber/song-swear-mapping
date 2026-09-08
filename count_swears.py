"""Count swear words in cached lyrics and write a wide-format CSV.

Input:  data/lyrics/*.txt caches produced by fetch_lyrics.py
Output: data/swear_counts.csv (one row per song, one column per swear stem)
"""

import csv
import re
from pathlib import Path

from fetch_lyrics import CACHE_DIR, SONG_LIST, cache_path_for, read_song_list
from swear_words import STEM_ORDER, count_stems

ROOT = Path(__file__).resolve().parent
OUTPUT_CSV = ROOT / "data" / "swear_counts.csv"

_SECTION = re.compile(r"\[[^\]]*\]")


def clean_lyrics(text: str) -> str:
    """Normalize lyrics into lowercase space-separated words, minus meta junk."""
    text = text.lower()
    cut = text.find("you might also like")
    if cut != -1:
        text = text[:cut]
    text = _SECTION.sub(" ", text)
    text = re.sub(r"\bembed\b|\bshare url\b|\bcopyembedcopy\b", " ", text)
    text = re.sub(r"[^a-z0-9* \n]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def main() -> None:
    rows = read_song_list()
    fields = ["Band", "Song", "Year", *STEM_ORDER, "Total"]

    records = []
    for index, row in enumerate(rows):
        record = {
            "Band": row.get("Band", "").strip(),
            "Song": row.get("Song", "").strip(),
            "Year": row.get("Year", "").strip(),
        }
        lyric_path = cache_path_for(index, record["Band"], record["Song"])
        if lyric_path.exists():
            text = clean_lyrics(lyric_path.read_text(encoding="utf-8"))
            counts = count_stems(text)
            record.update(counts)
            record["Total"] = sum(counts.values())
        else:
            record.update({stem: 0 for stem in STEM_ORDER})
            record["Total"] = 0
        records.append(record)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    print(f"Wrote {len(records)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()