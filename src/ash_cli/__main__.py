from .config import get_config
from .tui import run


def main() -> None:
    config = get_config()
    run(config)


if __name__ == "__main__":
    main()
