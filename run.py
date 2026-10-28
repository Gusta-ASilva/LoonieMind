"""Inicialização local. Execute: python run.py"""
import argparse
import json
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen
import webbrowser

import uvicorn


def already_running(port):
    try:
        with urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1) as response:
            return json.load(response).get("aplicacao") == "LoonieMind"
    except (URLError, OSError, ValueError):
        return False


def open_when_ready(port):
    for _ in range(120):
        if already_running(port):
            webbrowser.open(f"http://127.0.0.1:{port}")
            return
        time.sleep(.25)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LoonieMind · Finanças com clareza")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if already_running(args.port):
        print(f"O LoonieMind já está aberto em http://127.0.0.1:{args.port}")
        if not args.no_browser:
            webbrowser.open(f"http://127.0.0.1:{args.port}")
        raise SystemExit(0)
    if not args.no_browser:
        threading.Thread(target=open_when_ready, args=(args.port,), daemon=True).start()
    uvicorn.run("looniemind.api:app", host="127.0.0.1", port=args.port, access_log=False)
