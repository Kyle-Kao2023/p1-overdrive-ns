# Changelog

All notable changes to P1 Trading Builder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-09-14

### Added
- 🎯 **Initial Release** - P1 Overdrive-NS Trading Decision System
- 🔒 **4-Gate Safety System**
  - Vol Sweet-Spot Gate (Bull/Bear volatility bands)
  - Consensus Gate (C_align, C_of, C_vision, Pine_match)
  - Liq-Buffer Gate (Risk budget vs liquidation buffer)
  - Event & Latency Gate (Blacklist events, SLA monitoring)
- 🧠 **Decision Engine**
  - CTFG 12-node Loopy-BP model (stub implementation)
  - Chain reasoning with evidence aggregation
  - Fragility testing and robustness validation
  - Real-time risk assessment
- 📊 **MPC Exit Strategy**
  - Hazard rate detection with simplified BOCPD
  - Dynamic exit decisions (hold/reduce/close/trail)
  - OrderFlow flip detection
  - Position timeout monitoring
- 🚀 **Microservices Architecture**
  - Decision Service (FastAPI, port 8000)
  - FeatureHub Service (Feature aggregation, port 8010)
  - Vision Service (YOLO pattern detection stub, port 8020)
- 🔌 **Trading Platform Adapters**
  - Freqtrade ExternalDecisionStrategy
  - Vedanta enter/exit adapters
- 🧪 **Comprehensive Testing**
  - Unit tests for all Gate logic
  - API integration tests
  - Hazard detection and MPC exit tests
  - Performance and latency tests
- 🐳 **DevOps & Infrastructure**
  - Docker Compose for local development
  - CI/CD pipeline with GitHub Actions
  - Pre-commit hooks (black, isort, ruff, mypy)
  - Health checks and monitoring endpoints
- 📚 **Documentation**
  - Complete API documentation with OpenAPI
  - Detailed README with quick start guide
  - Product Requirements Document (PRD)
  - Contributing guidelines

### Technical Specifications
- **Latency SLA**: <70ms for decision API (p95)
- **Target Precision**: 95% (MAE ≤ 0.6%)
- **Hit Rate**: 75% @ 1% target
- **Risk Management**: Conformal prediction calibration
- **Scalability**: Microservices with Redis backend

### Models (Stub Implementation)
- ✅ CTFG 12-node factor graph (simplified weighted combination)
- ✅ Quantile prediction (volatility and market-based estimation)
- ✅ Conformal calibration (basic threshold adjustment)
- ✅ BOCPD hazard detection (statistical change point detection)

### Supported Features
- 📈 Multi-timeframe Z-score alignment
- 📊 OrderFlow analysis (OBI, dCVD, replenish rate)
- 👁️ Vision pattern recognition (stub)
- ⛓️ On-chain metrics (OI ROC, Gas Z-score)
- 🎯 TradingView Pine Script integration
- 🔄 Real-time market snapshots

### API Endpoints
#### Decision Service
- `POST /decide/enter` - Entry decision with full reasoning chain
- `POST /decide/exit` - Exit decision with MPC strategy
- `GET /health` - Service health check
- `GET /status` - Detailed system status
- `GET /metrics` - Performance metrics

#### FeatureHub Service  
- `GET /snapshot` - Market snapshot generation
- `POST /tv/webhook` - TradingView Pine webhook
- `POST /vision/tokens` - Vision detection results

#### Vision Service
- `POST /detect` - Image pattern detection (stub)

### Configuration
- 📝 YAML-based configuration system
- 🔧 Environment variable support
- ⚙️ Gate threshold customization
- 🎛️ Risk parameter tuning

### Safety Features
- 🛡️ Input validation with Pydantic v2
- ⏰ API timeout protection
- 🚫 Blacklist event blocking
- 📊 Real-time performance monitoring
- 🔒 Liquidation buffer validation

---

### Legend
- 🎯 Core Features
- 🔒 Safety & Risk Management  
- 🧠 AI/ML Models
- 📊 Analytics & Monitoring
- 🚀 Performance & Infrastructure
- 🔌 Integrations
- 🧪 Testing & Quality
- 📚 Documentation
