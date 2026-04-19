import argparse
import sys

from .config import Args, get_config, reset_config
from .error import (
    ValidationError,
    validate_arg_range,
    validate_non_empty,
    validate_positive,
    validate_url,
)
from .tui import run


def _get_version() -> str:
    return "0.1.0"


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
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--reset", action="store_true", help="Reset configuration to defaults"
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {_get_version()}"
    )
    ns = parser.parse_args()
    return Args(
        model=ns.model,
        temperature=ns.temperature,
        max_tokens=ns.max_tokens,
        url=ns.url,
        debug=ns.debug,
        reset=ns.reset,
    )


def main() -> None:
    args = _parse_args()
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
    try:
        _validate_args(args)
    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    config = get_config(args=args)
    run(config)


if __name__ == "__main__":
    main()
