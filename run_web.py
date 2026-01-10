#!/usr/bin/env python3
"""
Запуск Web-UI для Load Orchestrator

Usage:
    python run_web.py
    python run_web.py --port 8080
"""

import argparse
from src.load_orchestrator.web.server import run_server


def main():
    parser = argparse.ArgumentParser(description="Run Load Orchestrator Web UI")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on (default: 8080)")
    parser.add_argument("--config", type=str, help="Path to config file (optional)")

    args = parser.parse_args()

    print(f"Starting Load Orchestrator Web UI on http://localhost:{args.port}")
    print("Press Ctrl+C to stop")

    run_server(port=args.port, config_path=args.config)


if __name__ == "__main__":
    main()