"""TradingView indicator ingestion.
TODO: Implement webhook/REST polling to collect RSI, TSI, KAMA, OBV, BB, Regression channel, Pivot.
Outputs standardized dict conforming to features/schema.py.
"""
def fetch_tv_snapshot(symbol: str, tf: str):
    # TODO: Implement real ingestion
    return {"symbol": symbol, "tf": tf, "tv": {"rsi": None, "tsi": None}, "ts": None}
