import base64
import json
import logging
import re

from openai import AsyncOpenAI

from config.defaults import SCAM_DETECTION_PROMPT, SCAM_SYSTEM_PROMPT
from models import ScamResult

logger = logging.getLogger(__name__)

_BASE_URL = "https://integrate.api.nvidia.com/v1"
_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"


def _extract_json(text: str) -> dict:
    """Strip think blocks + markdown fences, extract JSON from last line first."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```(?:json)?", "", text).replace("```", "")
    text = text.strip()
    logger.debug("NIM content response: %s", text[:1000])

    # Try last non-empty line first (model often puts JSON at end)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass

    # Fallback: greedy search for largest {…} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in response: {text!r}")
    return json.loads(match.group(0))


async def analyze_image(image_bytes: bytes, api_key: str) -> ScamResult:
    try:
        client = AsyncOpenAI(base_url=_BASE_URL, api_key=api_key)
        b64 = base64.b64encode(image_bytes).decode()

        stream = await client.chat.completions.create(
            model=_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SCAM_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                        {"type": "text", "text": SCAM_DETECTION_PROMPT},
                    ],
                },
            ],
            temperature=0.6,
            top_p=0.95,
            max_tokens=65536,
            extra_body={
                "chat_template_kwargs": {"enable_thinking": True},
                "reasoning_budget": 16384,
            },
            stream=True,
        )

        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                content_parts.append(delta.content)
            # collect reasoning as fallback in case content is empty
            if getattr(delta, "reasoning_content", None):
                reasoning_parts.append(delta.reasoning_content)

        raw = "".join(content_parts)
        if not raw.strip():
            # model put everything in the thinking chain — extract JSON from there
            logger.warning("content empty, falling back to reasoning_content")
            raw = "".join(reasoning_parts)
        data = _extract_json(raw)

        return ScamResult(
            is_scam=bool(data["is_scam"]),
            confidence=int(data["confidence"]),
            reason=str(data["reason"]),
        )

    except Exception as exc:
        logger.error("NVIDIA NIM analyzer error: %s", exc, exc_info=True)
        return ScamResult(is_scam=False, confidence=0, reason=f"analyzer error: {exc}")
