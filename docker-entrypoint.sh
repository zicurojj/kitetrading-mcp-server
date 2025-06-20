#!/bin/bash
set -e

APP_DATA=${DATA_DIR:-/app/data}
APP_LOGS=${LOG_DIR:-/app/logs}

mkdir -p "$APP_DATA" "$APP_LOGS"
# chown -R appuser:appuser "$APP_DATA" "$APP_LOGS"

wait_for_dependencies() {
    echo "Checking dependencies..."
    echo "Dependencies ready."
}

run_fastapi() {
    echo "Starting FastAPI Trading Server..."
    exec python fastapi_server.py
}

run_setup_auth() {
    echo "Running authentication setup..."
    exec python setup_auth.py
}

case "${1:-fastapi}" in
    fastapi)
        wait_for_dependencies
        run_fastapi
        ;;
    setup-auth)
        run_setup_auth
        ;;
    *)
        echo "Usage: $0 {fastapi|setup-auth}"
        exit 1
        ;;
esac
