"""Likert-7 direction encoding + continuous dir_score with explanations."""
LIKERT_BINS = [-1.00,-0.66,-0.33,-0.10,0.10,0.33,0.66,1.00]

def to_likert(dir_score: float) -> int:
    # Maps [-1,1] → {-3..+3}
    for i in range(7):
        if LIKERT_BINS[i] <= dir_score < LIKERT_BINS[i+1]:
            return i - 3
    return 3 if dir_score >= 1.0 else -3

def encode_direction(evidence: dict) -> dict:
    """Compute dir_score_htf/ltf/micro and discrete likert labels.
    evidence includes structure_state, box_duration_bars, dist_to_poc_bps, equilibrium_pos, tv_strength, kama_rel, tokens, of metrics...
    """
    # TODO: implement scoring; placeholder returns neutral
    return {
        "dir_score_htf": 0.0, "dir_htf": 0,
        "dir_score_ltf": 0.0, "dir_ltf": 0,
        "dir_score_micro": 0.0, "dir_micro": 0,
        "explain": ["placeholder"]
    }
