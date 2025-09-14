#!/usr/bin/env python3
"""
LLM Reasoner 邊界情況範例

演示如何在邊界情況下觸發 LLM 推理，以及如何處理推理結果。
"""

import requests
import json
from typing import Dict, Any

# 配置
API_BASE = "http://localhost:8000/v2"
TIMEOUT = 5.0

def create_borderline_request() -> Dict[str, Any]:
    """創建會觸發 LLM 推理的邊界情況請求"""
    return {
        "symbol": "ETHUSDT",
        "version": "2.0",
        "side_hint": "short",
        "ts": "2025-09-15T14:30:00Z",
        "tf": "15m",
        "features": {
            # 標準技術指標
            "sigma_1m": 0.0018,
            "skew_1m": -0.72,
            "Z_4H": -0.9,
            "Z_1H": -0.7,
            "Z_15m": -0.6,

            # 一致性指標 (略低，邊界情況)
            "C_align": 0.82,
            "C_of": 0.78,
            "C_vision": 0.76,

            # v2: Likert-7 方向編碼
            "direction": {
                "dir_score_htf": -0.75,
                "dir_htf": -2,           # 中度看空
                "dir_score_ltf": -0.65,
                "dir_ltf": -2,
                "dir_score_micro": -0.55,
                "dir_micro": -1          # 輕度看空
            },

            # v2: FinGPT 新聞分析
            "news": {
                "sentiment_score": -0.3,
                "event_risk": 0.15,
                "headline_summary": "Fed signals potential rate hike, crypto markets cautious"
            },

            # 衝突信號 (會觸發 LLM)
            "pine_match": True,
            "of_divergence": True,      # OrderFlow 背離
            "vision_conflict": True     # 視覺模式衝突
        },
        "pgm": {
            "p_hit": 0.74,              # 邊界值！會觸發 LLM
            "mae_q999": 0.0058,
            "slip_q95": 0.0004,
            "t_hit_q50_bars": 6,

            # v2: 保形預測置信區間
            "conformal_ci": {
                "p_hit_lower": 0.71,
                "p_hit_upper": 0.77,
                "coverage_prob": 0.95
            }
        }
    }

def analyze_llm_response(decision: Dict[str, Any]) -> None:
    """分析 LLM 推理結果"""
    print("=" * 60)
    print("🤖 LLM 推理分析")
    print("=" * 60)

    if "llm_reasoning" not in decision:
        print("❌ LLM 推理未觸發 (可能不在邊界範圍)")
        return

    llm = decision["llm_reasoning"]

    print(f"✅ LLM 推理已觸發")
    print(f"📝 Rationale: {llm['rationale']}")
    print(f"🏷️  Meta Tag: {llm['meta_tag']}")
    print(f"📊 LLM 置信度: {llm['c_llm']:.2f}")
    print(f"⏱️  推理耗時: {llm.get('reasoning_time_ms', 'N/A')}ms")
    print(f"🎯 觸發原因: {llm.get('triggered_by', 'borderline_p_hit')}")

    # 分析推理質量
    confidence = llm['c_llm']
    if confidence > 0.8:
        print("🟢 高質量推理 - 可以信賴")
    elif confidence > 0.6:
        print("🟡 中等質量推理 - 需要謹慎")
    else:
        print("🔴 低質量推理 - 建議回退到純數值決策")

def demonstrate_llm_reasoning():
    """演示 LLM 推理功能"""
    print("🚀 P1-System v2 LLM Reasoner 演示")
    print("=" * 60)

    # 創建邊界情況請求
    request = create_borderline_request()

    print("📤 發送邊界情況請求...")
    print(f"   p_hit: {request['pgm']['p_hit']} (邊界值)")
    print(f"   衝突信號: {request['features']['of_divergence']}")

    try:
        # 調用 v2 API
        response = requests.post(
            f"{API_BASE}/decide/enter",
            json=request,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        decision = response.json()

        # 基本決策結果
        print(f"\n📋 決策結果:")
        print(f"   允許交易: {'✅' if decision['allow'] else '❌'}")
        print(f"   建議方向: {decision.get('side', 'N/A')}")
        print(f"   分配比例: {decision.get('alloc_equity_pct', 0):.1%}")
        print(f"   推理鏈: {decision.get('reason_chain', 'N/A')}")

        # 分析 LLM 推理
        analyze_llm_response(decision)

        # 性能指標
        if "metrics" in decision:
            metrics = decision["metrics"]
            print(f"\n⚡ 性能指標:")
            print(f"   總延遲: {metrics.get('total_latency_ms', 'N/A')}ms")
            print(f"   LLM 延遲: {metrics.get('llm_latency_ms', 'N/A')}ms")
            print(f"   Gate 檢查: {metrics.get('gates_latency_ms', 'N/A')}ms")

    except requests.exceptions.RequestException as e:
        print(f"❌ API 請求失敗: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ 響應解析失敗: {e}")

def test_non_borderline_case():
    """測試非邊界情況 (不應觸發 LLM)"""
    print("\n🧪 測試非邊界情況 (不應觸發 LLM)")
    print("=" * 60)

    request = create_borderline_request()
    request["pgm"]["p_hit"] = 0.85  # 非邊界值

    try:
        response = requests.post(
            f"{API_BASE}/decide/enter",
            json=request,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        decision = response.json()

        if "llm_reasoning" in decision:
            print("⚠️  非邊界情況也觸發了 LLM (可能配置有誤)")
        else:
            print("✅ 非邊界情況正確跳過 LLM 推理")

    except requests.exceptions.RequestException as e:
        print(f"❌ 非邊界測試失敗: {e}")

if __name__ == "__main__":
    # 主演示
    demonstrate_llm_reasoning()

    # 對比測試
    test_non_borderline_case()

    print("\n" + "=" * 60)
    print("✨ LLM Reasoner 演示完成")
    print("💡 提示: 檢查 logs/ 目錄中的詳細推理日誌")
    print("📚 更多範例: examples/llm_reasoning/")