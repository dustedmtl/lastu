"""utilities for reading data from polars."""

# pylint: disable=invalid-name, line-too-long

from typing import Optional, Dict, Tuple, Any, List, Union
# from collections import Counter, defaultdict
import polars as pl
import pandas as pd
import re
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
        expr = pl.col(column).str.replace("#", "") == values[0]
        for value in values[1:]:
            expr = expr | (pl.col(column).str.replace("#", "") == value)
    elif operation == "contains":
        expr = pl.col(column).str.contains(values[0])
        for value in values[1:]:
            expr = expr | pl.col(column).str.contains(value)
    elif operation == "middle":
        middleregex = ".+%s.+"
        expr = pl.col(column).str.contains(middleregex % values[0])
        for value in values[1:]:
            expr = expr | pl.col(column).str.contains(middleregex % value)
#        expr2 = pl.col(column).str.starts_with(values[0])
#        for value in values[1:]:
#            expr2 = expr2 | pl.col(column).str.starts_with(value)
#        expr3 = pl.col(column).str.ends_with(values[0])
#        for value in values[1:]:
#            expr3 = expr3 | pl.col(column).str.ends_with(value)
#        print(expr)
#        print(expr2)
#        print(expr3)
#        expr = expr & ~expr2 & ~expr3
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
                  filters: Optional[Dict[str, List]]) -> pl.DataFrame:
    """Query a lazy dataframe."""
    # Apply filters if provided
    if filters:
        for column, conditions in filters.items():
            for condition in conditions:
                filter_type = condition.get("type")
                value = condition.get("value")
                negate = condition.get("negate", False)

                # Build the filter expression based on type
                if filter_type in ["equal", "contains", "middle", "starts_with", "ends_with"]:
                    expr = create_string_expression(column, filter_type, value)
                # redundant:
                # elif filter_type == "not_equal":
                #     expr = pl.col(column) != value
                # FIXME: "middle" query (cannot start or end with the string)
                elif filter_type == "in":
                    expr = pl.col(column).is_in(value)  # `value` should be a list of acceptable values
                elif filter_type in ['=']:
                    expr = pl.col(column) == value
                elif filter_type in ['!=']:
                    expr = pl.col(column) != value
                elif filter_type in ["greater_than", '>']:
                    expr = pl.col(column) > value
                elif filter_type in ["less_than", '<']:
                    expr = pl.col(column) < value
                elif filter_type in ["greater_than_or_equal", '>=']:
                    expr = pl.col(column) >= value
                elif filter_type in ["less_than_or_equal", '<=']:
                    expr = pl.col(column) <= value
                else:
                    raise ValueError(f"Unsupported filter type: {filter_type}")

                # Apply negation if specified
                if negate:
                    expr = ~expr

                # Apply the filter to the lazy DataFrame
                lazy_df = lazy_df.filter(expr)
                print(lazy_df)

    # Collect the result to execute the query
    return lazy_df.collect()


def parse_query_polars(query: str,
                       lazy_df: pl.LazyFrame) -> Tuple[List[List[Any]], List]:
    """Parse query to polars filter structure."""
    parts = query.lower().split('and')
    kvparts = []
    errors: List[str] = []

    numkeys = ['frequency', 'len',
               'lemmafreq', 'lemmalen', 'amblemma',
               'hood', 'ambform',
               'relfrequency', 'rellemmafreq',
               'initrigramfreq', 'fintrigramfreq', 'bigramfreq']
    strkeys = ['lemma', 'form', 'pos',
               'start', 'middle', 'end',
               'top'
               ]
    # FIXME: extend strkeys from headers
    # FIXME: input csv header instead of lazy_df
    # strkeys.extend(revfeatmap.keys())
    formkeys = ['start', 'middle', 'end']
    boolkeys = ['compound']
    stroperators = ['=', '!=', 'like', 'in', 'notin']
    formoperators = ['=', '!=', 'in', 'notin']
    numoperators = ['=', '!=', '<', '>', '<=', '>=']

    shortcuts = {
        'freq': 'frequency',
        'relfreq': 'relfrequency',
        'nouncase': 'case',
        'nnumber': 'number',
    }

    for part in parts:

        try:
            part = re.sub(r'not\s+in', 'notin', part, re.I)
            vals = part.split()
            bols = [w for w in vals if w in boolkeys]

            value: Any = None
            negate = False
            isok = False

            if bols:
                if bols[0] == 'compound':
                    key = 'lemma'
                    polarsop = 'contains'
                    value = '#'
                    if len(vals) > 1:
                        if vals[0] == 'not':
                            negate = True
                            isok = True
                        else:
                            errors.append(f"Invalid query part: '{part.strip()}'")
                    else:
                        # comparator = '>'
                        isok = True

                else:
                    errors.append(f"Invalid query part: '{part.strip()}'")

            else:
                key, comparator, value = vals
                value = value.strip("'").strip('"')
                # if key == 'lemma' and comparator != 'like':
                #    key = 'lemmac'
                key = shortcuts.get(key, key)

                if key in numkeys:
                    if comparator in numoperators:
                        # print(f'Num ok: {key} {comparator}')
                        try:
                            value = float(value)
                            polarsop = comparator
                            isok = True
                        except ValueError as ve:
                            logging.exception("Can't cast %s as float: %s", value, ve)
                            errors.append(f"Query value for key '{key}' not ok: '{value}' is not a number")
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                elif key in formkeys:
                    if key == 'start':
                        polarsop = 'starts_with'
                    elif key == 'end':
                        polarsop = 'ends_with'
                    elif key == 'middle':
                        # FIXME: not right
                        polarsop = 'middle'

                    if comparator in formoperators:
                        if comparator in ['in', 'notin']:
                            value = value.split(',')
                        if comparator in ['!=', 'notin']:
                            negate = True
                        key = 'form'
                        isok = True
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # print(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # logger.debug("Query comparator for '%s' not ok: '%s'", key, comparator)
                elif key in strkeys:
                    if comparator in stroperators:
                        polarsop = 'equal'
                        if key == 'pos':
                            value = value.upper()
                        elif key == 'case':
                            value = value.title()

                        if comparator in ['in', 'notin']:
                            value = value.split(',')
                        if comparator in ['!=', 'notin']:
                            negate = True
                        isok = True
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # print(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # logger.debug("Query comparator for '%s' not ok: '%s'", key, comparator)
                else:
                    errors.append(f"Query key '{key}' not ok")
                    # print(f"Query key '{key}' not ok")

            if isok:
                kvparts.append([key, polarsop, value, negate])
        except ValueError as e:
            logging.exception(e)
            errors.append(f"Invalid query part: '{part.strip()}'")

    return kvparts, errors


def query_to_filter(query: str,
                    lazy_df: pl.LazyFrame) -> Dict[str, List[Dict]]:
    """Convert LASTU query to polars filters."""
    k, e = parse_query_polars(query, lazy_df)

    filters: dict[str, List] = {}
    for part in k:
        key, op, value, negate = part
        if key not in filters:
            filters[key] = []
        filters[key].append({
            "type": op,
            "value": value,
            "negate": negate,
        })
    return filters


def query(lazy_df: pl.LazyFrame,
          query: str) -> pl.DataFrame:
    """Query lazy frame using LASTU syntax."""
    filters = query_to_filter(query, lazy_df)
    logging.info("%s -> %s", query, filters)
    return query_lazy_df(lazy_df, filters)
