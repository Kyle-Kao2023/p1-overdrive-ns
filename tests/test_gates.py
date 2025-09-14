"""Gate逻辑测试"""
import pytest
from services.decision.schemas.features import Features, PGMMetrics
from services.decision.schemas.base import OnChain, OrderFlow, VisionTokens, MarketSnapshot
from services.decision.gates import vol, consensus, liq_buffer, event_latency


@pytest.fixture
def bull_features():
    """牛市特征数据"""
    return Features(
        sigma_1m=0.0015,  # 在bull范围内
        skew_1m=0.65,     # 正向偏度
        Z_4H=0.8,
        Z_1H=0.6,
        Z_15m=0.7,
        C_align=0.89,     # 高一致性
        C_of=0.85,
        C_vision=0.82,
        pine_match=True,
        onchain=OnChain(oi_roc=0.12, gas_z=-0.5),
        OF=OrderFlow(obi=0.67, dCVD=2.1, replenish=0.78),
        vision_tokens=VisionTokens(tokens={"bull_hammer": 0.85}),
        market=MarketSnapshot(mark=43250.5, liq_price=41800.0, spread_bp=2, depth_px=2500000)
    )


@pytest.fixture
def bear_features():
    """熊市特征数据"""
    return Features(
        sigma_1m=0.0018,  # 在bear范围内
        skew_1m=-0.72,    # 负向偏度
        Z_4H=-0.9,
        Z_1H=-0.7,
        Z_15m=-0.6,
        C_align=0.88,
        C_of=0.83,
        C_vision=0.79,
        pine_match=True,
        onchain=OnChain(oi_roc=0.08, gas_z=1.1),
        OF=OrderFlow(obi=0.31, dCVD=-1.2, replenish=0.67),
        vision_tokens=VisionTokens(tokens={"bear_engulfing": 0.82}),
        market=MarketSnapshot(mark=2415.3, liq_price=2458.8, spread_bp=3, depth_px=1200000)
    )


@pytest.fixture
def good_pgm():
    """良好的PGM指标"""
    return PGMMetrics(
        p_hit=0.79,
        mae_q999=0.0058,
        slip_q95=0.0004,
        t_hit_q50_bars=6,
        factors=[["Z4H//Z15m", 0.21], ["OF_triad", 0.18]]
    )


class TestVolGate:
    """波动率Gate测试"""
    
    def test_bull_vol_sweet_spot_pass(self, bull_features):
        """测试牛市波动率甜蜜点通过"""
        passed, msg = vol.check_vol_gate(bull_features, "long")
        assert passed, f"Bull vol gate should pass: {msg}"
        assert "PASS" in msg
    
    def test_bear_vol_sweet_spot_pass(self, bear_features):
        """测试熊市波动率甜蜜点通过"""
        passed, msg = vol.check_vol_gate(bear_features, "short")
        assert passed, f"Bear vol gate should pass: {msg}"
        assert "PASS" in msg
    
    def test_vol_gate_fail_extreme_sigma(self, bull_features):
        """测试极端波动率被拒绝"""
        bull_features.sigma_1m = 0.005  # 过高的波动率
        passed, msg = vol.check_vol_gate(bull_features, "long")
        assert not passed, "Extreme volatility should be rejected"
        assert "FAIL" in msg
    
    def test_vol_gate_fail_neutral_skew(self, bull_features):
        """测试中性偏度被拒绝"""
        bull_features.skew_1m = 0.1  # 偏度绝对值太小
        passed, msg = vol.check_vol_gate(bull_features, "long")
        assert not passed, "Neutral skew should be rejected"
        assert "neutral" in msg.lower()


class TestConsensusGate:
    """共识Gate测试"""
    
    def test_consensus_pass_all_criteria(self, bull_features):
        """测试所有共识标准通过"""
        passed, msg = consensus.passes(bull_features)
        assert passed, f"All consensus criteria should pass: {msg}"
        assert "PASS" in msg
    
    def test_consensus_fail_low_c_align(self, bull_features):
        """测试C_align过低被拒绝"""
        bull_features.C_align = 0.75  # 低于0.85阈值
        passed, msg = consensus.passes(bull_features)
        assert not passed, "Low C_align should be rejected"
        assert "C_align" in msg
    
    def test_consensus_fail_pine_mismatch(self, bull_features):
        """测试Pine不匹配被拒绝"""
        bull_features.pine_match = False
        passed, msg = consensus.passes(bull_features)
        assert not passed, "Pine mismatch should be rejected"
        assert "Pine_match=False" in msg


class TestLiqBufferGate:
    """流动性缓冲Gate测试"""
    
    def test_liq_buffer_pass(self, bear_features, good_pgm):
        """测试流动性缓冲通过"""
        passed, msg, risk_details = liq_buffer.passes(bear_features, good_pgm)
        assert passed, f"Liq buffer should pass: {msg}"
        assert "PASS" in msg
        assert risk_details["safety_margin"] > 0
    
    def test_liq_buffer_fail_insufficient(self, bear_features, good_pgm):
        """测试流动性缓冲不足被拒绝"""
        # 设置过高的MAE
        good_pgm.mae_q999 = 0.02  # 2%的MAE，超过liq buffer
        passed, msg, risk_details = liq_buffer.passes(bear_features, good_pgm)
        assert not passed, "Insufficient liq buffer should be rejected"
        assert "FAIL" in msg
        assert risk_details["safety_margin"] < 0
    
    def test_liq_buffer_fail_low_depth(self, bear_features, good_pgm):
        """测试深度不足被拒绝"""
        bear_features.market.depth_px = 500000  # 低于最小深度
        passed, msg, risk_details = liq_buffer.passes(bear_features, good_pgm)
        assert not passed, "Low depth should be rejected"
        assert "Depth" in msg


class TestEventLatencyGate:
    """事件与延迟Gate测试"""
    
    def test_event_latency_pass_normal(self):
        """测试正常情况通过"""
        passed, msg = event_latency.passes()
        assert passed, f"Normal conditions should pass: {msg}"
        assert "PASS" in msg
    
    def test_blacklist_events_empty(self):
        """测试空黑名单事件"""
        passed, msg = event_latency.check_blacklist_events()
        assert passed, "Empty blacklist should pass"
        assert "No blacklist events" in msg


@pytest.mark.integration
class TestGateIntegration:
    """Gate集成测试"""
    
    def test_all_gates_pass_bull_scenario(self, bull_features, good_pgm):
        """测试牛市场景所有Gate通过"""
        # Vol Gate
        vol_pass, vol_msg = vol.check_vol_gate(bull_features, "long")
        
        # Consensus Gate  
        consensus_pass, consensus_msg = consensus.passes(bull_features)
        
        # Liq Buffer Gate
        liq_pass, liq_msg, _ = liq_buffer.passes(bull_features, good_pgm)
        
        # Event & Latency Gate
        event_pass, event_msg = event_latency.passes()
        
        # 所有Gate都应该通过
        assert vol_pass, f"Vol gate failed: {vol_msg}"
        assert consensus_pass, f"Consensus gate failed: {consensus_msg}"
        assert liq_pass, f"Liq buffer gate failed: {liq_msg}"
        assert event_pass, f"Event & latency gate failed: {event_msg}"
    
    def test_all_gates_pass_bear_scenario(self, bear_features, good_pgm):
        """测试熊市场景所有Gate通过"""
        # Vol Gate
        vol_pass, vol_msg = vol.check_vol_gate(bear_features, "short")
        
        # Consensus Gate
        consensus_pass, consensus_msg = consensus.passes(bear_features)
        
        # Liq Buffer Gate
        liq_pass, liq_msg, _ = liq_buffer.passes(bear_features, good_pgm)
        
        # Event & Latency Gate
        event_pass, event_msg = event_latency.passes()
        
        # 所有Gate都应该通过
        assert vol_pass, f"Vol gate failed: {vol_msg}"
        assert consensus_pass, f"Consensus gate failed: {consensus_msg}"
        assert liq_pass, f"Liq buffer gate failed: {liq_msg}"
        assert event_pass, f"Event & latency gate failed: {event_msg}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
