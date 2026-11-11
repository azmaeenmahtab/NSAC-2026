"""PyroScope pipeline command-line interface."""

import argparse
import sys

from pyroscope_pipeline.common.logging import get_logger

logger = get_logger("cli")


def main() -> None:
    parser = argparse.ArgumentParser(description="PyroScope Fire Data Pipeline CLI")
    parser.add_argument(
        "stage",
        nargs="?",
        default="help",
        choices=["help", "ingest", "cluster", "aggregate", "harmonize", "stats", "all"],
        help="Pipeline stage to execute",
    )
    args = parser.parse_args()

    if args.stage == "help":
        parser.print_help()
        sys.exit(0)

    if args.stage in ("ingest", "all"):
        logger.info("Executing ingest stage...")
        from pyroscope_pipeline.ingest.run import run_ingest

        stats = run_ingest()
        logger.info(f"Ingest complete: {stats}")

    if args.stage not in ("help", "ingest", "all"):
        logger.info(f"Stage '{args.stage}' requested (placeholder until stage implementation).")


if __name__ == "__main__":
    main()
