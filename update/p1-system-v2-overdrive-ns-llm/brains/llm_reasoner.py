"""LLM Reasoner: from numeric features → human-style reasoning, confidence, meta-tag.
LLM must obey schema and latency budget; used only on borderline cases.
"""
def reason(features: dict) -> dict:
    # TODO: integrate FinGPT/local LLM
    return {"rationale": "placeholder rationale", "c_llm": 0.6, "meta_tag": "box-trap"}
