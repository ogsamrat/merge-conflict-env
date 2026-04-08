"""Utility functions for data processing."""

from typing import Callable, List, Optional


def process_items(
    data: List[str],
    predicate: Optional[Callable[[str], bool]] = None,
) -> List[str]:
    """Process a list of string items with an optional predicate filter.

    Args:
        data: List of string items to process.
        predicate: Optional predicate function to filter items.

    Returns:
        List of cleaned, non-empty string items.
    """
    if predicate:
        data = [item for item in data if predicate(item)]

    results: List[str] = []
    for item in data:
        cleaned = item.strip().lower()
        if cleaned:
            results.append(cleaned)
    return results


def format_output(data: List[str], separator: str = ", ") -> str:
    """Format items into a single string."""
    return separator.join(str(item) for item in data)


def search_items(data: List[str], query: str) -> List[str]:
    """Search for items matching a query string.

    Args:
        data: List of items to search through.
        query: Search query string.

    Returns:
        List of items containing the query.
    """
    query_lower = query.strip().lower()
    return [item for item in data if query_lower in item.strip().lower()]
