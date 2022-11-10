"""Utilities for reading and writing sqlite databases."""

# pylint: disable=invalid-name, line-too-long

# from typing import List, Dict, Tuple, Optional, Callable, Iterable
from typing import List, Tuple, Union, Dict, Optional
from collections import Counter, defaultdict
# import sys
import time
# from os.path import basename
# from io import StringIO
import sqlite3
from sqlite3 import IntegrityError
import logging
import pandas as pd
from pandas.io.sql import DatabaseError
import numpy as np
from tqdm.autonotebook import tqdm
from tabulate import tabulate
from .mytypes import Freqs

logger = logging.getLogger('ui-qt6')
logger.setLevel(logging.DEBUG)


def get_connection(dbfile: str) -> sqlite3.Connection:
    """Get SQLite connection."""
    sqlcon = sqlite3.connect(dbfile)
    return sqlcon


def query_timing(func):
    """Get timing information from a function."""

    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        results = func(*args, **kwargs)
        end = time.perf_counter()
        logger.info('Query execution took %.1f seconds', end - start)
        return results
    return wrapper


@query_timing
def adhoc_query(connection: sqlite3.Connection,
                sqlstr: str,
                verbose: bool = False,
                todf: bool = False) -> Optional[pd.DataFrame]:
    """Execute an adhoc query."""
    try:
        if verbose:
            logger.debug('Executing query: %s', sqlstr)
        if todf:
            df = pd.DataFrame(pd.read_sql_query(sqlstr, connection))
            return df

        # print(connection)
        cursor = connection.cursor()
        cursor.execute(sqlstr)
        connection.commit()
        data = cursor.fetchall()
        return data
    except Exception as e:
        logging.exception(e)
        if not todf:
            connection.rollback()
        return None


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

        for i, j in zip(range(0, len(form)-1), range(2, len(form)+1)):
            # print(i, j, form[i:j])
            bi[form[i:j]] += freq

        if len(form) < 4:
            continue

        initrigram = form[:3]
        fintrigram = form[-3:]
        # print(row, initrigram, fintrigram)
        init[initrigram] += freq
        fin[fintrigram] += freq

    return init, fin, bi


def insert_trigram_freqs(connection: sqlite3.Connection,
                         init: Counter, fin: Counter, bi: Counter,
                         empty: bool = False):
    """Insert frequencies to database."""

    ok = defaultdict(bool)
    for table in ['initgramfreqs', 'fingramfreqs', 'bigramfreqs']:
        ok[table] = True
        print(f'Checking table {table}...', flush=True)
        have = adhoc_query(connection, f'select * from {table} limit 1', verbose=True)
        if len(have) > 0:
            if empty:
                print(f'Emptying table {table}...', flush=True)
                _ = adhoc_query(connection, f'delete from {table}', verbose=True)
            else:
                ok[table] = False

    cursor = connection.cursor()

    for table, counts in zip(['initgramfreqs', 'fingramfreqs', 'bigramfreqs'],
                             [init, fin, bi]):
        if not ok[table]:
            print(f'Table {table} already has content, not inserting', flush=True)
            continue

        print(f'Inserting {len(counts)} rows to table {table}', flush=True)

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
                        bi: Counter,
                        empty: bool = False):
    """Insert word/bigram frequencies to database."""
    ok = True
    table = 'wordbigramfreqs'
    print(f'Checking table {table}...', flush=True)
    have = adhoc_query(connection, f'select * from {table} limit 1', verbose=True)
    if len(have) > 0:
        if empty:
            print(f'Emptying table {table}...', flush=True)
            _ = adhoc_query(connection, f'delete from {table}', verbose=True)
        else:
            ok = False

    if not ok:
        print(f'Table {table} already has content, not inserting', flush=True)
        return

    # select = "SELECT DISTINCT(form) from wordfreqs LIMIT 10"
    print(f'Loading distinct forms from {table}...', flush=True)
    rows = adhoc_query(connection, "SELECT DISTINCT(form) from wordfreqs", verbose=True)
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
        print(f'Inserting {len(insvalues)} rows to table wordbigramfreqs', flush=True)
        cursor = connection.cursor()
        cursor.executemany(insertsql, insvalues)
        connection.commit()
    except IntegrityError as e:
        # this is not ok
        print('Issue', e)
        connection.rollback()


# FIXME: record choices from feature tables
class DatabaseConnection:
    """Encapsulation of database connection."""

    def __init__(self, filename: str):
        """Initialize database connection class."""
        # super().__init__(args)
        self.limit = 10000
        self.dbfile = filename
        self.connection = get_connection(filename)
        self.tables = ['wordfreqs']
        self.columns = defaultdict(list)  # type: ignore
        self.record_columns()

    def record_columns(self):
        """Store column lists."""
        for table in self.tables:
            # print(table)
            columndata = adhoc_query(self.connection,
                                     f'PRAGMA table_info({table})',
                                     todf=True)
            cols = columndata.name
            self.columns[table] = list(cols)

    def rowlimit(self, limit: int = None) -> int:
        """Get/set rowlimit."""
        if limit:
            self.limit = limit
        return self.limit

    def get_connection(self) -> sqlite3.Connection:
        """Return SQL connection."""
        return self.connection

    def have_posx(self) -> bool:
        """Check if posx is in column list."""
        return 'posx' in self.columns['wordfreqs']

    # FIXME: move to query class
    def get_queryselects(self, useposx: bool) -> str:
        """Get applicable query selects."""
        cols = []

        for col in self.columns['wordfreqs']:
            usecol = 'w.' + col
            if usecol == 'w.pos':
                usecol = 'w.posx as pos' if useposx else 'w.pos'
            elif usecol == 'w.posx':
                continue
            elif usecol == 'w.revform':
                continue
            elif usecol == 'w.frequency':
                if useposx:
                    usecol = "sum(w.frequency) as frequency"
            cols.append(usecol)
        return ', '.join(cols)


# FIXME: make this a query class
def parse_query(query: str) -> Tuple[List[List[str]], List]:
    """Parse query to SQL key-values."""
    parts = query.split('and')
    kvparts = []
    errors: List[str] = []

    numkeys = ['frequency', 'len',
               'lemmafreq', 'lemmalen', 'amblemma',
               'hood', 'ambform',
               'initrigramfreq', 'fintrigramfreq', 'bigramfreq']
    strkeys = ['lemma', 'form', 'pos',
               'nouncase', 'nnumber',
               'tense', 'person', 'verbform',
               'posspers', 'possnum',
               'start', 'middle', 'end',
               'derivation', 'clitic'  # these my be complex
               ]
    formkeys = ['start', 'middle', 'end']
    boolkeys = ['compound']

    stroperators = ['=', '!=', 'like', 'in']
    formoperators = ['=', '!=']
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
                            errors.append(f"Invalid query part: '{part.strip()}'")
                    else:
                        comparator = 'like'
                        isok = True
                else:
                    errors.append(f"Invalid query part: '{part.strip()}'")

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
                            errors.append(f"Query value for key '{key}' not ok: '{value}' is not a number")
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                elif key in formkeys:
                    if comparator in formoperators:
                        isok = True
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
        except ValueError as e:
            logging.exception(e)
            errors.append(f"Invalid query part: '{part.strip()}'")

    return kvparts, errors


indexorder = ['w.form', 'w.lemma',
              'w.frequency', 'w.len',
              'w.ambform', 'w.hood',
              'w.nouncase',
              'w.derivation',
              'w.clitic']

# fields that have good indexes
indexfields = {'w.frequency': 'wfreq_form', 'w.form': 'wform_len',
               'w.len': 'wlen', 'w.lemma': 'wlemma',
               'w.ambform': 'wambform', 'w.hood': 'whood',
               'w.nouncase': 'wcase',
               'w.derivation': 'wder',
               'w.clitic': 'wclitic'}


def parse_querystring(querystr: str) -> Tuple[str, List, List, List, List, bool]:
    """Parse the query string."""
    queryparts, errors = parse_query(querystr)
    # print(queryparts)

    whereparts = []
    wherestr = ""
    args = []
    useposx = True
    gfields = defaultdict(set)  # type: ignore

    indexers = []
    notlikeindexers = []

    for andpart in queryparts:
        # FIXME: NOT IN
        k, c, v = andpart
        usetable = 'w'
        if k in ['lemmafreq', 'lemmalen', 'amblemma']:
            usetable = 'l'
        elif k.endswith('freq'):
            usetable = k[0]
            k = 'frequency'
        fullcol = f'{usetable}.{k}'
        if fullcol in indexorder:
            if c == 'like':
                # % not at the beginning of string of like query: no indexing
                if not v.startswith('%'):
                    indexers.append(fullcol)
            else:
                notlikeindexers.append(fullcol)
                indexers.append(fullcol)

        gflist = gfields.get(k, set())
        if c == 'in':
            invals = [w.strip() for w in v.split(',')]
            if k in ['cliticx']:
                # old method, deprecated
                usetable = k[0]
                subargs = []
                whereor = []
                for val in invals:
                    subargs.append(f'{val}%')
                    subargs.append(val)
                    whereor.append(f'{usetable}.{k} LIKE ?')
                    whereor.append(f'{usetable}.{k} LIKE ?')
                whereparts.append(f"({' OR '.join(whereor)})")
                args.extend(subargs)
            elif k in ['derivation', 'clitic']:
                usetable = k[0]
                # separate table for derivations and clitics
                qmarks = ','.join(['?'] * len(invals))
                whereparts.append(f'{usetable}.{k} {c} ({qmarks})')
                whereparts.append(f'w.lemma = {usetable}.lemma and w.form = {usetable}.form and w.posx = {usetable}.pos and w.feats = {usetable}.feats')
                args.extend(invals)
            else:
                if k == 'pos':
                    if 'AUX' in invals:
                        useposx = False
                    else:
                        k = 'posx'
                qmarks = ','.join(['?'] * len(invals))
                whereparts.append(f'{usetable}.{k} {c} ({qmarks})')
                args.extend(invals)
            _ = [gflist.add(_) for _ in invals]
        else:
            # FIXME: IN query
            if k == 'start':
                if c == '=':
                    whereparts.append(f'instr({usetable}.form, ?) {c} 1')
                else:
                    whereparts.append(f'instr({usetable}.form, ?) {c} 1')
                args.append(v)
                continue
            if k == 'middle':
                if c == '=':
                    # whereparts.append(f'{usetable}.form GLOB ?')
                    # args.append(f'?*{v}*?')
                    whereparts.append(f'instr({usetable}.form, ?) > 1')
                    args.append(v)
                    whereparts.append(f'{usetable}.revform NOT GLOB ?')
                    args.append(v[::-1] + "*")
                else:
                    whereparts.append(f'instr({usetable}.form, ?) == 0')
                    args.append(v)
                continue
            if k == 'end':
                if c == '=':
                    whereparts.append(f'{usetable}.revform GLOB ?')
                else:
                    whereparts.append(f'{usetable}.revform NOT GLOB ?')
                args.append(v[::-1] + "*")
                continue
            if k == 'pos':
                if v == 'AUX':
                    useposx = False
                else:
                    k = 'posx'
            whereparts.append(f'{usetable}.{k} {c} ?')
            args.append(v)
            if c == '=':
                gflist.add(v)
        gfields[k] = gflist

    if len(whereparts) > 0:
        wherestr = "WHERE " + " AND ".join(whereparts)

    return wherestr, args, errors, indexers, notlikeindexers, useposx


def parse_querydict(querydict: Dict) -> Tuple[str, List, List, List, List]:
    """Parse query dictionary."""
    wherestr = ""
    whereparts = []
    args = []
    indexers = set()
    errors: List[str] = []

    # FIXME: validate: can only have lemma/form (?)
    for querypart in querydict.keys():
        for queryval in querydict[querypart]:
            indexers.add(querypart)
            whereparts.append(f'w.{querypart} = ?')
            args.append(queryval)
    wherestr = "WHERE " + " OR ".join(whereparts)
    return wherestr, args, errors, list(indexers), []


def get_indexer(indexers: List,
                notlikeindexers: List,
                orderby: str) -> str:
    """Possibly force indexer."""
    print(f'Indexers: {indexers}')
    print(f'Not LIKE indexers: {notlikeindexers}')

    orderby = orderby.split(' ')[0]
    windexedby = ""
    # At least one column needs to be indexed with a proper index
    if len(notlikeindexers) == 0:
        for indexer in indexorder:
            if indexer in indexers and indexer in indexfields:
                windexedby = f"indexed by {indexfields[indexer]}"
                break
        if len(windexedby) == 0:
            # The best index depends on the sorting. This is by default frequency
            orderfield = orderby.split(' ')[0]
            if orderfield in indexfields:
                windexedby = f"indexed by {indexfields[orderby]}"
        print(f'Force indexer other than autoindex: {windexedby}')
    return ""
    return windexedby


def get_querystring(query: Union[str, Dict] = None,
                    orderby: str = 'w.frequency',
                    defaultindex: bool = False) -> Tuple[str, List[str], List[str], str, bool]:
    """Get final query string and other things."""
    useposx = True
    if isinstance(query, str):
        wherestr, args, errors, indexers, notlikeindexers, useposx = parse_querystring(query)
        # print(errors)
    elif isinstance(query, dict):
        defaultindex = True
        wherestr, args, errors, indexers, notlikeindexers = parse_querydict(query)

    print(wherestr, args)
    windexedby = "" if defaultindex else get_indexer(indexers, notlikeindexers, orderby)
    return wherestr, args, errors, windexedby, useposx


def get_orderby(orderby: str) -> str:
    """Get SQLorderby string."""
    orderdirection = 'DESC'
    orderparts = orderby.split(' ')
    if orderparts[0].startswith('w.'):
        orderby = orderparts[0]
        if len(orderparts) > 1:
            if orderparts[1] in ['ASC', 'DESC']:
                orderdirection = orderparts[1]
    orderstring = ' '.join([orderby, orderdirection])
    return orderstring


# FIXME: defaultindex to connection class
# FIXME: lemmas, grams to connection class?
def get_frequency_dataframe(dbconnection: DatabaseConnection,
                            orderby: str = 'w.frequency',
                            query: Union[str, Dict] = None,
                            defaultindex: bool = False,
                            lemmas: bool = False,
                            # aggregate: bool = True,
                            grams: bool = False) -> Tuple[pd.DataFrame, int, str]:
    """Get frequencies as dataframe."""
    # FIXME: validate rowlimit

    connection = dbconnection.connection

    # FIXME: orderstring takes posx into account
    orderstring = get_orderby(orderby)
    # table = 'wordfreqs'
    # wherestr = ""
    # args: List[str] = []

    wherestr, args, errors, windexedby, useposx = get_querystring(query, orderstring, defaultindex)
    wselects = dbconnection.get_queryselects(useposx)
    # print(wselects)

    # FIXME: return query errors if so deemed

    #    if isinstance(query, str):
    #        wherestr, args, errors, indexers, notlikeindexers = parse_querystring(query)
    #        print(errors)
    #    elif isinstance(query, dict):
    #        defaultindex = True
    #        wherestr, args, errors, indexers, notlikeindexers = parse_querydict(query)

    #    print(wherestr, args)

    #    windexedby = "" if defaultindex else get_indexer(indexers, notlikeindexers, orderby)

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

    addfrom = ""
    addselects = ""
    addjoins = ""

    if 'posx' in wselects:
        groupby = "group by w.lemma, w.form, w.posx, w.feats"

    if 'd.derivation' in wherestr:
        addfrom += ",derivations d"
    if 'c.clitic' in wherestr:
        addfrom += ",clitics c"

    if lemmas:
        addselects += ', l.lemmafreq, l.lemmalen, l.amblemma'
        addjoins += ' LEFT JOIN lemmas l ON w.lemma = l.lemma AND w.posx = l.pos'

        addselects += ', 1-lf.formpct as ambform'
        addjoins += ' LEFT JOIN lemmaforms lf ON w.lemma = lf.lemma AND w.form = lf.form AND w.posx = lf.pos'

    if grams:
        aliases = ['i', 'f', 'b']
        names = ['initgramfreq', 'fingramfreq', 'bigramfreq']
        tables = ['initgramfreqs', 'fingramfreqs', 'wordbigramfreqs']
        comps = ['substr(w.form, 1, 3)', 'substr(w.form, -3, 3)', 'w.form']

        for alias, aname, atable, wordcomp in zip(aliases, names, tables, comps):
            # print(alias, aname, atable, wordcomp)
            if alias in 'if':
                addselects += f', iif(length(w.form) > 3, {alias}.frequency, 0) as {aname}'
            else:
                addselects += f', {alias}.frequency as {aname}'
            addjoins += f' LEFT JOIN {atable} {alias} ON {alias}.form = {wordcomp}'

    sqlstr = f'SELECT {wselects}{addselects} FROM wordfreqs w{addfrom} {windexedby} {addjoins} {wherestr} {groupby} ORDER BY {orderstring} LIMIT {dbconnection.rowlimit()}'
    print(sqlstr)
    print(args)

    querystatus = 0
    querymessage = 'success'

    try:
        explainer = pd.read_sql_query('explain query plan ' + sqlstr,
                                      connection,
                                      params=args)
        print()
        print('Query plan:')
        print(tabulate(explainer, headers=explainer.columns))

        starttime = time.perf_counter()
        sql_query = pd.read_sql_query(sqlstr,
                                      connection,
                                      params=args)

        df = pd.DataFrame(sql_query)
        endtime = time.perf_counter()
        print()
        print(f'{len(df)} rows returned in {endtime - starttime:.1f} seconds')

    except DatabaseError as e:
        print(str(e))
        _, errmsg = str(e).split(': ', 1)
        print(errmsg)
        logging.exception(e)
        df = pd.DataFrame()
        querymessage = errmsg

    return df, querystatus, querymessage
