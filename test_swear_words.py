from count_swears import clean_lyrics
from swear_words import count_stems


def test_clean_lyrics_strips_sections_and_footer():
    text = ("[Chorus]\nFUCK! Embed\nShare URL\nCopyEmbedCopy\n"
            "You might also like\nnever counted")
    assert clean_lyrics(text) == "fuck"


def test_stem_groups_variants():
    counts = count_stems("fuck fucking fucked motherfucker bullshit shitty")
    assert counts["fuck"] == 4
    assert counts["shit"] == 2


def test_word_boundaries_ignore_similar_words():
    counts = count_stems("class whatever asshole jasper scathing")
    assert counts["ass"] == 1  # only asshole


def test_censored_variants():
    counts = count_stems("f*ck s**t a**hole")
    assert counts["fuck"] == 1
    assert counts["shit"] == 1
    assert counts["ass"] == 1