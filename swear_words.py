"""Curated swear-word stems and variants for lyric analysis."""

import re

SWEAR_STEMS = {
    "fuck": [
        "fuck", "fucks", "fucked", "fucking",
        "fuckin", "fucker", "fuckers", "fucka", "fuckas",
        "motherfucker", "motherfuckers", "motherfucking",
        "motherfuckin", "f*ck", "f**k", "fck", "fukk",
    ],
    "shit": [
        "shit", "shits", "shitted", "shitting", "shitty",
        "bullshit", "bullshitting", "shithead", "shitheads",
        "s*it", "s**t", "sh*t", "sht",
    ],
    "bitch": [
        "bitch", "bitches", "bitchy", "bitching", "bitchin",
        "b*itch",
    ],
    "ass": [
        "ass", "asses", "arse", "asshole", "assholes",
        "asshat", "asshats", "jackass", "dumbass", "badass",
        "a**hole",
    ],
    "damn": [
        "damn", "damned", "damnit", "dammit", "goddamn",
        "goddamnit", "goddammit", "goddamned",
    ],
    "hell": [
        "hell", "hells", "hellhole", "hellfire",
    ],
    "cunt": [
        "cunt", "cunts", "c*nt",
    ],
    "dick": [
        "dick", "dicks", "dickhead", "dickheads",
        "dickless", "d*ck",
    ],
    "pussy": [
        "pussy", "pussies", "p*ssy",
    ],
    "cock": [
        "cock", "cocks", "cocksucker", "cocksuckers",
        "cockhead", "c*ck",
    ],
    "tits": [
        "tits", "titty", "titties", "boobs", "boobies",
    ],
    "whore": [
        "whore", "whores", "w*ore",
    ],
    "slut": [
        "slut", "sluts", "slutty", "s*ut",
    ],
    "bastard": [
        "bastard", "bastards", "b*stard",
    ],
    "piss": [
        "piss", "pissing", "pissed", "pisses",
        "p*ss", "p*ssed",
    ],
}

STEM_ORDER = list(SWEAR_STEMS)

_STEM_PATTERNS = {
    stem: re.compile(
        r"\b(?:" + "|".join(re.escape(v) for v in variants) + r")\b",
        re.IGNORECASE,
    )
    for stem, variants in SWEAR_STEMS.items()
}


def count_stems(text: str) -> dict[str, int]:
    """Return {stem: count} of swear stems found in ``text``."""
    return {
        stem: len(pattern.findall(text))
        for stem, pattern in _STEM_PATTERNS.items()
    }