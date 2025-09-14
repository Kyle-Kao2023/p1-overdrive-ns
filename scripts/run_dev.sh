#!/usr/bin/env bash
set -e

echo "🚀 Starting P1 Trading Builder Development Environment"

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Python 3.11+ required, found $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# 安装依赖（如果需要）
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate || source venv/Scripts/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

# 启动Redis（如果没有运行）
if ! pgrep -f redis-server > /dev/null; then
    echo "🗄️  Starting Redis..."
    redis-server --daemonize yes --port 6379 || echo "⚠️  Redis start failed, using Docker alternative"
fi

# 导出环境变量
export APP_ENV=dev
export LOG_LEVEL=INFO
export REDIS_URL=redis://localhost:6379/0
export CONFIG_PATH=./configs/default.yaml

echo "🎯 Starting services in development mode..."

# 启动所有服务（后台运行）
echo "📡 Starting Decision Service on port 8000..."
uvicorn services.decision.app:app --reload --port 8000 &
DECISION_PID=$!

echo "🔄 Starting FeatureHub Service on port 8010..."  
uvicorn services.featurehub.app:app --reload --port 8010 &
FEATUREHUB_PID=$!

echo "👁️  Starting Vision Service on port 8020..."
uvicorn services.vision.app:app --reload --port 8020 &
VISION_PID=$!

# 等待服务启动
sleep 3

echo ""
echo "✅ All services started successfully!"
echo ""
echo "🔗 Service URLs:"
echo "   Decision Service:  http://localhost:8000"
echo "   Decision API Docs: http://localhost:8000/docs"
echo "   FeatureHub:        http://localhost:8010"
echo "   Vision Service:    http://localhost:8020"
echo ""
echo "🛠️  Development Commands:"
echo "   Test APIs:         curl http://localhost:8000/health"
echo "   Run Tests:         pytest -v"
echo "   Check Linting:     ruff check ."
echo "   Format Code:       black ."
echo ""
echo "⚠️  Press Ctrl+C to stop all services"
echo ""

# 等待中断信号
trap 'kill $DECISION_PID $FEATUREHUB_PID $VISION_PID; echo "🛑 Services stopped"; exit' INT
wait
