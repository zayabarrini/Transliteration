#!/bin/bash

# Deployment script for Transliteration Tools

echo "🚀 Deploying Transliteration Tools..."

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Setting up virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p uploads processed static/downloads

# Set up environment variables
if [ ! -f .env ]; then
    cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(16))")
UPLOAD_FOLDER=uploads
PROCESSED_FOLDER=processed
MAX_CONTENT_LENGTH=16777216
EOF
    echo "🔑 Created .env file with secret key"
fi

# Test the application
echo "🧪 Testing application..."
python -c "from app import app; print('✅ Application imports successfully')"

echo "🎉 Deployment setup complete!"
echo "📝 To run the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "🐳 Or using Docker:"
echo "   docker-compose up --build"