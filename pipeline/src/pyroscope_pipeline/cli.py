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

    if args.stage in ("aggregate", "all"):
        logger.info("Executing aggregate stage...")
        from pyroscope_pipeline.aggregate.run import run_aggregation

        agg_summary = run_aggregation()
        logger.info(f"Aggregation complete: {agg_summary}")

    if args.stage in ("harmonize", "all"):
        logger.info("Executing harmonize stage...")
        from pyroscope_pipeline.harmonize.run import run_harmonization

        harm_summary = run_harmonization()
        logger.info(f"Harmonization complete: {harm_summary}")

    if args.stage in ("stats", "all"):
        logger.info("Executing stats stage...")
        from pyroscope_pipeline.stats.run import run_stats

        stats_summary = run_stats()
        logger.info(f"Stats assembly complete: {stats_summary}")


if __name__ == "__main__":
    main()
