"""Utilities for reading and writing sqlite databases."""

# pylint: disable=invalid-name, line-too-long

# from typing import List, Dict, Tuple, Optional, Callable, Iterable
from typing import List, Tuple, Optional, Union, Dict
from collections import Counter, defaultdict
# from os.path import basename
# from io import StringIO
import sqlite3
from sqlite3 import IntegrityError
import pandas as pd
import numpy as np
from tqdm.autonotebook import tqdm
from tabulate import tabulate
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
        'Person[psor]': 'posspers',
        'Number[psor]': 'possnum',
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

    if len(values2) > 0:
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
               'posspers', 'possnum',
               'derivation', 'clitic',  # these my be complex
               'compound'  # special handling
               ]
    boolkeys = ['compound']

    stroperators = ['=', '!=', 'like', 'in']
    numoperators = ['=', '!=', '<', '>', '<=', '>=']

    for part in parts:
        try:
            vals = part.split()
            bols = [w for w in vals if w in boolkeys]

            isok = False

            if bols:
                if bols[0] == 'compound':
                    key = 'lemma'
                    value = '%#%'
                    if len(vals) > 1:
                        if vals[0] == 'not':
                            comparator = 'not like'
                            isok = True
                        else:
                            print(f"Invalid query part: {part}")
                    else:
                        comparator = 'like'
                        isok = True
                else:
                    print(f"Invalid query part: {part}")

            else:
                key, comparator, value = vals
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
            print(f"Invalid query part {part}: {e}")

    return kvparts


indexorder = ['w.form', 'w.frequency',
              'w.nouncase', 'w.nnumber', 'w.derivation',
              'w.clitic', 'w.pos', 'w.lemma']


def parse_querystring(querystr: str) -> Tuple[str, List, List, List]:
    """Parse the query string."""
    queryparts = parse_query(querystr)
    # print(queryparts)

    whereparts = []
    wherestr = ""
    args = []

    gfields = defaultdict(set)  # type: ignore

    indexers = []
    notlikeindexers = []

    for andpart in queryparts:
        k, c, v = andpart
        usetable = 'w'
        if k.endswith('freq'):
            usetable = k[0]
            k = 'frequency'
        fullcol = f'{usetable}.{k}'
        if fullcol in indexorder:
            indexers.append(fullcol)
            if c != 'like':
                notlikeindexers.append(fullcol)
        whereparts.append(f'{usetable}.{k} {c} ?')
        args.append(v)
        gflist = gfields.get(k, set())
        gflist.add(v)
        gfields[k] = gflist

    if len(whereparts) > 0:
        wherestr = "WHERE " + ' AND '.join(whereparts)

    return wherestr, args, indexers, notlikeindexers


def parse_querydict(querydict: Dict) -> Tuple[str, List, List, List]:
    """Parse query dictionary."""
    wherestr = ""
    whereparts = []
    args = []
    indexers = set()

    for querypart in querydict.keys():
        for queryval in querydict[querypart]:
            indexers.add(querypart)
            whereparts.append(f'w.{querypart} = ?')
            args.append(queryval)
    wherestr = 'WHERE ' + ' OR '.join(whereparts)
    return wherestr, args, list(indexers), []


def get_indexer(indexers: List,
                notlikeindexers: List) -> str:
    """Possibly force indexer."""
    print(f'Indexers: {indexers}')
    print(f'Not LIKE indexers: {notlikeindexers}')
    indexfields = {'w.frequency': 'wfreq', 'w.form': 'wform',
                   'w.len': 'wlen', 'w.lemma': 'wlemma',
                   'w.derivation': 'wder', 'w.clitic': 'wclitic'}
    windexedby = ""
    # At least one column needs to be indexed with a proper index
    if len(notlikeindexers) == 0:
        for indexer in indexorder:
            if indexer in indexers and indexer in indexfields:
                windexedby = f"indexed by {indexfields[indexer]}"
                break
        if len(windexedby) == 0:
            windexedby = "indexed by wform"
        print(f'Force indexer other than autoindex: {windexedby}')
    return windexedby


def get_frequency_dataframe(connection: sqlite3.Connection,
                            rowlimit: int = 10000,
                            orderby: str = 'w.frequency',
                            query: Union[str, Dict] = None,
                            defaultindex: bool = False,
                            # aggregate: bool = True,
                            grams: bool = False) -> Tuple[pd.DataFrame, int, str]:
    """Get frequencies as dataframe."""
    table = 'wordfreqs'
    # FIXME: validate rowlimit, orderby
    # FIXME: make this a class

    wherestr = ""
    args = []

    if isinstance(query, str):
        wherestr, args, indexers, notlikeindexers = parse_querystring(query)
    elif isinstance(query, dict):
        defaultindex = True
        wherestr, args, indexers, notlikeindexers = parse_querydict(query)

    print(wherestr, args)

    if len(wherestr) == 0:
        return pd.DataFrame(), -1, 'No valid query string'

    groupby = ""
    # dropcols = []
    # if aggregate:
    #    groupby = "GROUP BY w.lemma, w.form, w.pos, w.feats"
    #    if 'pos' in gfields:
    #        if 'NOUN' in gfields['pos']:
    #            groupby += ", w.nouncase, w.nnumber"
    #            # dropcols.extend(['verbform', 'tense'])
    #        elif 'VERB' in gfields:
    #            groupby += ", w.tense, w.person, w.verbform"
    #            # dropcols.extend(['nouncase'])
    #        elif 'ADJ' in gfields:
    #            groupby += ", w.nouncase, w.nnumber"
    #            # dropcols.extend(['verbform', 'tense'])

    addselects = ""
    addjoins = ""

    windexedby = "" if defaultindex else get_indexer(indexers, notlikeindexers)

    if grams:
        aliases = ['i', 'f', 'b']
        names = ['initgramfreq', 'fingramfreq', 'bigramfreq']
        tables = ['initgramfreqs', 'fingramfreqs', 'wordbigramfreqs']
        comps = ['substr(w.form, 1, 3)', 'substr(w.form, -3, 3)', 'w.form']

        for alias, aname, atable, wordcomp in zip(aliases, names, tables, comps):
            # print(alias, aname, atable, wordcomp)
            addselects += f', {alias}.frequency as {aname}'
            addjoins += f' LEFT JOIN {atable} {alias} ON {alias}.form = {wordcomp}'

    # sqlstr = f'SELECT w.*{addselects} FROM {table} w{addjoins} {wherestr} {groupby} ORDER BY {orderby} DESC LIMIT {rowlimit}'
    sqlstr = f'SELECT w.*{addselects} FROM {table} w {windexedby} {addjoins} {wherestr} {groupby} ORDER BY {orderby} DESC LIMIT {rowlimit}'
    print(sqlstr)
    print(args)

    explainer = pd.read_sql_query('explain query plan ' + sqlstr,
                                  connection,
                                  params=args)
    print()
    print('Query plan:')
    print(tabulate(explainer, headers=explainer.columns))

    querystatus = 0
    querymessage = 'success'

    sql_query = pd.read_sql_query(sqlstr,
                                  connection,
                                  params=args)

    df = pd.DataFrame(sql_query)

    return df, querystatus, querymessage
