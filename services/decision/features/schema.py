"""Unified FeatureHub schema description (for validation)."""
FEATURE_SCHEMA = {
    "ts": "ISO8601",
    "symbol": "str",
    "tf": "str",
    "tv": dict,
    "structure": dict,
    "location": dict,
    "vision_tokens": list,
    "of": dict,
    "vol": dict,
    "news": dict,
    "direction": dict
}
