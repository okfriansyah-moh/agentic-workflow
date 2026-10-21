"""JSON command line interface for the portable workflow."""
import argparse
import importlib
import json
import sys
import subprocess

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agent-workflow")
    parser.add_argument("--version", action="version", version=f"agent-workflow {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    requested = list(argv) if argv is not None else sys.argv[1:]
    modules = ("resources",) if requested[:1] == ["resources"] else ("installer", "coordination", "gates", "skill_resolution", "tools", "host_verification", "resources")
    try:
        for name in modules:
            importlib.import_module(f"agent_workflow.{name}").register(commands)
    except ImportError:
        print(json.dumps({"status": "blocked", "reason": "Selected platform lacks required workflow runtime support; no workload launched. Use resources for capacity diagnostics."}))
        return 1
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
