"""Fetch lyrics for every song in song_list.csv and cache them to disk.

Uses the LyricsGenius client (official Genius API). Requires a Genius
access token, provided via the GENIUS_ACCESS_TOKEN environment variable.
"""

import csv
import os
import re
import sys
from pathlib import Path

import lyricsgenius
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
SONG_LIST = ROOT / "song_list.csv"
CACHE_DIR = ROOT / "data" / "lyrics"
MISSES_CSV = ROOT / "data" / "misses.csv"

BAND_OVERRIDES = {
    "green day": "Green Day",
    "pennywise": "Pennywise",
    "face to face": "Face to Face",
    "teenage bottlerocket": "Teenage Bottlerocket",
    "social d": "Social Distortion",
    "decendents": "Descendents",
    "hüsker dü": "Hüsker Dü",
    "husker du": "Hüsker Dü",
    "lars fredrickson and the b": "Lars Frederiksen and the Bastards",
    "mister t experience": "The Mr. T Experience",
    "sex pistols": "Sex Pistols",
    "gen x": "Generation X",
    "distillers": "The Distillers",
    "get dead": "Get Dead",
    "last gang": "The Last Gang",
    "interruptors": "The Interrupters",
    "bombpops": "The Bombpops",
    "armstrongs": "The Armstrongs",
    "violents": "Violent Femmes",
    "dollheads": "The Dollheads",
}

SONG_OVERRIDES = {
    "blitsgreig bop": "Blitzkrieg Bop",
    "bro hym": "Bro Hymn",
    "good riddence": "Good Riddance",
    "the kid's aren't alright": "The Kids Aren't Alright",
    "i'm not ok": "I'm Not Okay (I Promise)",
    "take 'em all": "Take 'Em All",
    "i don't wanna grow up": "I Wanna Be Sedated",
    "keasby nights": "Keasbey Nights",
    "fuckmylife 666": "FuckMyLife666",
    "99 red balloons": "99 Red Balloons",
    "i was wrong": "I Was Wrong",
    "do what you want": "Do What You Want",
}


def read_song_list() -> list[dict]:
    """Return the rows of song_list.csv as dicts."""
    with SONG_LIST.open(newline="") as fh:
        return [row for row in csv.DictReader(fh)]


def normalize(row: dict) -> tuple[str, str]:
    """Return cleaned (band, song) keys used for the API search."""
    band = (row["Band"] or "").strip()
    song = (row["Song"] or "").strip()
    band_key = BAND_OVERRIDES.get(band.casefold(), band)
    song_key = SONG_OVERRIDES.get(song.casefold(), song)
    return band_key, song_key


def cache_path_for(index: int, band: str, song: str) -> Path:
    """Return the cache file path for a song (0-based index)."""
    slug = re.sub(r"[^\w .\-]+", "_", f"{band} - {song}").strip()
    return CACHE_DIR / f"{index:03d}-{slug}.txt"


def main() -> None:
    token = os.environ.get("GENIUS_ACCESS_TOKEN")
    if not token:
        sys.exit(
            "GENIUS_ACCESS_TOKEN not set. Get a free token at "
            "https://genius.com/api-clients and `export GENIUS_ACCESS_TOKEN=...`"
        )

    genius = lyricsgenius.Genius(
        token,
        timeout=15,
        retries=3,
        sleep_time=1.0,
    )

    songs = read_song_list()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    misses: list[dict] = []

    for index, row in enumerate(songs):
        band = (row["Band"] or "").strip()
        song = (row["Song"] or "").strip()
        band_key, song_key = normalize(row)

        out = cache_path_for(index, band, song)
        if out.exists():
            print(f"[{index + 1:3d}/{len(songs)}] cached  {band} - {song}")
            continue

        try:
            found = genius.search_song(song_key, artist=band_key)
        except Exception as exc:  # noqa: BLE001 - keep the run alive per song
            print(f"[{index + 1:3d}/{len(songs)}] error   {band} - {song}: {exc}")
            misses.append(
                {"index": index, "Band": band, "Song": song, "Year": row.get("Year", ""), "reason": str(exc)}
            )
            continue

        if found is None:
            print(f"[{index + 1:3d}/{len(songs)}] MISS    {band} - {song}")
            misses.append(
                {"index": index, "Band": band, "Song": song, "Year": row.get("Year", ""), "reason": "not found"}
            )
            continue

        out.write_text(found.lyrics, encoding="utf-8")
        print(f"[{index + 1:3d}/{len(songs)}] saved   {band} - {song}")

    if misses:
        MISSES_CSV.parent.mkdir(parents=True, exist_ok=True)
        with MISSES_CSV.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=["index", "Band", "Song", "Year", "reason"])
            writer.writeheader()
            writer.writerows(misses)
        print(f"\n{len(misses)} miss(es) logged in {MISSES_CSV}")


if __name__ == "__main__":
    main()