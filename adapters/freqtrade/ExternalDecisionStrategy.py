"""Freqtrade外部决策策略适配器"""
import requests
from datetime import datetime
from typing import Optional

from freqtrade.strategy import IStrategy, DecimalParameter
import talib.abstract as ta
import pandas as pd
import numpy as np
from pandas import DataFrame

# 决策服务配置
DECISION_URL = "http://localhost:8000"
FEATUREHUB_URL = "http://localhost:8010"
TIMEOUT_MS = 50


class ExternalDecisionStrategy(IStrategy):
    """
    P1 External Decision Strategy
    
    使用外部决策服务进行入场和退出决策
    """
    
    # 策略参数
    INTERFACE_VERSION = 3
    
    # 最小ROI设置（由于使用外部决策，设置为禁用）
    minimal_roi = {"0": 100}
    
    # 止损设置（No-Stop策略）
    stoploss = -0.99
    
    # 时间框架
    timeframe = '15m'
    
    # 启动周期数
    startup_candle_count: int = 50
    
    # 可选参数
    decision_timeout = DecimalParameter(0.03, 0.1, default=0.05, space="buy")
    
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """填充技术指标"""
        
        # 基础价格指标
        dataframe['hl2'] = (dataframe['high'] + dataframe['low']) / 2
        dataframe['hlc3'] = (dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        
        # 移动平均线
        dataframe['ema_9'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema_21'] = ta.EMA(dataframe, timeperiod=21)
        dataframe['sma_50'] = ta.SMA(dataframe, timeperiod=50)
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']
        
        # 布林带
        bollinger = ta.BBANDS(dataframe)
        dataframe['bb_lower'] = bollinger['lowerband']
        dataframe['bb_middle'] = bollinger['middleband'] 
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])
        
        # 成交量指标
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        
        # 波动率计算
        dataframe['log_return'] = np.log(dataframe['close'] / dataframe['close'].shift(1))
        dataframe['volatility_1m'] = dataframe['log_return'].rolling(5).std()
        dataframe['skew_1m'] = dataframe['log_return'].rolling(20).skew()
        
        # Z-scores (多时间框架)
        for period in [96, 24, 4]:  # 4H, 1H, 15m (in 15m candles)
            col_name = f'z_{period}'
            dataframe[col_name] = (dataframe['close'] - dataframe['close'].rolling(period).mean()) / dataframe['close'].rolling(period).std()
        
        return dataframe
    
    def get_market_snapshot(self, symbol: str) -> Optional[dict]:
        """从FeatureHub获取市场快照"""
        try:
            response = requests.get(
                f"{FEATUREHUB_URL}/snapshot",
                params={"symbol": symbol, "timeframe": self.timeframe},
                timeout=self.decision_timeout.value
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"FeatureHub error: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"Error getting market snapshot: {e}")
            return None
    
    def create_enter_request(self, dataframe: DataFrame, metadata: dict, side_hint: str) -> dict:
        """创建入场决策请求"""
        symbol = metadata['pair']
        latest = dataframe.iloc[-1]
        
        # 获取市场快照
        snapshot = self.get_market_snapshot(symbol)
        
        if snapshot:
            # 使用FeatureHub的数据
            features = {
                "sigma_1m": snapshot.get("sigma_1m", 0.002),
                "skew_1m": snapshot.get("skew_1m", 0.0),
                "Z_4H": snapshot["z_scores"].get("4H", 0.0),
                "Z_1H": snapshot["z_scores"].get("1H", 0.0), 
                "Z_15m": snapshot["z_scores"].get("15m", 0.0),
                "C_align": snapshot.get("c_align", 0.8),
                "C_of": snapshot.get("c_of", 0.8),
                "C_vision": snapshot.get("c_vision", 0.75),
                "pine_match": True,  # 假设Freqtrade信号匹配
                "onchain": snapshot.get("onchain", {"oi_roc": 0.0, "gas_z": 0.0}),
                "OF": snapshot.get("orderflow", {"obi": 0.0, "dCVD": 0.0, "replenish": 0.6}),
                "vision_tokens": {"tokens": {}},
                "market": {
                    "mark": snapshot.get("mark_price", latest['close']),
                    "liq_price": snapshot.get("mark_price", latest['close']) * (1.1 if side_hint == "long" else 0.9),
                    "spread_bp": snapshot.get("spread_bp", 5.0),
                    "depth_px": snapshot.get("depth_px", 1000000)
                }
            }
        else:
            # 使用本地计算的fallback数据
            features = {
                "sigma_1m": latest.get('volatility_1m', 0.002),
                "skew_1m": latest.get('skew_1m', 0.0),
                "Z_4H": latest.get('z_96', 0.0),
                "Z_1H": latest.get('z_24', 0.0),
                "Z_15m": latest.get('z_4', 0.0),
                "C_align": 0.85,  # 默认值
                "C_of": 0.80,
                "C_vision": 0.75,
                "pine_match": True,
                "onchain": {"oi_roc": 0.0, "gas_z": 0.0},
                "OF": {"obi": 0.0, "dCVD": 0.0, "replenish": 0.6},
                "vision_tokens": {"tokens": {}},
                "market": {
                    "mark": latest['close'],
                    "liq_price": latest['close'] * (1.1 if side_hint == "long" else 0.9),
                    "spread_bp": 5.0,
                    "depth_px": 1000000
                }
            }
        
        # PGM指标（简化）
        pgm = {
            "p_hit": 0.78,
            "mae_q999": 0.006,
            "slip_q95": 0.0005,
            "t_hit_q50_bars": 6,
            "factors": []
        }
        
        return {
            "symbol": symbol,
            "side_hint": side_hint,
            "ts": datetime.utcnow().isoformat(),
            "tf": self.timeframe,
            "features": features,
            "pgm": pgm
        }
    
    def call_decision_api(self, endpoint: str, payload: dict) -> Optional[dict]:
        """调用决策API"""
        try:
            response = requests.post(
                f"{DECISION_URL}/{endpoint}",
                json=payload,
                timeout=self.decision_timeout.value
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log(f"Decision API error: {response.status_code}")
                return None
                
        except Exception as e:
            self.log(f"Error calling decision API: {e}")
            return None
    
    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """填充入场信号"""
        
        # 初始化信号列
        dataframe['enter_long'] = 0
        dataframe['enter_short'] = 0
        dataframe['enter_tag'] = ''
        
        # 只在最新的K线上进行决策（避免重复调用API）
        if len(dataframe) < 2:
            return dataframe
        
        # 检查多头信号
        long_request = self.create_enter_request(dataframe, metadata, "long")
        long_decision = self.call_decision_api("decide/enter", long_request)
        
        if long_decision and long_decision.get("allow") and long_decision.get("side") == "long":
            dataframe.loc[dataframe.index[-1], 'enter_long'] = 1
            dataframe.loc[dataframe.index[-1], 'enter_tag'] = f"p1_long_{long_decision.get('alloc_equity_pct', 0.6):.1f}"
            self.log(f"Long signal: {long_decision.get('reason_chain', [])}")
        
        # 检查空头信号
        short_request = self.create_enter_request(dataframe, metadata, "short")
        short_decision = self.call_decision_api("decide/enter", short_request)
        
        if short_decision and short_decision.get("allow") and short_decision.get("side") == "short":
            dataframe.loc[dataframe.index[-1], 'enter_short'] = 1
            dataframe.loc[dataframe.index[-1], 'enter_tag'] = f"p1_short_{short_decision.get('alloc_equity_pct', 0.6):.1f}"
            self.log(f"Short signal: {short_decision.get('reason_chain', [])}")
        
        return dataframe
    
    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """填充退出信号（使用custom_exit代替）"""
        dataframe['exit_long'] = 0
        dataframe['exit_short'] = 0
        return dataframe
    
    def custom_exit(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs) -> Optional[str]:
        """自定义退出逻辑"""
        
        # 构建退出请求
        exit_request = {
            "position": {
                "avg_entry": trade.open_rate,
                "side": "long" if trade.is_short else "short",
                "qty": trade.amount,
                "upl_pct": current_profit
            },
            "updates": {
                "p_hit": 0.65,  # 简化值
                "mae_q90": 0.003,
                "t_hit_q50_bars": 8,
                "h_t": 0.25,  # 简化hazard
                "dCVD": 0.0,
                "replenish": 0.6
            }
        }
        
        # 调用退出决策API
        exit_decision = self.call_decision_api("decide/exit", exit_request)
        
        if exit_decision:
            action = exit_decision.get("action", "hold")
            
            if action == "close":
                self.log(f"P1 Exit: CLOSE - {exit_decision.get('reason', [])}")
                return "p1_close"
            elif action == "reduce":
                reduce_pct = exit_decision.get("reduce_pct", 0.5)
                self.log(f"P1 Exit: REDUCE {reduce_pct:.1%} - {exit_decision.get('reason', [])}")
                return f"p1_reduce_{reduce_pct:.0%}"
        
        return None
    
    def log(self, message: str) -> None:
        """记录日志"""
        print(f"[P1Strategy] {message}")  # 可以集成到Freqtrade的日志系统
