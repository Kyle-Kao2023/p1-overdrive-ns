#!/usr/bin/env python3
"""
Learner/Trainer 設置範例

演示如何設置和啟動 v2 學習訓練管道。
"""

import json
import os
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path

# 模擬導入 (實際使用時取消註釋)
# from services.decision.learner.experience_store import ExperienceStore
# from services.decision.learner.imitation import ImitationLearner
# from services.decision.learner.rl_trainer import RLTrainer

def create_sample_expert_data() -> List[Dict[str, Any]]:
    """創建範例專家交易數據"""
    return [
        {
            "trade_id": "expert_001",
            "timestamp": "2025-09-14T10:15:00Z",
            "symbol": "ETHUSDT",
            "features": {
                "sigma_1m": 0.0016,
                "Z_4H": -0.8,
                "Z_1H": -0.6,
                "C_align": 0.89,
                "direction": {
                    "dir_score_htf": -0.8,
                    "dir_htf": -3,
                    "dir_score_ltf": -0.7,
                    "dir_ltf": -2
                }
            },
            "expert_decision": {
                "action": "short",
                "size_pct": 0.03,
                "confidence": 0.85,
                "reasoning": "Strong HTF bearish with good alignment"
            },
            "outcome": {
                "p_hit_actual": 0.82,
                "mae_actual": 0.0045,
                "t_hit_actual_bars": 8,
                "pnl_pct": 0.0287
            },
            "expert_rating": 5,  # 1-5 星評分
            "market_regime": "high_vol_bear"
        },
        {
            "trade_id": "expert_002",
            "timestamp": "2025-09-14T14:30:00Z",
            "symbol": "BTCUSDT",
            "features": {
                "sigma_1m": 0.0022,
                "Z_4H": 0.9,
                "Z_1H": 0.7,
                "C_align": 0.91,
                "direction": {
                    "dir_score_htf": 0.85,
                    "dir_htf": 3,
                    "dir_score_ltf": 0.75,
                    "dir_ltf": 2
                }
            },
            "expert_decision": {
                "action": "long",
                "size_pct": 0.025,
                "confidence": 0.92,
                "reasoning": "Perfect bullish setup with strong momentum"
            },
            "outcome": {
                "p_hit_actual": 0.88,
                "mae_actual": 0.0031,
                "t_hit_actual_bars": 5,
                "pnl_pct": 0.0356
            },
            "expert_rating": 5,
            "market_regime": "trending_bull"
        },
        # 添加更多範例...
    ]

def create_human_feedback_data() -> List[Dict[str, Any]]:
    """創建人類反饋偏好數據"""
    return [
        {
            "feedback_id": "fb_001",
            "timestamp": "2025-09-14T16:00:00Z",
            "trade_pair": {
                "trade_a": {
                    "decision": "short",
                    "size_pct": 0.04,
                    "reasoning": "Technical indicators suggest downtrend"
                },
                "trade_b": {
                    "decision": "short",
                    "size_pct": 0.02,
                    "reasoning": "Conservative approach due to volatility"
                }
            },
            "human_preference": "B",  # 偏好交易 B
            "preference_reason": "Better risk management in uncertain conditions",
            "confidence": 0.8,
            "trader_experience": "expert"
        },
        {
            "feedback_id": "fb_002",
            "timestamp": "2025-09-14T17:15:00Z",
            "trade_pair": {
                "trade_a": {
                    "decision": "wait",
                    "size_pct": 0.0,
                    "reasoning": "Unclear signals, better to wait"
                },
                "trade_b": {
                    "decision": "long",
                    "size_pct": 0.015,
                    "reasoning": "Small position to capture potential upside"
                }
            },
            "human_preference": "A",
            "preference_reason": "Risk management more important than missing opportunities",
            "confidence": 0.9,
            "trader_experience": "intermediate"
        }
    ]

def setup_experience_store():
    """設置經驗存儲系統"""
    print("🗄️ 設置 Experience Store...")

    # 創建數據目錄
    data_dir = Path("data/v2/experience")
    data_dir.mkdir(parents=True, exist_ok=True)

    # 保存專家數據
    expert_data = create_sample_expert_data()
    expert_file = data_dir / "expert_trades.jsonl"

    with open(expert_file, 'w', encoding='utf-8') as f:
        for trade in expert_data:
            f.write(json.dumps(trade, ensure_ascii=False) + '\n')

    print(f"✅ 專家交易數據保存到: {expert_file}")
    print(f"   包含 {len(expert_data)} 筆專家交易")

    # 保存偏好數據
    feedback_data = create_human_feedback_data()
    feedback_file = data_dir / "human_feedback.jsonl"

    with open(feedback_file, 'w', encoding='utf-8') as f:
        for feedback in feedback_data:
            f.write(json.dumps(feedback, ensure_ascii=False) + '\n')

    print(f"✅ 人類反饋數據保存到: {feedback_file}")
    print(f"   包含 {len(feedback_data)} 筆偏好反饋")

def setup_imitation_learning():
    """設置模仿學習"""
    print("\n🎓 設置模仿學習 (Imitation Learning)...")

    config = {
        "model": {
            "architecture": "transformer",
            "hidden_dim": 256,
            "num_layers": 4,
            "num_heads": 8
        },
        "training": {
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
            "validation_split": 0.2
        },
        "data": {
            "expert_trades_path": "data/v2/experience/expert_trades.jsonl",
            "min_expert_rating": 4,  # 只使用 4-5 星評分的交易
            "augmentation": {
                "enabled": True,
                "noise_level": 0.05
            }
        }
    }

    config_file = Path("configs/imitation_learning.yaml")

    # 這裡應該使用 yaml.dump，為了簡化使用 json
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ 模仿學習配置保存到: {config_file}")
    print("📝 配置要點:")
    print(f"   - 模型架構: {config['model']['architecture']}")
    print(f"   - 學習率: {config['training']['learning_rate']}")
    print(f"   - 最小專家評分: {config['data']['min_expert_rating']}")

def setup_rlhf():
    """設置人類反饋強化學習"""
    print("\n🤝 設置 RLHF (Reinforcement Learning from Human Feedback)...")

    config = {
        "reward_model": {
            "architecture": "bradley_terry",
            "hidden_dim": 128,
            "comparison_pairs": 1000  # 最少需要的比較對數
        },
        "policy_training": {
            "algorithm": "PPO",
            "learning_rate": 0.0003,
            "clip_epsilon": 0.2,
            "value_coef": 0.5,
            "entropy_coef": 0.01
        },
        "data": {
            "feedback_path": "data/v2/experience/human_feedback.jsonl",
            "min_confidence": 0.7,  # 最小置信度閾值
            "balance_preferences": True
        },
        "safety": {
            "kl_penalty": 0.1,  # KL 散度懲罰
            "max_reward_scale": 5.0,
            "reward_clipping": True
        }
    }

    config_file = Path("configs/rlhf.yaml")

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ RLHF 配置保存到: {config_file}")
    print("📝 配置要點:")
    print(f"   - 獎勵模型: {config['reward_model']['architecture']}")
    print(f"   - 策略算法: {config['policy_training']['algorithm']}")
    print(f"   - KL 懲罰: {config['safety']['kl_penalty']}")

def setup_finrl_training():
    """設置 FinRL 離線訓練"""
    print("\n🏋️ 設置 FinRL 離線訓練環境...")

    config = {
        "environment": {
            "name": "P1TradingEnv",
            "market": "crypto",
            "assets": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            "lookback_window": 256,
            "leverage": 100
        },
        "algorithm": {
            "name": "SAC",  # Soft Actor-Critic
            "hyperparameters": {
                "learning_rate": 0.0003,
                "buffer_size": 1000000,
                "batch_size": 256,
                "tau": 0.005,
                "gamma": 0.99
            }
        },
        "training": {
            "total_timesteps": 1000000,
            "eval_episodes": 100,
            "checkpoint_frequency": 10000,
            "early_stopping": {
                "patience": 50000,
                "min_improvement": 0.01
            }
        },
        "data": {
            "historical_data_path": "data/historical/",
            "start_date": "2023-01-01",
            "end_date": "2024-12-31",
            "train_test_split": 0.8
        }
    }

    config_file = Path("configs/finrl_training.yaml")

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✅ FinRL 配置保存到: {config_file}")
    print("📝 配置要點:")
    print(f"   - 環境: {config['environment']['name']}")
    print(f"   - 算法: {config['algorithm']['name']}")
    print(f"   - 訓練步數: {config['training']['total_timesteps']:,}")

def create_training_scripts():
    """創建訓練腳本"""
    print("\n📜 創建訓練腳本...")

    scripts_dir = Path("scripts/v2_training")
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # 模仿學習腳本
    il_script = scripts_dir / "run_imitation_learning.py"
    with open(il_script, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""運行模仿學習訓練"""

from services.decision.learner.imitation import ImitationLearner
from pathlib import Path
import yaml

def main():
    print("🎓 開始模仿學習訓練...")

    # 加載配置
    with open("configs/imitation_learning.yaml") as f:
        config = yaml.safe_load(f)

    # 初始化學習器
    learner = ImitationLearner(config)

    # 開始訓練
    learner.train()

    print("✅ 模仿學習訓練完成")

if __name__ == "__main__":
    main()
''')

    # RLHF 腳本
    rlhf_script = scripts_dir / "run_rlhf.py"
    with open(rlhf_script, 'w') as f:
        f.write('''#!/usr/bin/env python3
"""運行 RLHF 訓練"""

from services.decision.learner.rl_trainer import RLTrainer
import yaml

def main():
    print("🤝 開始 RLHF 訓練...")

    with open("configs/rlhf.yaml") as f:
        config = yaml.safe_load(f)

    trainer = RLTrainer(config)
    trainer.train_with_human_feedback()

    print("✅ RLHF 訓練完成")

if __name__ == "__main__":
    main()
''')

    print(f"✅ 訓練腳本創建完成:")
    print(f"   - 模仿學習: {il_script}")
    print(f"   - RLHF: {rlhf_script}")

def main():
    """主設置流程"""
    print("🚀 P1-System v2 Learner/Trainer 設置")
    print("=" * 60)

    # 檢查先決條件
    print("🔍 檢查先決條件...")
    required_dirs = ["data", "configs", "scripts"]
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ 目錄結構就緒")

    # 設置各組件
    setup_experience_store()
    setup_imitation_learning()
    setup_rlhf()
    setup_finrl_training()
    create_training_scripts()

    print("\n" + "=" * 60)
    print("🎉 Learner/Trainer 設置完成！")
    print("\n📋 下一步操作:")
    print("1. 收集至少 100 筆專家交易數據")
    print("2. 運行模仿學習: python scripts/v2_training/run_imitation_learning.py")
    print("3. 收集人類偏好反饋")
    print("4. 運行 RLHF: python scripts/v2_training/run_rlhf.py")
    print("5. 設置 FinRL 歷史數據並開始離線訓練")
    print("\n💡 提示: 確保有足夠的計算資源 (GPU 推薦)")

if __name__ == "__main__":
    main()