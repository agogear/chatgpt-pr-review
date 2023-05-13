from logging import basicConfig, getLevelName, info
from argparse import ArgumentParser


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--logging",
        default="warning",
        type=str,
        help="logging level",
        choices=["debug", "info", "warning", "error"],
    )
    args = parser.parse_args()

    basicConfig(encoding="utf-8", level=getLevelName(args.logging.upper()))

    info("ok")


if __name__ == "__main__":
    main()
