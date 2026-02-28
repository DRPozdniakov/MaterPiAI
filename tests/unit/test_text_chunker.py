"""Tests for the pure chunk_text() function."""

from app.services.tts import chunk_text


class TestChunkText:
    def test_empty_string(self):
        assert chunk_text("", max_chars=100) == []

    def test_whitespace_only(self):
        assert chunk_text("   ", max_chars=100) == []

    def test_single_sentence_fits(self):
        assert chunk_text("Hello world.", max_chars=100) == ["Hello world."]

    def test_two_sentences_fit_in_one_chunk(self):
        result = chunk_text("Hello. World.", max_chars=100)
        assert result == ["Hello. World."]

    def test_two_sentences_split_when_too_long(self):
        result = chunk_text("Hello. World.", max_chars=10)
        assert result == ["Hello.", "World."]

    def test_greedy_packing(self):
        text = "A. B. C. D."
        result = chunk_text(text, max_chars=7)
        # "A. B." = 5 chars ≤ 7, then "C." + " D." = "C. D." = 5 chars ≤ 7
        assert result == ["A. B.", "C. D."]

    def test_long_sentence_not_split_mid_sentence(self):
        # A single sentence longer than max_chars stays as one chunk
        long = "A" * 200 + "."
        result = chunk_text(long, max_chars=100)
        assert result == [long]

    def test_exclamation_marks(self):
        result = chunk_text("Stop! Go! Now!", max_chars=10)
        assert result == ["Stop!", "Go! Now!"]

    def test_question_marks(self):
        result = chunk_text("Why? How? What?", max_chars=10)
        assert result == ["Why? How?", "What?"]

    def test_unicode_punctuation(self):
        result = chunk_text("日本語。中国語。韓国語。", max_chars=10)
        assert result == ["日本語。", "中国語。韓国語。"]

    def test_mixed_punctuation(self):
        result = chunk_text("Hello! How are you? Fine.", max_chars=25)
        assert result == ["Hello! How are you? Fine."]

    def test_preserves_text_content(self):
        text = "First sentence. Second sentence. Third sentence."
        result = chunk_text(text, max_chars=1000)
        assert " ".join(result) == text

    def test_default_max_chars_is_large(self):
        # With default (4500), moderate text should be one chunk
        text = "Hello. " * 100  # ~700 chars
        result = chunk_text(text.strip())
        assert len(result) == 1
