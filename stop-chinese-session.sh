#!/bin/zsh

echo "🛑 Stopping Chinese Syntax Analyzer + Grammar DB session..."

# Kill the tmux session
tmux kill-session -t chinese-session 2>/dev/null && echo "✅ Tmux session stopped"

# Stop any remaining processes
pkill -f "uvicorn main:app" 2>/dev/null && echo "✅ Backend stopped"
pkill -f "npm run dev" 2>/dev/null && echo "✅ Frontend stopped"
pkill -f "python3 -m web.webChineseColor-coded" 2>/dev/null && echo "✅ Chinese Analyzer stopped"

# Stop docker containers
cd /home/zaya/Downloads/Zayas/zayas-grammar-db/backend
docker-compose down 2>/dev/null && echo "✅ Database stopped"

echo "🎯 All services stopped successfully!"