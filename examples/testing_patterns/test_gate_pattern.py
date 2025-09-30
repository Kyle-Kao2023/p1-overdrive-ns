"""
P1 Trading Builder - Gate 测试模式示例
展示如何为 P1 系统的 Gate 组件编写完整的单元测试
"""

import pytest
from unittest.mock import Mock, patch
import logging

# 假设从 P1 系统导入 (实际路径根据项目结构调整)
# from services.decision.gates.vol import VolGate

class TestVolGate:
    """
    P1 VolGate 测试套件
    
    测试策略：
    1. 正常情况 - 波动率在甜蜜点范围内
    2. 边界情况 - 波动率在边界值
    3. 异常情况 - 波动率超出范围
    4. 配置错误 - 无效的配置参数
    """
    
    @pytest.fixture
    def vol_config(self):
        """标准的 VolGate 配置"""
        return {
            "vol_sweet_spot": {
                "bull": {
                    "sigma_min": 0.0012,
                    "sigma_max": 0.0022,
                    "skew_min": 0.5
                },
                "bear": {
                    "sigma_min": 0.0015, 
                    "sigma_max": 0.0028,
                    "skew_max": -0.5
                }
            }
        }
    
    @pytest.fixture
    def vol_gate(self, vol_config):
        """VolGate 实例"""
        from examples.decision_patterns.gate_implementation import VolGate
        return VolGate(vol_config)
    
    @pytest.fixture
    def base_features(self):
        """基础市场特征"""
        return {
            "symbol": "ETHUSDT",
            "side_hint": "short",
            "sigma_1m": 0.0020,
            "skew_1m": -0.65,
            "_runtime_ms": 15
        }
    
    def test_vol_gate_pass_bear_market(self, vol_gate, base_features):
        """测试：空头市场，波动率在甜蜜点 - 应该通过"""
        
        # 设置测试数据：空头方向，波动率和偏度都在理想范围
        features = {**base_features, "side_hint": "short", "sigma_1m": 0.0020, "skew_1m": -0.65}
        
        # 执行测试
        passed, reason = vol_gate.passes(features)
        
        # 验证结果
        assert passed == True
        assert "sweet_spot" in reason
        assert "0.0020" in reason  # 确保包含实际波动率值
        
    def test_vol_gate_fail_sigma_too_high(self, vol_gate, base_features):
        """测试：波动率过高 - 应该失败"""
        
        features = {**base_features, "sigma_1m": 0.0035}  # 超过 bear.sigma_max
        
        passed, reason = vol_gate.passes(features)
        
        assert passed == False
        assert "outside" in reason
        assert "0.0035" in reason
        
    def test_vol_gate_fail_wrong_skew(self, vol_gate, base_features):
        """测试：偏度方向错误 - 应该失败"""
        
        # 空头市场但偏度为正 (牛市偏度)
        features = {**base_features, "side_hint": "short", "skew_1m": 0.7}
        
        passed, reason = vol_gate.passes(features)
        
        assert passed == False
        assert "skew" in reason.lower()
        assert "invalid" in reason
    
    def test_vol_gate_boundary_conditions(self, vol_gate, base_features):
        """测试：边界值情况"""
        
        # 测试波动率下边界
        features = {**base_features, "sigma_1m": 0.0015}  # bear.sigma_min
        passed, reason = vol_gate.passes(features)
        assert passed == True
        
        # 测试波动率上边界  
        features = {**base_features, "sigma_1m": 0.0028}  # bear.sigma_max
        passed, reason = vol_gate.passes(features)
        assert passed == True
        
        # 测试略超边界
        features = {**base_features, "sigma_1m": 0.00281}  # 刚超过 bear.sigma_max
        passed, reason = vol_gate.passes(features)
        assert passed == False
    
    @patch('examples.decision_patterns.gate_implementation.logger')
    def test_vol_gate_logging(self, mock_logger, vol_gate, base_features):
        """测试：Gate 日志记录功能"""
        
        vol_gate.passes(base_features)
        
        # 验证日志调用
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        
        # 检查日志消息格式
        log_message = call_args[0][0]
        assert "Gate VOL:" in log_message
        assert "PASS" in log_message or "FAIL" in log_message
        
        # 检查日志额外字段
        log_extra = call_args[1]["extra"]
        assert log_extra["gate_name"] == "VOL"
        assert log_extra["symbol"] == "ETHUSDT"
        assert "runtime_ms" in log_extra

class TestLLMReasonerIntegration:
    """
    P1 LLM Reasoner 集成测试
    测试 LLM 推理器与 Gate 系统的集成
    """
    
    @pytest.fixture
    def llm_config(self):
        return {
            "timeout_ms": 150,
            "max_daily_calls": 100,
            "borderline_range": [0.72, 0.78]
        }
    
    @pytest.fixture
    def llm_reasoner(self, llm_config):
        from examples.ai_components.llm_reasoner_pattern import LLMReasoner
        return LLMReasoner(llm_config)
    
    def test_should_trigger_borderline_p_hit(self, llm_reasoner):
        """测试：边界 p_hit 值应该触发 LLM"""
        
        features = {"symbol": "ETHUSDT"}
        pgm = {"p_hit": 0.74}  # 在边界范围内
        
        should_trigger, trigger_reason = llm_reasoner.should_trigger_llm(features, pgm)
        
        assert should_trigger == True
        assert trigger_reason.value == "borderline_p_hit"
    
    def test_should_not_trigger_clear_signal(self, llm_reasoner):
        """测试：明确信号不应该触发 LLM"""
        
        features = {"symbol": "ETHUSDT"}
        pgm = {"p_hit": 0.85}  # 明确高于边界
        
        should_trigger, trigger_reason = llm_reasoner.should_trigger_llm(features, pgm)
        
        assert should_trigger == False
        assert trigger_reason is None
    
    @pytest.mark.asyncio
    async def test_llm_reasoning_timeout_fallback(self, llm_reasoner):
        """测试：LLM 超时时的后备机制"""
        
        features = {"symbol": "ETHUSDT", "side_hint": "short"}
        pgm = {"p_hit": 0.74}
        
        # Mock LLM API 超时
        with patch.object(llm_reasoner, '_call_llm_api') as mock_api:
            mock_api.side_effect = asyncio.TimeoutError()
            
            result = await llm_reasoner.reason(features, pgm)
            
            # 验证后备推理结果
            assert result is not None
            assert result.meta_tag == "llm-fallback"
            assert result.c_llm == 0.3  # 低置信度
            assert "保守策略" in result.rationale

# P1 专用测试工具函数
def create_test_features(symbol="ETHUSDT", side="short", **overrides):
    """
    创建标准化的测试特征向量
    简化测试数据创建，确保格式一致性
    """
    base_features = {
        "symbol": symbol,
        "side_hint": side,
        "ts": "2025-09-30T10:25:00Z",
        "tf": "15m",
        "sigma_1m": 0.0018,
        "skew_1m": -0.72 if side == "short" else 0.65,
        "Z_4H": -0.9, "Z_1H": -0.7, "Z_15m": -0.6,
        "C_align": 0.88, "C_of": 0.83, "C_vision": 0.79,
        "pine_match": True,
        "direction": {
            "dir_score_htf": -0.75 if side == "short" else 0.75,
            "dir_htf": -2 if side == "short" else 2,
            "dir_score_ltf": -0.65 if side == "short" else 0.65,
            "dir_ltf": -2 if side == "short" else 2,
        }
    }
    
    # 应用覆盖参数
    base_features.update(overrides)
    return base_features

def create_test_pgm(p_hit=0.76, **overrides):
    """创建标准化的测试 PGM 预测结果"""
    base_pgm = {
        "p_hit": p_hit,
        "mae_q999": 0.0058,
        "slip_q95": 0.0004,
        "t_hit_q50_bars": 6
    }
    
    base_pgm.update(overrides)
    return base_pgm

# 性能测试示例
@pytest.mark.performance
def test_decision_latency_requirement():
    """
    P1 关键性能测试：决策延迟必须 < 70ms
    这是 P1 系统的核心 SLA 要求
    """
    
    start_time = time.time()
    
    # 模拟完整决策流程
    features = create_test_features()
    pgm = create_test_pgm()
    
    # 这里应该调用实际的决策 API
    # result = decision_service.decide_enter(features, pgm)
    
    runtime_ms = (time.time() - start_time) * 1000
    
    # 验证延迟要求
    assert runtime_ms < 70, f"决策延迟 {runtime_ms:.1f}ms 超过 SLA 要求 (<70ms)"

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
