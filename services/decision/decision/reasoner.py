"""鏈式推理主流程 - Decision Agent"""
import time
from typing import Dict, List, Tuple

from loguru import logger

from ..core.config import config_manager
from ..core.utils import perf_monitor, timer
from ..gates import consensus, event_latency, liq_buffer, vol
from ..models.ctfg import ctfg_model
from ..models.quantile import quantile_predictor
from ..brains.xlstm import infer_sequence as xlstm_infer_sequence
from ..brains.llm_reasoner import reason as llm_reason
from ..schemas.features import EnterRequest
from ..schemas.responses import EnterResponse
from ..schemas.base import ExecutionConfig, RiskMetrics


def run_gate_checks(request: EnterRequest) -> Tuple[bool, List[str], List[str]]:
    """
    运行所有Gate检查
    
    Returns:
        (是否通过所有Gates, 通过的检查, 失败的检查)
    """
    passed_checks = []
    failed_checks = []
    
    # 1. 事件与延迟Gate
    event_ok, event_msg = event_latency.passes()
    if event_ok:
        passed_checks.append(event_msg)
    else:
        failed_checks.append(event_msg)
    
    # 2. 波动率Gate
    vol_ok, vol_msg = vol.check_vol_gate(request.features, request.side_hint)
    if vol_ok:
        passed_checks.append(vol_msg)
    else:
        failed_checks.append(vol_msg)
    
    # 3. 共识Gate
    consensus_ok, consensus_msg = consensus.passes(request.features)
    if consensus_ok:
        passed_checks.append(consensus_msg)
    else:
        failed_checks.append(consensus_msg)
    
    # 4. 流动性缓冲Gate
    liq_ok, liq_msg, risk_details = liq_buffer.passes(request.features, request.pgm)
    if liq_ok:
        passed_checks.append(liq_msg)
    else:
        failed_checks.append(liq_msg)
    
    # 所有Gate都必须通过
    all_passed = len(failed_checks) == 0
    
    return all_passed, passed_checks, failed_checks


def generate_reason_chain(
    request: EnterRequest, 
    gates_passed: bool, 
    passed_checks: List[str], 
    failed_checks: List[str],
    pgm_result = None
) -> List[str]:
    """生成推理链"""
    reason_chain = []
    
    # 1. Gate检查结果
    if gates_passed:
        reason_chain.append("✓ All Gates PASSED")
        # 添加关键指标
        reason_chain.append(f"C_align={request.features.C_align:.2f}")
        reason_chain.append(f"C_of={request.features.C_of:.2f}")
        reason_chain.append(f"C_vision={request.features.C_vision:.2f}")
        
        if pgm_result:
            reason_chain.append(f"p_hit={pgm_result.p_hit:.2f}/T50={pgm_result.t_hit_q50_bars}")
        
        reason_chain.append("MAE+Slip+ε ≤ LiqBuffer")
        
        # 添加因子分析
        if pgm_result and pgm_result.factors:
            top_factors = sorted(pgm_result.factors, key=lambda x: abs(x[1]), reverse=True)[:3]
            factor_str = ", ".join([f"{name}({weight:+.2f})" for name, weight in top_factors])
            reason_chain.append(f"Top factors: {factor_str}")
        
    else:
        reason_chain.append("✗ Gate FAILURE:")
        reason_chain.extend(failed_checks)
    
    return reason_chain


def run_fragility_test(request: EnterRequest, pgm_result) -> Tuple[bool, str]:
    """
    脆弱性测试 - 擾動最強因子/參數，檢查決策是否翻盤
    
    简化实现：检查关键指标的边界情况
    """
    try:
        # 检查关键指标是否接近阈值边界
        fragility_issues = []
        
        # 1. 检查C指标的稳定性
        c_align_margin = request.features.C_align - config_manager.get("gates.C_align_min", 0.85)
        if c_align_margin < 0.05:  # 5%的安全边距
            fragility_issues.append(f"C_align margin only {c_align_margin:.3f}")
        
        c_of_margin = request.features.C_of - config_manager.get("gates.C_of_min", 0.80)
        if c_of_margin < 0.05:
            fragility_issues.append(f"C_of margin only {c_of_margin:.3f}")
        
        # 2. 检查P_hit的稳定性
        p_hit_margin = pgm_result.p_hit - config_manager.get("gates.p_hit_min", 0.75)
        if p_hit_margin < 0.05:
            fragility_issues.append(f"p_hit margin only {p_hit_margin:.3f}")
        
        # 3. 检查流动性缓冲的稳定性
        liq_buffer = abs(request.features.market.mark - request.features.market.liq_price) / request.features.market.mark
        risk_budget = pgm_result.mae_q999 + pgm_result.slip_q95 + config_manager.get("gates.epsilon", 0.0005)
        safety_margin = liq_buffer - risk_budget
        
        if safety_margin < 0.005:  # 50bp的安全边距
            fragility_issues.append(f"LiqBuffer safety margin only {safety_margin:.4f}")
        
        # 4. 检查波动率的稳定性
        sigma = request.features.sigma_1m
        vol_config = config_manager.get_vol_config(request.side_hint)
        
        if vol_config:
            sigma_min = vol_config.get("sigma_min", 0)
            sigma_max = vol_config.get("sigma_max", float("inf"))
            
            if sigma - sigma_min < 0.0002:  # 接近下界
                fragility_issues.append(f"Sigma close to lower bound: {sigma:.4f}")
            if sigma_max - sigma < 0.0002:  # 接近上界
                fragility_issues.append(f"Sigma close to upper bound: {sigma:.4f}")
        
        # 判断脆弱性
        if fragility_issues:
            return False, f"Fragility issues: {'; '.join(fragility_issues)}"
        else:
            return True, "Fragility test PASSED"
            
    except Exception as e:
        logger.warning(f"Fragility test error: {e}")
        return True, "Fragility test skipped due to error"


def determine_allocation_and_side(request: EnterRequest, pgm_result) -> Tuple[str, float]:
    """确定方向和分配"""
    # 基于多个信号确定最终方向
    signals_long = 0
    signals_short = 0
    
    # Z-score信号
    avg_z = (request.features.Z_4H + request.features.Z_1H + request.features.Z_15m) / 3
    if avg_z > 0.5:
        signals_long += 1
    elif avg_z < -0.5:
        signals_short += 1
    
    # 偏度信号
    if request.features.skew_1m > 0.5:
        signals_long += 1
    elif request.features.skew_1m < -0.5:
        signals_short += 1
    
    # OrderFlow信号
    if request.features.OF.dCVD > 1.0:
        signals_long += 1
    elif request.features.OF.dCVD < -1.0:
        signals_short += 1
    
    # 默认使用side_hint
    if signals_long > signals_short:
        suggested_side = "long"
    elif signals_short > signals_long:
        suggested_side = "short"
    else:
        suggested_side = request.side_hint
    
    # 分配基于置信度
    base_allocation = 0.6  # 基础分配60%
    confidence_boost = (pgm_result.p_hit - 0.75) * 2  # p_hit每超过75%的1%，增加2%分配
    
    allocation = min(base_allocation + confidence_boost, 0.9)  # 最多90%分配
    allocation = max(allocation, 0.1)  # 最少10%分配
    
    return suggested_side, allocation


def decide_enter(request: EnterRequest, config: Dict = None) -> EnterResponse:
    """
    主入场决策函数
    
    决策流程：
    1. 先驗拒單（Event/Latency/Vol）
    2. 多假說：H_long / H_short / H_wait
    3. 證據鏈：TV、YOLO、HTF/LTF、OF、OI/Gas 支持/反證
    4. 融合：CTFG → P(hit)；xLSTM → Q(MAE)/Q(Slip)/T_hit；Conformal 校準
    5. 邊界：Liq-Buffer 檢核
    6. 脆弱性：拔最強因子/擾動 σ/深度/OF，不可翻盤
    7. 行動：允許/拒絕、side、alloc、exec；輸出 reason_chain
    """
    
    with timer() as timing:
        try:
            # 获取配置
            if config is None:
                config = config_manager.get_gates_config()
            
            # 1. Gate检查
            gates_passed, passed_checks, failed_checks = run_gate_checks(request)
            
            # 如果Gate失败，直接拒绝
            if not gates_passed:
                reason_chain = generate_reason_chain(request, False, passed_checks, failed_checks)
                
                return EnterResponse(
                    allow=False,
                    side=None,
                    alloc_equity_pct=None,
                    exec=None,
                    risk=None,
                    reason_chain=reason_chain,
                    runtime_ms=timing["duration_ms"]
                )
            
            # 2. PGM模型推理
            pgm_result = ctfg_model.predict(request.features)

            # 2.1 xLSTM 長序推斷（v2 升級）：併行估計時序上下文
            xlstm_meta = {"tf": request.tf, "symbol": request.symbol}
            try:
                xlstm_ctx = xlstm_infer_sequence(token_seq=[], of_seq=[], tv_seq=[], meta=xlstm_meta)
            except Exception:
                xlstm_ctx = {}
            
            # 3. 脆弱性测试
            fragility_ok, fragility_msg = run_fragility_test(request, pgm_result)
            
            # 4. 最终决策
            if not fragility_ok:
                reason_chain = generate_reason_chain(request, True, passed_checks, failed_checks, pgm_result)
                reason_chain.append(f"FRAGILITY FAIL: {fragility_msg}")
                
                return EnterResponse(
                    allow=False,
                    side=None,
                    alloc_equity_pct=None,
                    exec=None,
                    risk=None,
                    reason_chain=reason_chain,
                    runtime_ms=timing["duration_ms"]
                )
            
            # 4.1 邊界單 → 啟用 LLM 仲裁（僅在邊界區間介入）
            used_llm = False
            llm_out = None
            borderline = 0.72 <= pgm_result.p_hit <= 0.78
            if borderline:
                try:
                    llm_out = llm_reason(
                        {
                            "symbol": request.symbol,
                            "tf": request.tf,
                            "features": request.features.model_dump(),
                            "pgm": pgm_result.model_dump(),
                            "xlstm": xlstm_ctx,
                        }
                    )
                    used_llm = True
                except Exception:
                    used_llm = False

            # 5. 生成允许响应
            suggested_side, allocation = determine_allocation_and_side(request, pgm_result)
            
            # 构建执行配置
            exec_config = ExecutionConfig(
                type=config_manager.get("exec.mode", "post_only_limit_or_mpo"),
                reduce_only_fallback=config_manager.get("exec.reduce_only_fallback", True)
            )
            
            # 构建风险指标
            liq_buffer_pct = abs(request.features.market.mark - request.features.market.liq_price) / request.features.market.mark
            risk_budget = pgm_result.mae_q999 + pgm_result.slip_q95 + config_manager.get("gates.epsilon", 0.0005)
            
            risk_metrics = RiskMetrics(
                liq_buffer_pct=liq_buffer_pct,
                lhs_pct=risk_budget
            )
            
            # 生成推理链
            reason_chain = generate_reason_chain(request, True, passed_checks, failed_checks, pgm_result)
            reason_chain.append(fragility_msg)
            if xlstm_ctx:
                reason_chain.append(
                    f"xLSTM: p_up_1pct={xlstm_ctx.get('p_up_1pct', 0):.2f}/t50={xlstm_ctx.get('t_hit50', 0)}"
                )
            if used_llm and isinstance(llm_out, dict):
                reason_chain.append(
                    f"LLM_arb: meta={llm_out.get('meta_tag','-')}, c_llm={llm_out.get('c_llm',0):.2f}"
                )
            
            # 记录性能
            perf_monitor.record("decision", timing["duration_ms"])
            
            return EnterResponse(
                allow=True,
                side=suggested_side,
                alloc_equity_pct=allocation,
                exec=exec_config,
                risk=risk_metrics,
                reason_chain=reason_chain,
                runtime_ms=timing["duration_ms"]
            )
            
        except Exception as e:
            logger.error(f"Error in enter decision: {e}")
            
            return EnterResponse(
                allow=False,
                side=None,
                alloc_equity_pct=None,
                exec=None,
                risk=None,
                reason_chain=[f"Decision error: {str(e)}"],
                runtime_ms=timing.get("duration_ms", 0)
            )
