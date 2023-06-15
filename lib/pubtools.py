"""Utilities for publishing dataframes."""

# pylint: disable=invalid-name, too-many-arguments, too-many-locals

from typing import List, Dict, Optional
from os.path import isfile
# import unicodedata
from datetime import datetime
import pandas as pd
# import matplotlib.pyplot as plt


def get_datestr():
    """Get current date string."""
    currdate = datetime.now()
    datestr = currdate.strftime("%Y%m%d")
    return datestr


def add_hlines(latex: str, hlines: Optional[List[int]] = None) -> str:
    """Add hlines to latex table."""
    lines = []
    lineno = 0
    for line in latex.split('\n'):
        lineno += 1
        if lineno > 2 and 'tabular' in line:
            lines.append('\hline')
        lines.append(line)
        if lineno in [1, 2]:
            lines.append('\hline')
        elif hlines and lineno in hlines:
            lines.append('\hline')

    return '\n'.join(lines)


def save_table(df: pd.DataFrame,
               name: str, path: str = 'paper/tables',
               ext: int = 1, index: bool = True,
               hlines: Optional[List[int]] = None,
               precision: int = 3,
               force: bool = False,
               colformat: Optional[Dict] = None):
    """Save dataframe to disk as latex, append date."""
    datestr = get_datestr()
    fmt = "%s/%s_%s_%d.tex"
    filename = fmt % (path, name, datestr, ext)
    if isfile(filename) and not force:
        print(f"File '{filename}' already exists")
        return
    ldf = df.copy()
    for col, t in zip(ldf.columns, ldf.dtypes):
        if t == bool:
            ldf = ldf.astype({col: str})
    latex = ldf.style.format(precision=precision).format_index("\\textbf{{{}}}",
                                                               escape="latex", axis=1)
    # Remove index column
    if not index:
        latex = latex.hide()
    # Apply column formatting overrides
    colfmt = ''
    for col, dt in zip(ldf.columns, ldf.dtypes):
        if colformat and col in colformat:
            colfmt += colformat[col]
        elif dt in [object, bool]:
            colfmt += 'l'
        else:
            colfmt += 'r'
    latex = latex.to_latex(column_format=colfmt).replace('_', '\\_')
    # print(latex)
    if hlines:
        latex = add_hlines(latex, hlines)
    # print(latex)
    print('Saving dataframe to', filename)
    with open(filename, 'w') as f:
        f.write(latex)
