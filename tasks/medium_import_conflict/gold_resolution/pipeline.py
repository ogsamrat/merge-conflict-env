"""Batch processing pipeline."""

import logging

from processor import DataProcessor

logging.basicConfig(level=logging.WARNING)


def run_pipeline(texts: list) -> list:
    """Process a batch of texts, skipping invalid inputs and logging errors."""
    dp = DataProcessor()
    results = []
    for t in texts:
        if not dp.validate(t):
            logging.warning("Skipping invalid input: %r", t)
            continue
        try:
            results.append(dp.process(t))
        except Exception as exc:
            logging.warning("Error processing %r: %s", t, exc)
    return results


def filter_valid(texts: list) -> list:
    """Return only texts that pass DataProcessor.validate()."""
    dp = DataProcessor()
    return [t for t in texts if dp.validate(t)]
