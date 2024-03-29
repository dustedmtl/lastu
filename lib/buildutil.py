"""Utilities for building databases."""

# pylint: disable=invalid-name, line-too-long

from typing import Optional, Dict, List
# from typing import List, Dict, Tuple, Optional, Callable, Iterable
# from typing import Optional, Tuple, Dict
# import sys
import math
# import os
from os.path import exists
import logging
import sqlite3
from sqlite3 import IntegrityError
# from pathlib import Path
# from shutil import copy
from tqdm.autonotebook import tqdm
from .dbutil import adhoc_query, chunks, DatabaseConnection


logger = logging.getLogger('wm2')
# logger.setLevel(logging.DEBUG)


def drop_table(sqlcon: sqlite3.Connection, table: str):
    """Drop table from database."""
    try:
        adhoc_query(sqlcon, f"DROP TABLE {table}", raiseerror=True)
    except sqlite3.OperationalError as se:
        if "no such table" in str(se):
            ...
        else:
            print(se)


def drop_helper_tables(sqlcon: sqlite3.Connection, full: bool = False):
    """Drop helper tables from the database."""
    if full:
        tables = [
            'initgramfreqs', 'fingramfreqs', 'bigramfreqs', 'wordbigramfreqs',
            'forms', 'lemmas', 'lemmaforms',
            'features', 'clitics', 'derivations', 'nouncases',
        ]
    else:
        tables = [
            'initgramfreqs', 'fingramfreqs', 'bigramfreqs', 'wordbigramfreqs',
            'forms', 'lemmas', 'lemmaforms',
        ]

    for table in tables:
        drop_table(sqlcon, table)


def drop_indexes(sqlcon: sqlite3.Connection,
                 match: str,
                 exclude: Optional[str] = None):
    """Drop matching indexes."""
    indexes = adhoc_query(sqlcon, "SELECT * FROM sqlite_master WHERE type = 'index'")
    droplist = []
    for idx in indexes:
        idxname = idx[1]
        if idx[4] is None:
            continue
        if 'UNIQUE' in idx[4]:
            print(f'Not dropping unique index: {idxname}')
            continue
        if exclude and exclude in idxname:
            print(f'Not dropping matching excluded index: {idxname}')
        if match in idxname:
            droplist.append(idxname)
    for idx in droplist:
        print(f'Dropping index {idx}...')
        sqlstr = f'DROP INDEX {idx}'
        adhoc_query(sqlcon, sqlstr)


def nullify_wordfreqs(sqlcon: sqlite3.Connection, full: bool = False):
    """Nullify computed information in the wordfreqs table."""
    if full:
        updatestr = "UPDATE wordfreqs SET hood = 0, ambform = 0, featid = 0"
    else:
        updatestr = "UPDATE wordfreqs SET hood = 0, ambform = 0"
    adhoc_query(sqlcon, updatestr)


def delete_rows(sqlcon: sqlite3.Connection,
                frequency: int):
    """Delete rows where frequency is lower than this value."""
    deletestr = f"DELETE FROM wordfreqs where frequency < {frequency}"
    adhoc_query(sqlcon, deletestr)


def delete_pos_rows(sqlcon: sqlite3.Connection,
                    poses: List[str]):
    """Delete rows with these wordclasses."""
    pp = ["'" + p + "'" for p in poses]
    pp2 = ','.join(pp)
    # print(pp2)
    deletestr = f"DELETE FROM wordfreqs where pos in ({pp2})"
    adhoc_query(sqlcon, deletestr)


def delete_len_rows(sqlcon: sqlite3.Connection,
                    maxlength: int):
    """Delete rows where form length is higher than this."""
    deletestr = f"DELETE FROM wordfreqs where len > {maxlength}"
    adhoc_query(sqlcon, deletestr)


def vacuum(sqlcon: sqlite3.Connection):
    """Vacuum a sqlite database."""
    print('Vacuuming the database...')
    adhoc_query(sqlcon, "VACUUM;")


def get_database_metadata(dbc: DatabaseConnection) -> Dict:
    """Get metadata from the database."""
    sqlcon = dbc.get_connection()
    data = adhoc_query(sqlcon, "select * from metadata;")
    return dict(data)


def add_schema(sqlcon: sqlite3.Connection,
               sqlfile: str):
    """Add schema from a SQL file."""
    cursor = sqlcon.cursor()
    print(f'Adding schema from {sqlfile}...')
    with open(f'sql/{sqlfile}', 'r', encoding='utf8') as schemafile:
        sqldata = schemafile.read()
        cursor.executescript(sqldata)
        sqlcon.commit()


def create_database(dbfile: str,
                    language: Optional[str] = None) -> DatabaseConnection:
    """Create new database."""
    if exists(dbfile):
        raise FileExistsError(dbfile)

    print(f'Creating database at {dbfile}')
    dbc = DatabaseConnection(dbfile, aggregates=False)
    sqlcon = dbc.get_connection()

    creationscripts = ['wordfreqs2.sql']

    if language is not None:
        tryscript = f'languages/features_{language}.sql'
    else:
        tryscript = 'features.sql'

    creationscripts.append(tryscript)

    for sqlfile in creationscripts:
        add_schema(sqlcon, sqlfile)

    dbc.record_features()
    return dbc


def add_features(dbc: DatabaseConnection):
    """Add features to features table."""
    featmap = dbc.featmap()
    sqlcon = dbc.get_connection()
    havefeats = adhoc_query(sqlcon, "SELECT distinct pos, feats FROM wordfreqs", todf=True)
    # print(havefeats)
    # template = "INSERT INTO %s (%s) values (%s)"
    itemplate = "INSERT OR IGNORE INTO %s (%s) values (%s)"

    featfields = ['feats', 'pos']

    for feat in sorted(featmap.keys()):
        featfields.append(featmap[feat])

    featinserts = []

    for _idx, row in havefeats.iterrows():
        pos = row.pos
        feats = row.feats
        featdict = {}

        for cat in feats.split('|'):
            if cat == '_':
                continue

            # print(cat)
            k, v = cat.split('=')
            featdict[k] = v

        featvals = [feats, pos]

        # cfeatdict = {cat.split('=')[0]: {k: v for k, v in cat.split('=')[1].items()} for cat in feats.split('|')}
        # print(pos, feats, featdict)
        for feat in sorted(featmap.keys()):
            featval = '_'
            # print(key, freq, featdict)
            if isinstance(featdict, dict) and feat in featdict:
                # print(feat, featdict[feat])
                featval = featdict[feat]
            # print(key, freq, featdict, featval)
            # print(recvals)
            featvals.append(featval)
        featinserts.append(featvals)

    cursor = sqlcon.cursor()

    insert_tpl = ', '.join(list(featfields))
    values_tpl = ', '.join(['?' for _ in featfields])
    insert_template = itemplate % ('features', insert_tpl, values_tpl)

    chunklen = 100000
    totfeatchunks = math.ceil(len(featinserts)/chunklen)

    print(f'Inserting {len(featinserts)} rows in {totfeatchunks} chunks...')
    print(insert_template)

    for chunk in tqdm(chunks(featinserts, chunklen=chunklen),
                      total=totfeatchunks):
        try:
            cursor.executemany(insert_template, chunk)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            sqlcon.rollback()
