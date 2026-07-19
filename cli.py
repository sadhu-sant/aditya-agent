#!/usr/bin/env python3
"""
Talk to Aditya directly from your terminal.

Usage:
    python cli.py                 # start chatting (session id = "local")
    python cli.py --session bob   # named session, persisted across runs
    python cli.py --new           # clear this session's history first
"""
import argparse

from aditya.agent import Aditya
from aditya.config import settings
from aditya.memory import clear_history, load_history, save_history


def main():
    parser = argparse.ArgumentParser(description="Chat with Aditya")
    parser.add_argument("--session", default="local", help="Session id (default: local)")
    parser.add_argument("--new", action="store_true", help="Clear existing history for this session")
    parser.add_argument("--no-tools", action="store_true", help="Disable tool use")
    args = parser.parse_args()

    if args.new:
        clear_history(args.session)

    agent = Aditya(use_tools=not args.no_tools)
    history = load_history(args.session)

    print(f"{settings.NAME} ready. Model: {settings.MODEL}  (session: {args.session})")
    print("Type 'exit' or Ctrl+C to quit.\n")

    while True:
        try:
            user_input = input("you> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbye!")
            break
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("bye!")
            break

        reply, history = agent.run(history, user_input)
        save_history(args.session, history)
        print(f"\n{settings.NAME}> {reply}\n")


if __name__ == "__main__":
    main()
