#!/bin/bash
echo ""
echo "🚀 AI IMAGE MATCHING ENGINE"
echo "=============================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating..."
source venv/bin/activate

echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

echo ""
echo "=============================="
echo "✅ STARTING APPLICATION"
echo "=============================="
echo ""
echo "🌐 Open browser: http://localhost:8000"
echo ""
echo "Features:"
echo "  ✅ Upload images with AI vision"
echo "  ✅ Create blog posts"
echo "  ✅ Match images to posts"
echo "  ✅ Guard logic (refuses wrong matches)"
echo "  ✅ Evaluation metrics"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python src/main.py
