from config.defaults import (
    DEFAULT_THRESHOLD,
    DEFAULT_SCAN_MODE,
    MAX_IMAGE_SIZE_BYTES,
    SCAM_DETECTION_PROMPT,
)


def test_default_threshold_is_85():
    assert DEFAULT_THRESHOLD == 85


def test_default_scan_mode():
    assert DEFAULT_SCAN_MODE == "bro_only"


def test_max_image_size():
    assert MAX_IMAGE_SIZE_BYTES == 10 * 1024 * 1024


def test_prompt_contains_json_instruction():
    assert "is_scam" in SCAM_DETECTION_PROMPT
    assert "confidence" in SCAM_DETECTION_PROMPT
    assert "reason" in SCAM_DETECTION_PROMPT
