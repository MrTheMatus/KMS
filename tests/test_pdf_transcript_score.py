"""Unit tests for PDF transcript scoring (no conversion)."""

from __future__ import annotations

from kms.app.pdf_converter import score_transcript_markdown


def test_score_empty_is_very_low() -> None:
    assert score_transcript_markdown("") < -1e8
    assert score_transcript_markdown("   \n\t\n") < -1e8


def test_score_prefers_dialogue_like_content() -> None:
    page_boiler = "## Page 1\n" + "x\n" * 15
    dialogue = "\n".join(
        [
            "User: This is a substantive message about debugging and stack traces.",
            "Assistant: Consider structured logging and correlation ids for threads.",
        ]
        * 6
    )
    assert score_transcript_markdown(dialogue) > score_transcript_markdown(page_boiler)


def test_score_polish_speaker_prefixes_count() -> None:
    pl = "Ty: dłuższa wypowiedź użytkownika o kodzie produkcyjnym\n" * 4
    noise = "lorem ipsum dolor sit amet " * 8
    assert score_transcript_markdown(pl) > score_transcript_markdown(noise)
