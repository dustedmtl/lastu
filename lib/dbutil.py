"""Utilities for reading and writing sqlite databases."""

# pylint: disable=invalid-name, line-too-long, too-many-locals, unnecessary-comprehension

# from typing import List, Dict, Tuple, Optional, Callable, Iterable
from typing import List, Tuple, Optional
from collections import Counter, defaultdict
# from os.path import basename
# from io import StringIO
import sqlite3
from sqlite3 import IntegrityError
import pandas as pd
import numpy as np
from tqdm.autonotebook import tqdm
from .mytypes import Freqs


def get_connection(dbfile: str) -> sqlite3.Connection:
    """Get SQLite connection."""
    sqlcon = sqlite3.connect(dbfile)
    return sqlcon


def write_freqs_to_db(connection: sqlite3.Connection,
                      freqs: Freqs):
    """Write frequencies to SQLite database."""
    cursor = connection.cursor()
    # cursor.execute('PRAGMA journal_mode=wal')
    # print('Cursor mode:', cursor.fetchall())

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


def get_trigram_freqs(connection: sqlite3.Connection) -> Tuple[Counter, Counter, Counter]:
    """Get initrigram, fintrigram, bigram frequencies."""
    init = Counter()  # type: ignore
    fin = Counter()  # type: ignore
    bi = Counter()  # type: ignore

    cursor = connection.cursor()
    # sqlstr = "select form, frequency from wordfreqs limit 10"
    sqlstr = "select form, frequency from wordfreqs"

    res = cursor.execute(sqlstr)
    for row in tqdm(res):
        form, freq = row
        initrigram = form[:3]
        fintrigram = form[-3:]
        # print(row, initrigram, fintrigram)
        init[initrigram] += freq
        fin[fintrigram] += freq

        for i, j in zip(range(0, len(form)-1), range(2, len(form)+1)):
            # print(i, j, form[i:j])
            bi[form[i:j]] += freq
    return init, fin, bi


def insert_trigram_freqs(connection: sqlite3.Connection,
                         init: Counter, fin: Counter, bi: Counter):
    """Insert frequencies to database."""
    cursor = connection.cursor()
    for table, counts in zip(['initgramfreqs', 'fingramfreqs', 'bigramfreqs'],
                             [init, fin, bi]):
        print(f'Inserting {len(counts)} rows to table {table}')

        insvalues = []
        for key, freq in counts.items():
            insvalues.append([key, freq])

        insertsql = f'INSERT INTO {table} (form, frequency) values (?, ?)'

        try:
            cursor.executemany(insertsql, insvalues)
            connection.commit()
        except IntegrityError as e:
            # this is not ok
            print('Issue', e)
            connection.rollback()


def insert_bigram_freqs(connection: sqlite3.Connection,
                        bi: Counter):
    """Insert word/bigram frequencies to database."""
    cursor = connection.cursor()

    # select = "SELECT DISTINCT(form) from wordfreqs LIMIT 10"
    select = "SELECT DISTINCT(form) from wordfreqs"
    cursor.execute(select)
    rows = cursor.fetchall()
    results = [row[0] for row in rows]

    insertsql = 'INSERT INTO wordbigramfreqs (form, frequency) VALUES (?, ?)'
    insvalues = []
    for form in results:
        bigs = [form[i:j] for i, j in zip(range(0, len(form)-1), range(2, len(form)+1))]
        freqs = [bi[s] for s in bigs]
        freq = int(np.sum(freqs) / len(freqs))
        # print(form, bigs, freqs, freq)
        insvalues.append([form, freq])

    try:
        cursor.executemany(insertsql, insvalues)
        connection.commit()
    except IntegrityError as e:
        # this is not ok
        print('Issue', e)
        connection.rollback()


def parse_query(query: str) -> List[List[str]]:
    """Parse query to SQL key-values."""
    parts = query.split('and')
    kvparts = []

    numkeys = ['frequency', 'len',
               'initrigramfreq', 'fintrigramfreq', 'bigramfreq']
    strkeys = ['lemma', 'form', 'pos',
               'nouncase', 'nnumber',
               'tense', 'person', 'verbform',
               'derivation', 'clitic',  # these my be complex
               'compound'  # special handling
               ]

    stroperators = ['=', '!=', 'like', 'in']
    numoperators = ['=', '!=', '<', '>', '<=', '>=']

    for part in parts:
        try:
            key, comparator, value = part.split()
            # print(f'{key}; {comparator}; {value}')
            value = value.strip("'").strip('"')

            isok = False

            if key in numkeys:
                if comparator in numoperators:
                    # print(f'Num ok: {key} {comparator}')
                    if value.isnumeric():
                        isok = True
                    else:
                        print(f"Query value for key '{key}' not ok: '{value}' is not a number")
                else:
                    print(f"Query comparator for '{key}' not ok: '{comparator}'")
            elif key in strkeys:
                if comparator in stroperators:
                    isok = True
                else:
                    print(f"Query comparator for '{key}' not ok: '{comparator}'")
            else:
                print(f"Query key '{key}' not ok")

            if isok:
                kvparts.append([key, comparator, value])
            # FIXME: compound
            # FIXME: derivation
            # FIXME: multiple values (?)
        except Exception as e:
            print(e)

    return kvparts


def get_frequency_dataframe(connection: sqlite3.Connection,
                            rowlimit: int = 10000,
                            orderby: str = 'frequency',
                            query: Optional[str] = None,
                            addgrams: bool = True,
                            aggregate: bool = True) -> pd.DataFrame:
    """Get frequencies as dataframe."""
    table = 'wordfreqs'
    # FIXME: validate rowlimit, orderby

    wherestr = ""
    args = []

    gfields = defaultdict(set)  # type: ignore

    if query:
        queryparts = parse_query(query)
        # print(queryparts)
        whereparts = []
        for andpart in queryparts:
            k, c, v = andpart
            usetable = 'w'
            if k.endswith('freq'):
                usetable = k[0]
                k = 'frequency'
            whereparts.append(f'{usetable}.{k} {c} ?')
            gflist = gfields.get(k, set())
            gflist.add(v)
            gfields[k] = gflist
            args.append(v)
        # print(whereparts)
        wherestr = "where " + ' and '.join(whereparts)
        print(wherestr)
        print(args)

    groupby = ""
    # dropcols = []
    if aggregate:
        groupby = "GROUP BY w.lemma, w.form, w.pos"
        if 'pos' in gfields:
            if 'NOUN' in gfields['pos']:
                groupby += ", w.nouncase, w.nnumber"
                # dropcols.extend(['verbform', 'tense'])
            elif 'VERB' in gfields:
                groupby += ", w.tense, w.person, w.verbform"
                # dropcols.extend(['nouncase'])
            elif 'ADJ' in gfields:
                groupby += ", w.nouncase, w.nnumber"
                # dropcols.extend(['verbform', 'tense'])

    # SELECT w.*, i.frequency as initgramfreq, f.frequency as fingramfreq, b.frequency as bigramfreq FROM wordfreqs w
    # LEFT JOIN initgramfreqs i ON i.form = substring(w.form, 1, 3)
    # LEFT JOIN fingramfreqs f ON f.form = substring(w.form, -3, 3)
    # LEFT join wordbigramfreqs b on b.form = w.form
    # where w.lemma = 'voi' and w.frequency > 10
    # GROUP BY w.lemma, w.form, w.pos, w.nouncase, w.nnumber ORDER BY w.frequency DESC LIMIT 10000;

    addselects = ""
    addjoins = ""

    # FIXME: second aggregation: just lemma, form and PoS

    if addgrams:
        aliases = ['i', 'f', 'b']
        names = ['initgramfreq', 'fingramfreq', 'bigramfreq']
        tables = ['initgramfreqs', 'fingramfreqs', 'wordbigramfreqs']
        comps = ['substring(w.form, 1, 3)', 'substring(w.form, -3, 3)', 'w.form']

        for alias, aname, atable, wordcomp in zip(aliases, names, tables, comps):
            # print(alias, aname, atable, wordcomp)
            addselects += f', {alias}.frequency as {aname}'
            addjoins += f' LEFT JOIN {atable} {alias} ON {alias}.form = {wordcomp}'

    sqlstr = f'SELECT w.*{addselects} FROM {table} w{addjoins} {wherestr} {groupby} ORDER BY {orderby} DESC LIMIT {rowlimit}'
    print(sqlstr)
    sql_query = pd.read_sql_query(sqlstr,
                                  connection,
                                  params=args)

    df = pd.DataFrame(sql_query)

    return df
