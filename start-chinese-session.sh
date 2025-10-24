#!/bin/zsh

# start-chinese-session.sh - Chinese Syntax Analyzer + Grammar DB session

CHINESE_ROOT="/home/zaya/Downloads/Zayas/ZayasTransliteration"
GRAMMAR_ROOT="/home/zaya/Downloads/Zayas/zayas-grammar-db"

echo "Starting Chinese Syntax Analyzer + Grammar DB session..."
echo "Chinese root: $CHINESE_ROOT"
echo "Grammar root: $GRAMMAR_ROOT"

# Check directories
[[ ! -d "$CHINESE_ROOT" ]] && { echo "Error: Chinese directory not found"; exit 1 }
[[ ! -d "$GRAMMAR_ROOT" ]] && { echo "Error: Grammar DB directory not found"; exit 1 }

# Kill existing session if it exists
if tmux has-session -t chinese-session 2>/dev/null; then
    echo "🔄 Killing existing session 'chinese-session'..."
    tmux kill-session -t chinese-session
    sleep 2
fi

# Kill any processes using our ports
echo "🔄 Cleaning up any existing processes on ports 8000 and 5173..."
pkill -f "uvicorn main:app" || true
pkill -f "npm run dev" || true
sleep 2

# Create new tmux session with first pane
echo "🚀 Creating tmux session with 4 splits..."
tmux new-session -d -s chinese-session -c "$CHINESE_ROOT" -n "Chinese-Analyzer"

# Split the window into 4 panes
tmux split-window -v -c "$GRAMMAR_ROOT"
tmux select-pane -t 0
tmux split-window -h -c "$GRAMMAR_ROOT"
tmux select-pane -t 2
tmux split-window -h -c "$GRAMMAR_ROOT"

# Now we have:
# Pane 0: Top-left (Chinese)
# Pane 1: Top-right (Grammar DB - Database)
# Pane 2: Bottom-left (Grammar DB - Backend) 
# Pane 3: Bottom-right (Grammar DB - Frontend)

# Start Chinese Syntax Analyzer in pane 0
echo "🔤 Starting Chinese Syntax Analyzer..."
tmux send-keys -t chinese-session:0.0 "cd $CHINESE_ROOT/transliteration" Enter
sleep 1
tmux send-keys -t chinese-session:0.0 "echo '=== Starting Chinese Syntax Analyzer ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.0 "pipenv run python3 -m web.webChineseColor-coded" Enter

# Start Grammar DB services in the other panes
echo "📚 Starting Grammar DB services..."

# Pane 1: Database only
echo "🐘 Starting Database..."
tmux send-keys -t chinese-session:0.1 "echo '=== Starting Grammar DB Database ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.1 "cd backend" Enter
sleep 1
tmux send-keys -t chinese-session:0.1 "sudo docker-compose down" Enter
sleep 2
tmux send-keys -t chinese-session:0.1 "sudo docker-compose up -d" Enter
sleep 2
tmux send-keys -t chinese-session:0.1 "echo 'Database running. Waiting for backend...'" Enter

# Pane 2: Backend API only
echo "🚀 Starting Backend API..."
sleep 8  # Wait longer for database to be ready
tmux send-keys -t chinese-session:0.2 "echo '=== Starting Grammar DB Backend ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "cd backend" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "echo 'Checking if port 8000 is free...'" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "lsof -ti:8000 | xargs kill -9 2>/dev/null || true" Enter
sleep 2
tmux send-keys -t chinese-session:0.2 "pipenv run uvicorn main:app --reload --port 8000" Enter

# Pane 3: Frontend
echo "💻 Starting Frontend..."
tmux send-keys -t chinese-session:0.3 "echo '=== Grammar DB Frontend ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.3 "cd frontend" Enter
sleep 1
tmux send-keys -t chinese-session:0.3 "echo 'Checking if port 5173 is free...'" Enter
sleep 1
tmux send-keys -t chinese-session:0.3 "lsof -ti:5173 | xargs kill -9 2>/dev/null || true" Enter
sleep 2
tmux send-keys -t chinese-session:0.3 "npm run dev -- --port 5173" Enter

# Arrange panes in a nice layout (2x2 grid)
tmux select-layout -t chinese-session:0 tiled

# Set pane titles
tmux set -p -t chinese-session:0.0 pane-border-status top
tmux set -p -t chinese-session:0.0 pane-border-format " Chinese Syntax Analyzer "
tmux set -p -t chinese-session:0.1 pane-border-status top  
tmux set -p -t chinese-session:0.1 pane-border-format " Grammar DB - Database "
tmux set -p -t chinese-session:0.2 pane-border-status top
tmux set -p -t chinese-session:0.2 pane-border-format " Grammar DB - Backend API "
tmux set -p -t chinese-session:0.3 pane-border-status top
tmux set -p -t chinese-session:0.3 pane-border-format " Grammar DB - Frontend "

echo ""
echo "✅ Session created successfully!"
echo ""
echo "📊 Layout:"
echo "   ┌─────────────────┬─────────────────┐"
echo "   │ Chinese Syntax  │ Grammar DB      │"
echo "   │ Analyzer        │ (Database)      │"
echo "   ├─────────────────┼─────────────────┤"
echo "   │ Grammar DB      │ Grammar DB      │"
echo "   │ (Backend API)   │ (Frontend)      │"
echo "   └─────────────────┴─────────────────┘"
echo ""
echo "🎮 TMUX Controls:"
echo "   - Switch panes:    Ctrl+a, then arrow keys"
echo "   - Detach:          Ctrl+a, d"
echo "   - Zoom pane:       Ctrl+a, m"
echo "   - Resize:          Ctrl+a, then h/j/k/l"
echo ""
echo "🌐 Services:"
echo "   - Chinese Analyzer: Check pane 0 for URL"
echo "   - Grammar Backend:  http://localhost:8000/docs"
echo "   - Grammar Frontend: http://localhost:5173"
echo ""

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 12

# Attach to the session
echo "Attaching to session..."
tmux attach -t chinese-session