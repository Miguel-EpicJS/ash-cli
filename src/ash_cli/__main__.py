import argparse
import sys
from pathlib import Path

from . import __version__
from .completions import get_bash_completion, get_zsh_completion
from .config import Args, get_available_models, get_config, reset_config
from .error import (
    ValidationError,
    validate_arg_range,
    validate_non_empty,
    validate_positive,
    validate_url,
)
from .session import (
    export_session,
    import_session,
    list_sessions,
    load_session,
    rename_session,
)
from .tui import run





def _validate_args(args: Args) -> None:
    if args.model is not None:
        validate_non_empty(args.model, "--model")
    if args.temperature is not None:
        validate_arg_range(args.temperature, 0.0, 2.0, "--temp")
    if args.max_tokens is not None:
        validate_positive(args.max_tokens, "--max-tokens")
    if args.url is not None:
        validate_url(args.url, "--url")


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(
        prog="ash-cli", description="AI CLI assistant that outputs bash commands"
    )
    parser.add_argument("--model", type=str, help="Model ID to use")
    parser.add_argument(
        "--temp", type=float, dest="temperature", help="Sampling temperature"
    )
    parser.add_argument("--max-tokens", type=int, help="Maximum tokens to generate")
    parser.add_argument("--url", type=str, help="Model API base URL")
    parser.add_argument("-v", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--reset", action="store_true", help="Reset configuration to defaults"
    )
    parser.add_argument("--session", type=str, help="Session ID to load")
    parser.add_argument(
        "--sessions",
        action="store_true",
        dest="list_sessions",
        help="List all sessions",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models",
    )
    parser.add_argument(
        "--export", type=str, dest="export_session", help="Export session to file"
    )
    parser.add_argument(
        "--import", type=str, dest="import_session", help="Import session from file"
    )
    parser.add_argument(
        "--rename", type=str, dest="rename_session", help="Rename session (session_id)"
    )
    parser.add_argument(
        "--completions",
        choices=["bash", "zsh"],
        help="Generate shell completions",
    )
    parser.add_argument(
        "--version", action="version", version=f"ash-cli {__version__}"
    )
    ns = parser.parse_args()
    return Args(
        model=ns.model,
        temperature=ns.temperature,
        max_tokens=ns.max_tokens,
        url=ns.url,
        debug=ns.debug,
        reset=ns.reset,
        session=ns.session,
        list_sessions=ns.list_sessions,
        list_models=ns.list_models,
        export_session=ns.export_session,
        import_session=ns.import_session,
        rename_session=ns.rename_session,
        completions=ns.completions,
    )


def _handle_session_args(args: Args) -> bool:
    if args.list_sessions:
        sessions = list_sessions()
        if not sessions:
            print("No sessions found.")
            return True
        for s in sessions:
            print(f"{s.id} | {s.name} | {s.created_at[:10]}")
        return True
    if args.export_session:
        parts = args.export_session.split(":", 1)
        if len(parts) != 2:
            print("Error: Use --export session_id:path/to/file.json")
            return True
        session_id, file_path = parts
        if export_session(session_id, Path(file_path)):
            print(f"Exported session {session_id} to {file_path}")
        else:
            print(f"Session {session_id} not found.")
        return True
    if args.import_session:
        path = Path(args.import_session)
        if import_session(path):
            print(f"Imported session from {path}")
        else:
            print(f"Failed to import from {path}")
        return True
    if args.rename_session:
        parts = args.rename_session.split(":", 1)
        if len(parts) != 2:
            print("Error: Use --rename session_id:new_name")
            return True
        session_id, new_name = parts
        session = rename_session(session_id, new_name)
        if session:
            print(f"Renamed session to {new_name}")
        else:
            print(f"Session {session_id} not found.")
        return True
    return False


def main() -> None:
    args = _parse_args()
    if args.list_models:
        models = get_available_models()
        for model_id, preset in models.items():
            base_url = preset.get("base_url", "N/A")
            print(f"{model_id} | {base_url}")
        return
    if args.completions:
        if args.completions == "bash":
            print(get_bash_completion())
        elif args.completions == "zsh":
            print(get_zsh_completion())
        return
    if args.reset:
        response = input("Are you sure you want to reset config? [y/N]: ")
        if response.lower() == "y":
            removed = reset_config()
            if removed:
                print(f"Removed: {', '.join(str(p) for p in removed)}")
            else:
                print("No config files found to remove.")
        else:
            print("Reset cancelled.")
        return
    if _handle_session_args(args):
        return
    try:
        _validate_args(args)
    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    config = get_config(args=args)
    session = None
    if args.session:
        session = load_session(args.session)
        if session:
            print(f"Loaded session: {session.name}")
        else:
            print(f"Session {args.session} not found.")
            sys.exit(1)
    run(config, session=session)


if __name__ == "__main__":
    main()
