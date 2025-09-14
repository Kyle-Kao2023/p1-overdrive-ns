#!/usr/bin/env python3
"""种子示例数据脚本"""
import requests
import json
from datetime import datetime

# 服务URLs
DECISION_URL = "http://localhost:8000"
FEATUREHUB_URL = "http://localhost:8010"
VISION_URL = "http://localhost:8020"

def test_decision_service():
    """测试Decision Service"""
    print("🎯 Testing Decision Service...")
    
    # 测试健康检查
    try:
        response = requests.get(f"{DECISION_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Decision Service health check passed")
        else:
            print(f"❌ Decision Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Decision Service not reachable: {e}")
        return False
    
    # 测试入场决策示例
    try:
        response = requests.get(f"{DECISION_URL}/decide/enter/examples", timeout=5)
        if response.status_code == 200:
            examples = response.json()
            print(f"✅ Retrieved {len(examples)} enter decision examples")
            
            # 测试牛市场景
            bull_example = examples["bull_scenario"]
            response = requests.post(f"{DECISION_URL}/decide/enter", json=bull_example, timeout=10)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Bull scenario decision: {'ALLOW' if result['allow'] else 'DENY'} {result.get('side', '')} {result.get('alloc_equity_pct', 0):.1%}")
            else:
                print(f"❌ Bull scenario test failed: {response.status_code}")
        else:
            print(f"❌ Failed to get examples: {response.status_code}")
    except Exception as e:
        print(f"❌ Enter decision test failed: {e}")
    
    return True

def test_featurehub_service():
    """测试FeatureHub Service"""
    print("\n🔄 Testing FeatureHub Service...")
    
    try:
        response = requests.get(f"{FEATUREHUB_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ FeatureHub health check passed")
        else:
            print(f"❌ FeatureHub health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FeatureHub not reachable: {e}")
        return False
    
    # 测试市场快照生成
    try:
        response = requests.get(f"{FEATUREHUB_URL}/snapshot", params={"symbol": "ETHUSDT"}, timeout=5)
        if response.status_code == 200:
            snapshot = response.json()
            print(f"✅ Generated market snapshot: {snapshot['symbol']} @ {snapshot['mark_price']:.2f}")
        else:
            print(f"❌ Snapshot generation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Snapshot test failed: {e}")
    
    return True

def test_vision_service():
    """测试Vision Service"""
    print("\n👁️  Testing Vision Service...")
    
    try:
        response = requests.get(f"{VISION_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Vision Service health check passed")
        else:
            print(f"❌ Vision Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Vision Service not reachable: {e}")
        return False
    
    # 测试检测端点
    try:
        test_request = {
            "image_ref": "test_chart_001",
            "image_url": "http://example.com/chart.png"
        }
        response = requests.post(f"{VISION_URL}/detect", json=test_request, timeout=5)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Pattern detection: {len(result['tokens'])} patterns, C_vision={result['c_vision']:.2f}")
        else:
            print(f"❌ Pattern detection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Vision detection test failed: {e}")
    
    return True

def send_sample_data():
    """发送示例数据"""
    print("\n📊 Sending sample data...")
    
    # 发送Pine webhook示例
    try:
        pine_data = {
            "symbol": "ETHUSDT",
            "timeframe": "15m",
            "timestamp": datetime.utcnow().isoformat(),
            "signal": "SELL",
            "price": 2415.3,
            "indicators": {
                "rsi": 75.2,
                "macd": -0.5,
                "bb_position": 0.85
            },
            "confidence": 0.78
        }
        
        response = requests.post(f"{FEATUREHUB_URL}/tv/webhook", json=pine_data, timeout=5)
        if response.status_code == 200:
            print("✅ Pine webhook data sent successfully")
        else:
            print(f"❌ Pine webhook failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Pine webhook test failed: {e}")
    
    # 发送Vision tokens示例
    try:
        vision_data = {
            "image_ref": "chart_20250914_102500",
            "timestamp": datetime.utcnow().isoformat(),
            "tokens": {
                "bear_engulfing": 0.82,
                "long_upper_wick": 0.74,
                "support_break": 0.68
            },
            "confidence_overall": 0.79
        }
        
        response = requests.post(f"{FEATUREHUB_URL}/vision/tokens", json=vision_data, timeout=5)
        if response.status_code == 200:
            print("✅ Vision tokens sent successfully")
        else:
            print(f"❌ Vision tokens failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Vision tokens test failed: {e}")

def run_integration_test():
    """运行集成测试"""
    print("\n🔄 Running integration test...")
    
    try:
        # 1. 获取市场快照
        snapshot_response = requests.get(f"{FEATUREHUB_URL}/snapshot", params={"symbol": "BTCUSDT"}, timeout=5)
        if snapshot_response.status_code != 200:
            print("❌ Failed to get market snapshot for integration test")
            return
        
        snapshot = snapshot_response.json()
        
        # 2. 构建决策请求
        decision_request = {
            "symbol": "BTCUSDT",
            "side_hint": "long",
            "ts": datetime.utcnow().isoformat(),
            "tf": "15m",
            "features": {
                "sigma_1m": snapshot["sigma_1m"],
                "skew_1m": snapshot["skew_1m"],
                "Z_4H": snapshot["z_scores"]["4H"],
                "Z_1H": snapshot["z_scores"]["1H"],
                "Z_15m": snapshot["z_scores"]["15m"],
                "C_align": snapshot["c_align"],
                "C_of": snapshot["c_of"],
                "C_vision": snapshot["c_vision"],
                "pine_match": True,
                "onchain": snapshot["onchain"],
                "OF": snapshot["orderflow"],
                "vision_tokens": {"tokens": {}},
                "market": {
                    "mark": snapshot["mark_price"],
                    "liq_price": snapshot["mark_price"] * 0.9,
                    "spread_bp": snapshot["spread_bp"],
                    "depth_px": snapshot["depth_px"]
                }
            },
            "pgm": {
                "p_hit": 0.78,
                "mae_q999": 0.006,
                "slip_q95": 0.0005,
                "t_hit_q50_bars": 6,
                "factors": []
            }
        }
        
        # 3. 调用决策API
        decision_response = requests.post(f"{DECISION_URL}/decide/enter", json=decision_request, timeout=10)
        if decision_response.status_code == 200:
            result = decision_response.json()
            print(f"✅ Integration test successful!")
            print(f"   Decision: {'ALLOW' if result['allow'] else 'DENY'}")
            print(f"   Side: {result.get('side', 'N/A')}")
            print(f"   Allocation: {result.get('alloc_equity_pct', 0):.1%}")
            print(f"   Runtime: {result['runtime_ms']}ms")
            print(f"   Reason chain: {len(result['reason_chain'])} steps")
        else:
            print(f"❌ Integration test failed: {decision_response.status_code}")
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")

def main():
    """主函数"""
    print("🌟 P1 Trading Builder - Seed Examples & Testing")
    print("=" * 50)
    
    # 测试各个服务
    decision_ok = test_decision_service()
    featurehub_ok = test_featurehub_service()
    vision_ok = test_vision_service()
    
    if decision_ok and featurehub_ok:
        # 发送示例数据
        send_sample_data()
        
        # 运行集成测试
        run_integration_test()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")
    
    if decision_ok and featurehub_ok and vision_ok:
        print("🎉 All services are running correctly!")
        print("\n🔗 Try these URLs:")
        print(f"   Decision API: {DECISION_URL}/docs")
        print(f"   FeatureHub:   {FEATUREHUB_URL}/health")
        print(f"   Vision:       {VISION_URL}/health")
    else:
        print("⚠️  Some services may not be running properly.")
        print("   Make sure to start them with: ./scripts/run_dev.sh")

if __name__ == "__main__":
    main()
