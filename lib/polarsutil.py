"""utilities for reading data from polars."""

# pylint: disable=invalid-name, line-too-long

from typing import Optional, Dict, Tuple, Any, List, Union
# from collections import Counter, defaultdict
import polars as pl
import pandas as pd
import logging
import time
# from tqdm.autonotebook import tqdm
# from tabulate import tabulate
# from .dbutil import query_timing

logger = logging.getLogger('wm2')
# logger.setLevel(logging.DEBUG)


def query_timing(func):
    """Get timing information from a function."""

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        results = func(*args, **kwargs)
        end = time.perf_counter()
        difference = end - start
        if difference > 0.01:
            logger.debug('Query execution took %.1f seconds', difference)
        return results
    return wrapper


def lazy_csv(csvfile: str) -> pl.LazyFrame:
    """Load lazy dataframe from a CSV file."""
    # Lazy load CSV file
    lazy_frame = pl.scan_csv(csvfile)

    return lazy_frame


def create_string_expression(column: str, operation: str, values: Union[str, List[str]]) -> pl.Expr:
    """
    Create an expression for string operations (ends_with, starts_with, contains, equals).
    
    Args:
        column (str): The name of the column to check.
        operation (str): The operation to perform ('ends_with', 'starts_with', 'contains', 'equals').
        values (Union[str, List[str]]): A single value or a list of values to check against.
    
    Returns:
        pl.Expr: A Polars expression based on the specified operation.
    """
    # Normalize values to a list
    if isinstance(values, str):
        values = [values]
    
    if not values:
        raise ValueError("The list of values cannot be empty.")
    
    if operation == "equal":
        expr = pl.col(column) == values[0]
        for value in values[1:]:
            expr = expr | (pl.col(column) == value)
    elif operation == "contains":
        expr = pl.col(column).str.contains(values[0])
        for value in values[1:]:
            expr = expr | pl.col(column).str.contains(value)
    elif operation == "starts_with":
        expr = pl.col(column).str.starts_with(values[0])
        for value in values[1:]:
            expr = expr | pl.col(column).str.starts_with(value)
    elif operation == "ends_with":
        expr = pl.col(column).str.ends_with(values[0])
        for value in values[1:]:
            expr = expr | pl.col(column).str.ends_with(value)
    else:
        raise ValueError(f"Unsupported string operation: {operation}")
    
    return expr


@query_timing
def query_lazy_df(lazy_df: pl.LazyFrame,
                  filters: Optional[Dict[str, List]]) -> pd.DataFrame:
    """Query a lazy dataframe."""
    # Apply filters if provided
    if filters:
        for column, conditions in filters.items():
            for condition in conditions:
                filter_type = condition.get("type")
                value = condition.get("value")
                negate = condition.get("negate", False)

                # Build the filter expression based on type
                if filter_type in ["equal", "contains", "starts_with", "ends_with"]:
                    expr = create_string_expression(column, filter_type, value)
                # redundant:
                # elif filter_type == "not_equal":
                #     expr = pl.col(column) != value
                # FIXME: "middle" query (cannot start or end with the string)
                elif filter_type == "in":
                    expr = pl.col(column).is_in(value)  # `value` should be a list of acceptable values
                elif filter_type == "greater_than":
                    expr = pl.col(column) > value
                elif filter_type == "less_than":
                    expr = pl.col(column) < value
                elif filter_type == "greater_than_or_equal":
                    expr = pl.col(column) >= value
                elif filter_type == "less_than_or_equal":
                    expr = pl.col(column) <= value
                else:
                    raise ValueError(f"Unsupported filter type: {filter_type}")

                # Apply negation if specified
                if negate:
                    expr = ~expr

                # Apply the filter to the lazy DataFrame
                lazy_df = lazy_df.filter(expr)

    # Collect the result to execute the query
    return lazy_df.collect()
