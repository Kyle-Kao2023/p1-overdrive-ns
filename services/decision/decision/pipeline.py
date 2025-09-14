"""Main decision pipeline orchestrating DataHub → Features → Brains → Gates → Decision."""
from .gates import run_gates
from ..brains.ctfg import CTFG
from ..brains.xlstm import infer_sequence
from ..brains.llm_reasoner import reason

def decide(snapshot: dict):
    # 1) Build sequences (placeholder)
    token_seq, of_seq, tv_seq = [], [], []
    tempo_y = infer_sequence(token_seq, of_seq, tv_seq, meta={"tf": snapshot.get("tf")})
    ctx = CTFG().infer(snapshot, tempo_y)
    ok, reasons = run_gates(snapshot, ctx)
    if not ok:
        return {"allow": False, "reasons": reasons}
    # borderline check (placeholder)
    borderline = 0.72 <= ctx["p_hit"] <= 0.78
    used_llm = False
    if borderline:
        arb = reason(snapshot)
        used_llm = True
    action = "long" if ctx["long_score"] >= ctx["short_score"] else "short"
    return {"allow": True, "action": action, "context": ctx, "used_llm": used_llm}
