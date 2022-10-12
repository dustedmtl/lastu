"""Utilities for reading and writing sqlite databases."""

# pylint: disable=invalid-name, line-too-long, too-many-locals, unnecessary-comprehension

# from typing import List, Dict, Tuple, Optional, Callable, Iterable
# from os.path import basename
# from io import StringIO
import sqlite3
from sqlite3 import IntegrityError
import pandas as pd
# from tqdm.notebook import tqdm
from .mytypes import Freqs


def get_connection(dbfile: str) -> sqlite3.Connection:
    """Get SQLite connection."""
    sqlcon = sqlite3.connect(dbfile)
    return sqlcon


def write_freqs_to_db(connection: sqlite3.Connection,
                      freqs: Freqs):
    """Write frequencies to SQLite database."""
    cursor = connection.cursor()
    cursor.execute('PRAGMA journal_mode=wal')
    print('Cursor mode:', cursor.fetchall())

    template = "INSERT INTO %s (%s) values (%s)"

    featmap = {
        'Number': 'nnumber',
        'Case': 'nouncase',
        'Derivation': 'derivation',
        'Tense': 'tense',
        'Person': 'person',
        'VerbForm': 'verbform',
        'Clitic': 'clitic'
    }

    fields = ['lemma', 'form', 'pos', 'frequency', 'len', 'feats']
    fields2 = ['lemma', 'form', 'pos', 'frequency', 'feats']

    for feat in sorted(featmap.keys()):
        fields.append(featmap[feat])

    itpl = ', '.join([f for f in fields])
    vtpl = ','.join(['?' for _ in fields])

    insert_template = template % ('wordfreqs', itpl, vtpl)
    # print(insert_template)

    values = []
    for key, freq in freqs[0].items():
        # print(key, freq)
        # lemma, word, pos = key.split(' ')
        lemma, word, pos, feats = key
        recvals = [lemma, word, pos, freq, len(word), feats]
        featdict = freqs[1][key]
        for feat in sorted(featmap.keys()):
            featval = '_'
            # print(key, freq, featdict)
            if isinstance(featdict, dict) and feat in featdict:
                # print(feat, featdict[feat])
                featval = featdict[feat]
            # print(key, freq, featdict, featval)
            # print(recvals)
            recvals.append(featval)
        # print(recvals)
        values.append(recvals)

    try:
        # FIXME: try to do an upsert? (update/insert)
        cursor.executemany(insert_template, values)
        connection.commit()
    except IntegrityError as e:
        # this is not ok
        print('Issue', e)
        connection.rollback()

    fields2 = ['lemma', 'form', 'pos', 'frequency', 'feats']

    itpl2 = ', '.join([f for f in fields2])
    vtpl2 = ','.join(['?' for _ in fields2])

    insert_template2 = template % ('wordfeats', itpl2, vtpl2)
    # print(insert_template)

    values2 = []
    for key, freq in freqs[2].items():
        lemma, word, pos, feats = key
        recvals = [lemma, word, pos, freq, feats]
        values2.append(recvals)

    try:
        cursor.executemany(insert_template2, values2)
        connection.commit()
    except IntegrityError as e:
        # this is not ok
        print('Issue', e)
        connection.rollback()


def get_frequency_dataframe(connection: sqlite3.Connection,
                            full: bool = False) -> pd.DataFrame:
    """Get frequencies as dataframe."""
    table = 'wordfeats' if full else 'wordfreqs'
    sql_query = pd.read_sql_query(f'SELECT * FROM {table}', connection)

    df = pd.DataFrame(sql_query)
    return df
