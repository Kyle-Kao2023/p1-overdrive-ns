"""Hazard和MPC测试"""
import pytest
import numpy as np
from services.decision.models.bocpd import SimplifiedBOCPD, estimate_hazard_from_returns, generate_synthetic_regime_shift
from services.decision.execution.mpc_exit import decide_exit, simulate_exit_scenarios
from services.decision.schemas.features import ExitRequest, ExitUpdates
from services.decision.schemas.base import Position


class TestHazardDetection:
    """Hazard检测测试"""
    
    def test_bocpd_initialization(self):
        """测试BOCPD初始化"""
        bocpd = SimplifiedBOCPD(window_size=20, sensitivity=2.0)
        assert bocpd.window_size == 20
        assert bocpd.sensitivity == 2.0
        assert len(bocpd.history) == 0
    
    def test_bocpd_update_normal_series(self):
        """测试正常序列的hazard率"""
        bocpd = SimplifiedBOCPD(window_size=10)
        
        # 生成稳定的正态分布序列
        np.random.seed(42)
        stable_series = np.random.normal(0, 0.01, 30)
        
        hazard_rates = []
        for value in stable_series:
            hazard = bocpd.update(value)
            hazard_rates.append(hazard)
        
        # 稳定序列的hazard率应该较低
        final_hazard = hazard_rates[-1]
        assert 0 <= final_hazard <= 1, f"Hazard rate {final_hazard} should be between 0 and 1"
        assert final_hazard < 0.5, f"Stable series should have low hazard rate, got {final_hazard}"
    
    def test_bocpd_regime_shift_detection(self):
        """测试regime shift检测"""
        bocpd = SimplifiedBOCPD(window_size=15, sensitivity=3.0)
        
        # 生成包含regime shift的序列
        regime_shift_series = generate_synthetic_regime_shift()
        
        hazard_rates = []
        for value in regime_shift_series:
            hazard = bocpd.update(value)
            hazard_rates.append(hazard)
        
        # 在regime shift后，hazard率应该上升
        early_hazard = np.mean(hazard_rates[:20])  # 第一个regime
        late_hazard = np.mean(hazard_rates[-10:])   # 第二个regime转换后
        
        assert late_hazard > early_hazard, f"Hazard should increase after regime shift: {early_hazard:.3f} -> {late_hazard:.3f}"
    
    def test_estimate_hazard_from_returns(self):
        """测试从收益率估计hazard"""
        # 测试空序列
        hazard_empty = estimate_hazard_from_returns([])
        assert hazard_empty == 0.0
        
        # 测试正常序列
        np.random.seed(42)
        normal_returns = np.random.normal(0, 0.01, 50).tolist()
        hazard_normal = estimate_hazard_from_returns(normal_returns)
        
        assert 0 <= hazard_normal <= 1
        
        # 测试regime shift序列
        shift_returns = generate_synthetic_regime_shift()
        hazard_shift = estimate_hazard_from_returns(shift_returns)
        
        assert hazard_shift > hazard_normal, "Regime shift series should have higher hazard"


class TestMPCExit:
    """MPC退出策略测试"""
    
    @pytest.fixture
    def base_position(self):
        """基础持仓数据"""
        return Position(
            avg_entry=2415.0,
            side="short",
            qty=120.0,
            upl_pct=0.42
        )
    
    @pytest.fixture
    def normal_updates(self):
        """正常更新数据"""
        return ExitUpdates(
            p_hit=0.70,
            mae_q90=0.003,
            t_hit_q50_bars=6,
            h_t=0.15,
            dCVD=-0.5,
            replenish=0.65
        )
    
    def test_mpc_exit_hold_decision(self, base_position, normal_updates):
        """测试持有决策"""
        request = ExitRequest(position=base_position, updates=normal_updates)
        response = decide_exit(request)
        
        assert response.action == "hold"
        assert response.reduce_pct is None
        assert len(response.reason) > 0
        assert response.runtime_ms > 0
    
    def test_mpc_exit_high_hazard_reduce(self, base_position, normal_updates):
        """测试高hazard触发减仓"""
        normal_updates.h_t = 0.35  # 超过默认阈值0.30
        
        request = ExitRequest(position=base_position, updates=normal_updates)
        response = decide_exit(request)
        
        assert response.action in ["reduce", "close"]
        if response.action == "reduce":
            assert 0 < response.reduce_pct <= 1
        
        # 原因中应该包含hazard
        reason_text = " ".join(response.reason)
        assert "hazard" in reason_text.lower()
    
    def test_mpc_exit_low_p_hit_reduce(self, base_position, normal_updates):
        """测试低p_hit触发减仓"""
        normal_updates.p_hit = 0.45  # 低于默认floor 0.50
        
        request = ExitRequest(position=base_position, updates=normal_updates)
        response = decide_exit(request)
        
        assert response.action in ["reduce", "close"]
        
        # 原因中应该包含p_hit
        reason_text = " ".join(response.reason)
        assert "p_hit" in reason_text.lower()
    
    def test_mpc_exit_critical_hazard_close(self, base_position, normal_updates):
        """测试极端hazard触发平仓"""
        normal_updates.h_t = 0.50  # 极高hazard
        
        request = ExitRequest(position=base_position, updates=normal_updates)
        response = decide_exit(request)
        
        assert response.action == "close"
        assert response.reduce_pct == 1.0
        
        # 原因中应该包含critical
        reason_text = " ".join(response.reason)
        assert "critical" in reason_text.lower()
    
    def test_mpc_exit_orderflow_flip(self, base_position, normal_updates):
        """测试订单流反转触发减仓"""
        # 空头持仓，dCVD变正是不利的
        normal_updates.dCVD = 2.0  # 强烈看涨信号，对空头不利
        
        request = ExitRequest(position=base_position, updates=normal_updates)
        response = decide_exit(request)
        
        assert response.action in ["reduce", "close"]
        
        # 原因中应该包含orderflow flip
        reason_text = " ".join(response.reason)
        assert "of_flip" in reason_text.lower() or "dcvd" in reason_text.lower()
    
    def test_mpc_exit_timeout_risk(self, base_position, normal_updates):
        """测试超时风险触发减仓"""
        normal_updates.t_hit_q50_bars = 15  # 远超grace period
        
        request = ExitRequest(position=base_position, updates=normal_updates)
        response = decide_exit(request)
        
        assert response.action in ["reduce", "close"]
        
        # 原因中应该包含timeout
        reason_text = " ".join(response.reason)
        assert "timeout" in reason_text.lower()


class TestMPCScenarios:
    """MPC场景测试"""
    
    def test_simulate_exit_scenarios(self):
        """测试退出场景模拟"""
        base_position = {
            "avg_entry": 2415.0,
            "side": "short",
            "qty": 120,
            "upl_pct": 0.42
        }
        
        results = simulate_exit_scenarios(base_position)
        
        # 应该有多个场景
        assert len(results) >= 4
        
        # 检查每个场景的结果
        for result in results:
            assert "scenario" in result
            assert "action" in result
            assert "reduce_pct" in result
            assert "reasons" in result
            assert "runtime_ms" in result
            
            # 动作应该有效
            assert result["action"] in ["hold", "reduce", "close", "trail"]
            
            # 如果是减仓，百分比应该有效
            if result["action"] in ["reduce", "trail"]:
                assert 0 < result["reduce_pct"] <= 1
            elif result["action"] == "close":
                assert result["reduce_pct"] == 1.0
    
    def test_scenario_critical_should_close(self):
        """测试critical场景应该平仓"""
        base_position = {
            "avg_entry": 2415.0,
            "side": "short", 
            "qty": 120,
            "upl_pct": 0.42
        }
        
        results = simulate_exit_scenarios(base_position)
        
        # 找到critical场景
        critical_result = None
        for result in results:
            if result["scenario"] == "Critical":
                critical_result = result
                break
        
        assert critical_result is not None, "Should have critical scenario"
        assert critical_result["action"] == "close", "Critical scenario should trigger close"
    
    def test_scenario_normal_should_hold_or_light_action(self):
        """测试normal场景应该持有或轻微动作"""
        base_position = {
            "avg_entry": 2415.0,
            "side": "short",
            "qty": 120, 
            "upl_pct": 0.42
        }
        
        results = simulate_exit_scenarios(base_position)
        
        # 找到normal场景
        normal_result = None
        for result in results:
            if result["scenario"] == "Normal":
                normal_result = result
                break
        
        assert normal_result is not None, "Should have normal scenario"
        # Normal场景应该是hold或轻微减仓
        if normal_result["action"] != "hold":
            assert normal_result["reduce_pct"] <= 0.5, "Normal scenario should not trigger heavy reduction"


@pytest.mark.integration 
class TestHazardMPCIntegration:
    """Hazard与MPC集成测试"""
    
    def test_hazard_influences_mpc_decision(self):
        """测试hazard率影响MPC决策"""
        base_position = Position(
            avg_entry=2415.0,
            side="short",
            qty=120.0,
            upl_pct=0.42
        )
        
        # 低hazard测试
        low_hazard_updates = ExitUpdates(
            p_hit=0.70,
            mae_q90=0.003,
            t_hit_q50_bars=6,
            h_t=0.10,  # 低hazard
            dCVD=-0.5,
            replenish=0.65
        )
        
        low_hazard_request = ExitRequest(position=base_position, updates=low_hazard_updates)
        low_hazard_response = decide_exit(low_hazard_request)
        
        # 高hazard测试
        high_hazard_updates = ExitUpdates(
            p_hit=0.70,
            mae_q90=0.003,
            t_hit_q50_bars=6,
            h_t=0.40,  # 高hazard
            dCVD=-0.5,
            replenish=0.65
        )
        
        high_hazard_request = ExitRequest(position=base_position, updates=high_hazard_updates)
        high_hazard_response = decide_exit(high_hazard_request)
        
        # 高hazard应该触发更强的动作
        action_strength = {"hold": 0, "trail": 1, "reduce": 2, "close": 3}
        
        low_strength = action_strength[low_hazard_response.action]
        high_strength = action_strength[high_hazard_response.action]
        
        assert high_strength >= low_strength, "Higher hazard should trigger stronger action"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
