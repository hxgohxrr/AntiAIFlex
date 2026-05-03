import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from models import ScamResult
from services.analyzer import _extract_json, analyze_image


def _make_raw(is_scam: bool, confidence: int, reason: str) -> str:
    return json.dumps({"is_scam": is_scam, "confidence": confidence, "reason": reason})


def _make_stream(content: str):
    """Async generator simulating OpenAI streaming chunks."""
    chunk = MagicMock()
    chunk.choices = [MagicMock()]
    chunk.choices[0].delta = MagicMock()
    chunk.choices[0].delta.content = content
    chunk.choices[0].delta.reasoning_content = None

    async def _gen():
        yield chunk

    return _gen()


# --- _extract_json unit tests ---

def test_extract_json_plain():
    raw = '{"is_scam": true, "confidence": 90, "reason": "fake"}'
    data = _extract_json(raw)
    assert data["is_scam"] is True
    assert data["confidence"] == 90


def test_extract_json_strips_think_block():
    raw = '<think>lots of reasoning here</think>\n{"is_scam": false, "confidence": 5, "reason": "clean"}'
    data = _extract_json(raw)
    assert data["is_scam"] is False
    assert data["confidence"] == 5


def test_extract_json_raises_on_no_json():
    with pytest.raises(ValueError, match="No JSON object found"):
        _extract_json("just some text with no braces")


def test_extract_json_strips_markdown_fence():
    raw = "```json\n{\"is_scam\": true, \"confidence\": 85, \"reason\": \"scam\"}\n```"
    data = _extract_json(raw)
    assert data["is_scam"] is True
    assert data["confidence"] == 85


def test_extract_json_last_line_priority():
    raw = "Analysis complete.\nI see a scam.\n{\"is_scam\": true, \"confidence\": 92, \"reason\": \"casino scam\"}"
    data = _extract_json(raw)
    assert data["confidence"] == 92


# --- analyze_image integration tests ---

async def test_analyze_image_detects_scam():
    raw = _make_raw(True, 92, "fake crypto giveaway")

    with patch("services.analyzer.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock(return_value=_make_stream(raw))

        result = await analyze_image(b"fake_image_bytes", api_key="test_key")

    assert isinstance(result, ScamResult)
    assert result.is_scam is True
    assert result.confidence == 92
    assert result.reason == "fake crypto giveaway"


async def test_analyze_image_clean_image():
    raw = _make_raw(False, 10, "normal image")

    with patch("services.analyzer.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock(return_value=_make_stream(raw))

        result = await analyze_image(b"fake_image_bytes", api_key="test_key")

    assert result.is_scam is False
    assert result.confidence == 10


async def test_analyze_image_api_error_returns_safe_default():
    with patch("services.analyzer.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock(side_effect=Exception("API error"))

        result = await analyze_image(b"fake_image_bytes", api_key="test_key")

    assert result.is_scam is False
    assert result.confidence == 0
    assert "error" in result.reason.lower()


async def test_analyze_image_think_block_stripped():
    raw = "<think>hmm this looks suspicious</think>\n" + _make_raw(True, 88, "celebrity scam")

    with patch("services.analyzer.AsyncOpenAI") as MockClient:
        instance = MockClient.return_value
        instance.chat = MagicMock()
        instance.chat.completions = MagicMock()
        instance.chat.completions.create = AsyncMock(return_value=_make_stream(raw))

        result = await analyze_image(b"fake_image_bytes", api_key="test_key")

    assert result.is_scam is True
    assert result.confidence == 88
