from argparse import ArgumentParser

from . import __version__
from .hello import HelloClass, say_hello_lots

__all__ = ["main"]


def main(args=None):
    parser = ArgumentParser()
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("name", help="Name of the person to greet")
    parser.add_argument("--times", type=int, default=5, help="Number of times to greet")
    args = parser.parse_args(args)
    say_hello_lots(HelloClass(args.name), args.times)


# test with: python -m gphotos_sync
if __name__ == "__main__":
    main()
