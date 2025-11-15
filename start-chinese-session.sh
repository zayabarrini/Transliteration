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
echo "🚀 Creating tmux session with 5 splits..."
tmux new-session -d -s chinese-session -c "$CHINESE_ROOT" -n "Chinese-Analyzer"

# Split the window into 5 panes (3 rows, 2 columns - with one large pane)
# First split: horizontal bottom for Grammar DB
tmux split-window -v -c "$GRAMMAR_ROOT"
# Second split: horizontal top-right for Chinese reserved
tmux select-pane -t 0
tmux split-window -h -c "$CHINESE_ROOT"
# Third split: horizontal bottom-left for Grammar DB split
tmux select-pane -t 2
tmux split-window -h -c "$GRAMMAR_ROOT"
# Fourth split: horizontal bottom-right for web translators
tmux select-pane -t 3
tmux split-window -h -c "$CHINESE_ROOT"
# Fifth split: one more for the second web translator
tmux select-pane -t 4
tmux split-window -h -c "$CHINESE_ROOT"

# Now we have:
# Pane 0: Top-left (Chinese Syntax Analyzer)
# Pane 1: Top-right (Grammar DB - Database)
# Pane 2: Middle-left (Grammar DB - Backend API) 
# Pane 3: Middle-right (Grammar DB - Frontend)
# Pane 4: Bottom-left (Web Translator 1)
# Pane 5: Bottom-right (Web Translator 2)

# Start Chinese Syntax Analyzer in pane 0
echo "🔤 Starting Chinese Syntax Analyzer..."
tmux send-keys -t chinese-session:0.0 "cd $CHINESE_ROOT/transliteration" Enter
sleep 1
tmux send-keys -t chinese-session:0.0 "echo '=== Starting Chinese Syntax Analyzer ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.0 "pipenv run python3 -m web.webChineseColor-coded" Enter

# Start Grammar DB services in panes 1, 2, and 3
echo "📚 Starting Grammar DB services..."

# Pane 1: Database only
echo "🐘 Starting Database..."
tmux send-keys -t chinese-session:0.1 "echo '=== Starting Grammar DB Database ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.1 "cd backend" Enter
sleep 1
tmux send-keys -t chinese-session:0.1 "docker-compose down" Enter
sleep 3
tmux send-keys -t chinese-session:0.1 "docker-compose up -d" Enter
sleep 5
tmux send-keys -t chinese-session:0.1 "echo 'Waiting for database to be ready...'" Enter
sleep 1
tmux send-keys -t chinese-session:0.1 "while ! docker-compose exec db pg_isready -U postgres; do sleep 2; done" Enter
sleep 2
tmux send-keys -t chinese-session:0.1 "echo '✅ Database is ready!'" Enter

# Pane 2: Backend API only
echo "🚀 Starting Backend API..."
sleep 15  # Wait much longer for database to be fully ready
tmux send-keys -t chinese-session:0.2 "echo '=== Starting Grammar DB Backend ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "cd backend" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "echo 'Checking if port 8000 is free...'" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "lsof -ti:8000 | xargs kill -9 2>/dev/null || true" Enter
sleep 2
tmux send-keys -t chinese-session:0.2 "echo 'Testing database connection...'" Enter
sleep 1
tmux send-keys -t chinese-session:0.2 "pipenv run python -c \"from main import engine; engine.connect(); print('✅ Database connection successful')\"" Enter
sleep 3
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

# New panes for web translators
echo "🌐 Starting Web Translators..."

# Pane 4: Web Translator 1
echo "🔤 Starting Web Translator..."
tmux send-keys -t chinese-session:0.4 "cd $CHINESE_ROOT/transliteration" Enter
sleep 1
tmux send-keys -t chinese-session:0.4 "echo '=== Starting Web Translator ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.4 "pipenv run python3 -m web.webTransliterator" Enter

# Pane 5: Web Translator 2 Language
echo "🔤 Starting Web Translator 2 Language..."
tmux send-keys -t chinese-session:0.5 "cd $CHINESE_ROOT/transliteration" Enter
sleep 1
tmux send-keys -t chinese-session:0.5 "echo '=== Starting Web Translator 2 Language ==='" Enter
sleep 1
tmux send-keys -t chinese-session:0.5 "pipenv run python3 -m web.webTranslator2Language" Enter

# Arrange panes in a nice layout
tmux select-layout -t chinese-session:0 tiled

# Set pane titles (only for panes that exist: 0-5)
tmux set -p -t chinese-session:0.0 pane-border-status top
tmux set -p -t chinese-session:0.0 pane-border-format " Chinese Syntax Analyzer "
tmux set -p -t chinese-session:0.1 pane-border-status top  
tmux set -p -t chinese-session:0.1 pane-border-format " Grammar DB - Database "
tmux set -p -t chinese-session:0.2 pane-border-status top
tmux set -p -t chinese-session:0.2 pane-border-format " Grammar DB - Backend API "
tmux set -p -t chinese-session:0.3 pane-border-status top
tmux set -p -t chinese-session:0.3 pane-border-format " Grammar DB - Frontend "
tmux set -p -t chinese-session:0.4 pane-border-status top
tmux set -p -t chinese-session:0.4 pane-border-format " Web Translator "
tmux set -p -t chinese-session:0.5 pane-border-status top
tmux set -p -t chinese-session:0.5 pane-border-format " Web Translator 2 Language "

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
echo "   ├─────────────────┼─────────────────┤"
echo "   │ Web Translator  │ Web Translator  │"
echo "   │                 │ 2 Language      │"
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
echo "   - Web Translators:  Check panes 4-5 for URLs"
echo ""

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 20

# Attach to the session
echo "Attaching to session..."
tmux attach -t chinese-session