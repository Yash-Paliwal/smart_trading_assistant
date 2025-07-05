#!/bin/bash

# Setup script for Radar Scanner Testing Environment
echo "🔧 Setting up Radar Scanner Testing Environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "📚 Installing required packages..."
pip install pandas numpy pandas-ta python-decouple websocket-client protobuf requests

# Install additional packages for testing
echo "🧪 Installing testing packages..."
pip install matplotlib seaborn

# Note: tkinter is built into Python, no need to install via pip
echo "ℹ️  tkinter is built into Python - no installation needed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p test_reports
mkdir -p test_scenarios

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "✅ Setup complete! Virtual environment is activated."
echo ""
echo "🎯 Next steps:"
echo "1. Run quick tests: python quick_test_runner.py"
echo "2. Launch dashboard: python development_dashboard.py"
echo "3. Run comprehensive tests: python scanner_tester.py"
echo ""
echo "💡 Remember to always activate the virtual environment first:"
echo "   source venv/bin/activate" 