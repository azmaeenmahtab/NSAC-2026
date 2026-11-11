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

    if args.stage in ("cluster", "all"):
        logger.info("Executing cluster stage...")
        from pyroscope_pipeline.clustering.run import run_clustering

        cluster_summary = run_clustering()
        logger.info(f"Clustering complete: {cluster_summary}")

    if args.stage not in ("help", "ingest", "cluster", "all"):
        logger.info(f"Stage '{args.stage}' requested (placeholder until stage implementation).")


if __name__ == "__main__":
    main()
