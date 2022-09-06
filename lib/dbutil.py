"""Utilities for reading and writing sqlite databases."""

# pylint: disable=invalid-name, line-too-long, too-many-locals, unnecessary-comprehension

from typing import Tuple
# from typing import List, Dict, Tuple, Optional, Callable, Iterable
# from os.path import basename
# from io import StringIO
from collections import Counter
import sqlite3
from sqlite3 import IntegrityError
import pandas as pd
# from tqdm.notebook import tqdm

Freqs = Tuple[Counter, Counter, Counter]


def get_connection(dbfile: str) -> sqlite3.Connection:
    """Get SQLite connection."""
    sqlcon = sqlite3.connect(dbfile)
    return sqlcon


def write_freqs_to_db(connection: sqlite3.Connection,
                      freqs: Freqs):
    """Write frequencies to SQLite database."""
    cursor = connection.cursor()

    template = "INSERT INTO %s (%s) values (%s)"

    fields = ['lemma', 'form', 'pos', 'frequency', 'len']
    itpl = ', '.join([f for f in fields])
    vtpl = ','.join(['?' for _ in fields])

    insert_template = template % ('wordfreqs', itpl, vtpl)
    # print(insert_template)

    values = []
    for key, freq in freqs[0].items():
        # print(key, freq)
        # lemma, word, pos = key.split(' ')
        lemma, word, pos = key
        recvals = [lemma, word, pos, freq, len(word)]
        values.append(recvals)

    try:
        # FIXME: try to do an upsert? (update/insert)
        cursor.executemany(insert_template, values)
        connection.commit()
    except IntegrityError as e:
        # this is not ok
        print('Issue', e)
        connection.rollback()


def get_frequency_dataframe(connection: sqlite3.Connection) -> pd.DataFrame:
    """Get frequencies as dataframe."""
    sql_query = pd.read_sql_query('SELECT * FROM wordfreqs', connection)

    df = pd.DataFrame(sql_query)
    return df
