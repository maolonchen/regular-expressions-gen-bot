#!/bin/bash

# LDPAS Service Management Script
# Manage start, stop, restart and status of the application

RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
PID_FILE="$PROJECT_DIR/app.pid"
LOG_FILE="$PROJECT_DIR/logs/app.log"

mkdir -p "$PROJECT_DIR/logs"

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_message $RED "Error: virtual environment not found. Run 'setup' first."
        exit 1
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

setup() {
    print_message $BLUE "Setting up project environment..."

    if [ ! -d "$VENV_DIR" ]; then
        print_message $BLUE "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        if [ $? -ne 0 ]; then
            print_message $RED "Error: failed to create virtual environment"
            exit 1
        fi
    fi

    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip

    print_message $BLUE "Installing dependencies..."
    if [ -f "$PROJECT_DIR/uv.lock" ]; then
        if command -v uv >/dev/null 2>&1; then
            uv sync
        else
            pip install uv && uv sync
        fi
    elif [ -f "$PROJECT_DIR/requirements.txt" ]; then
        pip install -r "$PROJECT_DIR/requirements.txt"
    else
        pip install -e .
    fi

    print_message $GREEN "Setup complete!"
}

start() {
    if is_running; then
        print_message $YELLOW "Service is already running"
        return 1
    fi

    print_message $BLUE "Starting LDPAS service..."

    check_venv
    source "$VENV_DIR/bin/activate"

    nohup python "$PROJECT_DIR/run_server.py" > "$LOG_FILE" 2>&1 &
    local pid=$!

    sleep 3

    if ps -p $pid > /dev/null 2>&1; then
        echo $pid > "$PID_FILE"
        print_message $GREEN "Service started, PID: $pid"
        print_message $GREEN "Endpoint: http://localhost:8765"
        return 0
    else
        print_message $RED "Failed to start. Check logs: $LOG_FILE"
        return 1
    fi
}

stop() {
    if ! is_running; then
        print_message $YELLOW "Service is not running"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    print_message $BLUE "Stopping service (PID: $pid)..."

    kill $pid
    sleep 2

    if ps -p $pid > /dev/null 2>&1; then
        print_message $YELLOW "Process did not stop gracefully, force killing..."
        kill -9 $pid
    fi

    rm -f "$PID_FILE"
    print_message $GREEN "Service stopped"
}

restart() {
    print_message $BLUE "Restarting service..."
    stop
    sleep 2
    start
}

status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_message $GREEN "Service is running, PID: $pid"

        if command -v curl >/dev/null 2>&1; then
            local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/health 2>/dev/null)
            if [ "$response" = "200" ]; then
                print_message $GREEN "Health check: OK (HTTP 200)"
            else
                print_message $YELLOW "Health check: abnormal (HTTP $response)"
            fi
        fi
    else
        print_message $RED "Service is not running"
    fi
}

logs() {
    if [ -f "$LOG_FILE" ]; then
        print_message $BLUE "Application logs (Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        print_message $YELLOW "Log file not found: $LOG_FILE"
    fi
}

clean_logs() {
    if [ -f "$LOG_FILE" ]; then
        rm -f "$LOG_FILE"
        print_message $GREEN "Log file cleaned"
    else
        print_message $YELLOW "Log file not found: $LOG_FILE"
    fi
}

show_help() {
    echo "LDPAS Service Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  setup     - Setup project environment"
    echo "  start     - Start the service"
    echo "  stop      - Stop the service"
    echo "  restart   - Restart the service"
    echo "  status    - Check service status"
    echo "  logs      - Tail application logs"
    echo "  clean     - Remove log files"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup    # First-time setup"
    echo "  $0 start    # Start service"
    echo "  $0 status   # Check status"
    echo "  $0 logs     # View logs"
}

main() {
    local command=$1

    case $command in
        setup)   setup ;;
        start)   start ;;
        stop)    stop ;;
        restart) restart ;;
        status)  status ;;
        logs)    logs ;;
        clean)   clean_logs ;;
        help|--help|-h) show_help ;;
        "")      show_help ;;
        *)
            print_message $RED "Unknown command: $command"
            print_message $YELLOW "Use $0 help to see available commands"
            exit 1
            ;;
    esac
}

main "$@"
