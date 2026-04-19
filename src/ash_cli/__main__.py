import argparse

from .config import Args, get_config
from .tui import run


def _get_version() -> str:
    return "0.1.0"


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
        "--version", action="version", version=f"%(prog)s {_get_version()}"
    )
    ns = parser.parse_args()
    return Args(
        model=ns.model,
        temperature=ns.temperature,
        max_tokens=ns.max_tokens,
        url=ns.url,
        debug=ns.debug,
    )


def main() -> None:
    args = _parse_args()
    config = get_config(args=args)
    run(config)


if __name__ == "__main__":
    main()
