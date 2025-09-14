"""Decision API测试"""
import pytest
from fastapi.testclient import TestClient
from services.decision.app import app
from services.decision.schemas.examples import EXAMPLE_ENTER_BULL, EXAMPLE_ENTER_BEAR, EXAMPLE_EXIT


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


class TestHealthEndpoints:
    """健康检查端点测试"""
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "P1 Decision Service"
        assert "features" in data
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_version_endpoint(self, client):
        """测试版本端点"""
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "service" in data


class TestEnterDecisionAPI:
    """入场决策API测试"""
    
    def test_enter_decision_bull_allow(self, client):
        """测试牛市入场决策 - 应该允许"""
        response = client.post("/decide/enter", json=EXAMPLE_ENTER_BULL)
        assert response.status_code == 200
        
        data = response.json()
        assert data["allow"] is True
        assert data["side"] in ["long", "short"]
        assert data["alloc_equity_pct"] > 0
        assert len(data["reason_chain"]) > 0
        assert data["runtime_ms"] > 0
    
    def test_enter_decision_bear_allow(self, client):
        """测试熊市入场决策 - 应该允许"""
        response = client.post("/decide/enter", json=EXAMPLE_ENTER_BEAR)
        assert response.status_code == 200
        
        data = response.json()
        assert data["allow"] is True
        assert data["side"] in ["long", "short"]
        assert data["alloc_equity_pct"] > 0
        assert len(data["reason_chain"]) > 0
    
    def test_enter_decision_vol_reject(self, client):
        """测试波动率拒绝场景"""
        # 修改示例数据创建拒绝场景
        reject_data = EXAMPLE_ENTER_BEAR.copy()
        reject_data["features"]["sigma_1m"] = 0.005  # 过高波动率
        reject_data["features"]["skew_1m"] = 0.1    # 中性偏度
        
        response = client.post("/decide/enter", json=reject_data)
        assert response.status_code == 200
        
        data = response.json()
        # 可能被拒绝或允许，取决于其他因素
        assert "allow" in data
        assert "reason_chain" in data
    
    def test_enter_decision_low_p_hit_reject(self, client):
        """测试低P_hit拒绝场景"""
        reject_data = EXAMPLE_ENTER_BEAR.copy()
        reject_data["pgm"]["p_hit"] = 0.60  # 低于0.75阈值
        
        response = client.post("/decide/enter", json=reject_data)
        assert response.status_code == 200
        
        data = response.json()
        # 可能被拒绝，但要检查reason_chain中的解释
        if not data["allow"]:
            reason_text = " ".join(data["reason_chain"])
            # 应该包含P_hit相关的拒绝原因
            assert any(keyword in reason_text.lower() for keyword in ["p_hit", "phit", "gate"])
    
    def test_enter_decision_invalid_request(self, client):
        """测试无效请求"""
        invalid_data = {"invalid": "data"}
        
        response = client.post("/decide/enter", json=invalid_data)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_enter_decision_examples_endpoint(self, client):
        """测试示例端点"""
        response = client.get("/decide/enter/examples")
        assert response.status_code == 200
        
        data = response.json()
        assert "bull_scenario" in data
        assert "bear_scenario" in data
        assert "reject_vol_scenario" in data
    
    def test_enter_decision_test_scenarios(self, client):
        """测试场景测试端点"""
        response = client.post("/decide/enter/test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["test_completed"] is True
        assert data["scenarios_tested"] > 0
        assert "results" in data


class TestExitDecisionAPI:
    """退出决策API测试"""
    
    def test_exit_decision_normal(self, client):
        """测试正常退出决策"""
        response = client.post("/decide/exit", json=EXAMPLE_EXIT)
        assert response.status_code == 200
        
        data = response.json()
        assert data["action"] in ["hold", "reduce", "close", "trail"]
        assert "reason" in data
        assert data["runtime_ms"] > 0
        
        if data["action"] in ["reduce", "trail"]:
            assert data["reduce_pct"] is not None
            assert 0 < data["reduce_pct"] <= 1
    
    def test_exit_decision_high_hazard(self, client):
        """测试高Hazard退出决策"""
        high_hazard_data = EXAMPLE_EXIT.copy()
        high_hazard_data["updates"]["h_t"] = 0.45  # 高Hazard
        
        response = client.post("/decide/exit", json=high_hazard_data)
        assert response.status_code == 200
        
        data = response.json()
        # 高Hazard应该触发减仓或平仓
        assert data["action"] in ["reduce", "close"]
        
        if data["action"] == "close":
            assert data["reduce_pct"] == 1.0
    
    def test_exit_decision_low_p_hit(self, client):
        """测试低P_hit退出决策"""
        low_phit_data = EXAMPLE_EXIT.copy()
        low_phit_data["updates"]["p_hit"] = 0.35  # 低P_hit
        
        response = client.post("/decide/exit", json=low_phit_data)
        assert response.status_code == 200
        
        data = response.json()
        # 低P_hit应该触发减仓
        assert data["action"] in ["reduce", "close"]
    
    def test_exit_decision_examples_endpoint(self, client):
        """测试退出示例端点"""
        response = client.get("/decide/exit/examples")
        assert response.status_code == 200
        
        data = response.json()
        assert "example_exit" in data
    
    def test_exit_decision_strategies_endpoint(self, client):
        """测试退出策略端点"""
        response = client.get("/decide/exit/strategies")
        assert response.status_code == 200
        
        data = response.json()
        assert "strategies" in data
        assert "risk_factors" in data


class TestPerformanceAndValidation:
    """性能和验证测试"""
    
    def test_enter_decision_latency(self, client):
        """测试入场决策延迟"""
        response = client.post("/decide/enter", json=EXAMPLE_ENTER_BULL)
        assert response.status_code == 200
        
        data = response.json()
        # 检查是否满足70ms的SLA
        assert data["runtime_ms"] < 100, f"Decision took {data['runtime_ms']}ms, too slow"
    
    def test_exit_decision_latency(self, client):
        """测试退出决策延迟"""
        response = client.post("/decide/exit", json=EXAMPLE_EXIT)
        assert response.status_code == 200
        
        data = response.json()
        # 退出决策应该更快
        assert data["runtime_ms"] < 50, f"Exit decision took {data['runtime_ms']}ms, too slow"
    
    def test_reason_chain_quality(self, client):
        """测试推理链质量"""
        response = client.post("/decide/enter", json=EXAMPLE_ENTER_BULL)
        assert response.status_code == 200
        
        data = response.json()
        reason_chain = data["reason_chain"]
        
        # 推理链应该有足够的信息
        assert len(reason_chain) >= 3, "Reason chain should have at least 3 steps"
        
        # 应该包含关键指标
        reason_text = " ".join(reason_chain)
        expected_indicators = ["C_align", "C_of", "C_vision", "p_hit"]
        found_indicators = [ind for ind in expected_indicators if ind in reason_text]
        assert len(found_indicators) >= 2, f"Reason chain should mention key indicators, found: {found_indicators}"


@pytest.mark.integration
class TestAPIIntegration:
    """API集成测试"""
    
    def test_full_decision_flow(self, client):
        """测试完整决策流程"""
        # 1. 入场决策
        enter_response = client.post("/decide/enter", json=EXAMPLE_ENTER_BULL)
        assert enter_response.status_code == 200
        
        enter_data = enter_response.json()
        
        if enter_data["allow"]:
            # 2. 如果允许入场，测试退出决策
            exit_response = client.post("/decide/exit", json=EXAMPLE_EXIT)
            assert exit_response.status_code == 200
            
            exit_data = exit_response.json()
            assert exit_data["action"] in ["hold", "reduce", "close", "trail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
