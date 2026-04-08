"""Main module for MyProject."""

from utils import process_items, format_output, search_items


def run_pipeline(raw_data: list[str]) -> str:
    """Run the full processing pipeline."""
    processed = process_items(data=raw_data)
    return format_output(data=processed)


def run_search(raw_data: list[str], query: str) -> str:
    """Search through processed data."""
    processed = process_items(data=raw_data)
    matches = search_items(data=processed, query=query)
    return format_output(data=matches)


if __name__ == "__main__":
    data = ["  Hello ", "World  ", "  ", "Python", "Hello World"]
    print(run_pipeline(data))
    print("Search results:", run_search(data, "hello"))
