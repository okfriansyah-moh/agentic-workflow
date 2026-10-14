"""JSON command line interface for the portable workflow."""
import argparse
import importlib
import json
import sys
import subprocess


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agent-workflow")
    parser.add_argument("--version", action="version", version="agent-workflow 1.0.0")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("installer", "coordination", "gates"):
        importlib.import_module(f"agent_workflow.{name}").register(commands)
    args = parser.parse_args(argv)
    try:
        result = args.handler(args)
        if result is not None:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        if isinstance(result, dict):
            return int(result.get("status") in {"error", "blocked", "failed", "conflict"})
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "error", "error": str(error)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
