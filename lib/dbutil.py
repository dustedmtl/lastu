"""utilities for reading and writing sqlite databases."""

# pylint: disable=invalid-name, line-too-long

# from typing import List, Dict, Tuple, Optional, Callable, Iterable
from typing import List, Tuple, Union, Dict, Optional, Iterator
from collections import Counter, defaultdict
# import sys
import time
import math
import re
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
from .features import allfeatures

logger = logging.getLogger('wm2')
# logger.setLevel(logging.DEBUG)


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
        difference = end - start
        if difference > 0.01:
            logger.debug('Query execution took %.1f seconds', difference)
        return results
    return wrapper


@query_timing
def adhoc_query(connection: sqlite3.Connection,
                sqlstr: str,
                verbose: bool = False,
                raiseerror: bool = False,
                todf: bool = False) -> Optional[pd.DataFrame]:
    """Execute an adhoc query."""
    try:
        if verbose:
            logger.info('Executing query: %s', sqlstr)
        else:
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
        if not todf:
            connection.rollback()
        if raiseerror:
            raise e
        logging.exception(e)
        return None


def chunks(dataset: Union[List, pd.DataFrame], chunklen=1000) -> Iterator:
    """Create an iterator for dataset chunks."""
    if isinstance(dataset, pd.DataFrame):
        dataset = dataset.values.tolist()
        # print(dataset[:10])
    for i in range(0, len(dataset), chunklen):
        slc = dataset[i:i+chunklen]
        yield slc


# FIXME: move gram freq functions to buildutil
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
        have = adhoc_query(connection, f'select * from {table} limit 1')
        if len(have) > 0:
            if empty:
                print(f'Emptying table {table}...', flush=True)
                _ = adhoc_query(connection, f'delete from {table}')
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
    have = adhoc_query(connection, f'select * from {table} limit 1')
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
    rows = adhoc_query(connection, "SELECT DISTINCT(form) from wordfreqs")
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


class DatabaseConnection:
    """Encapsulation of database connection."""

    def __init__(self,
                 filename: str,
                 aggregates: bool = True):
        """Initialize database connection class."""
        # super().__init__(args)
        self.limit = 10000
        filename = filename.replace("\\", "/")
        self.dbfile = filename
        self.connection = get_connection(filename)
        # self.tables = ['wordfreqs', 'features', 'forms', 'lemmaforms', 'lemmas']
        self.tables = ['wordfreqs', 'features', 'lemmas']
        self.columns = defaultdict(list)  # type: ignore
        self.record_columns()
        if aggregates:
            self.fetch_aggregate_frequencies()
        self.record_features()

    def record_features(self):
        """Get actual features from the database."""
        actualfeatures = adhoc_query(self.connection,
                                     'PRAGMA table_info(features)',
                                     verbose=True)
        # All supported features
        # print(allfeatures)
        # Actual features
        # print(actualfeatures)
        featcols = [t[1] for t in actualfeatures]
        # print(featcols)
        featmap = {}
        for udfeat, sqlfeat in allfeatures.items():
            # print(udfeat, sqlfeat)
            if sqlfeat in featcols:
                featmap[udfeat] = sqlfeat

        self._featmap = featmap

    def new_connection(self):
        """Get new (transient) database connection."""
        return get_connection(self.dbfile)

    def fetch_aggregate_frequencies(self):
        """Fetch aggregate frequencies."""
        self.wordfreqs = adhoc_query(self.connection, 'select sum(frequency) from wordfreqs', verbose=True)
        self.lemmafreqs = adhoc_query(self.connection, 'select sum(lemmafreq) from lemmas', verbose=True)
        self.initfreqs = adhoc_query(self.connection, 'select sum(frequency) from initgramfreqs', verbose=True)
        self.finfreqs = adhoc_query(self.connection, 'select sum(frequency) from fingramfreqs', verbose=True)
        self.bifreqs = adhoc_query(self.connection, 'select sum(frequency) from bigramfreqs', verbose=True)
        # self.wbifreqs = adhoc_query(self.connection, 'select sum(frequency) from wordbigramfreqs', verbose=True)

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

    def featmap(self, reverse: bool = False) -> Dict:
        """Return feature map."""
        if reverse:
            fmap = {v: k for k, v in self._featmap.items()}
            return fmap
        return self._featmap

    # FIXME: move to query class
    def get_queryselects(self, table: str, useposx: bool = False) -> List:
        """Get applicable query selects."""
        cols = []

        dropcols = ['w.posx', 'w.id', 'w.featid',
                    'w.frequencyx',
                    'w.revform',
                    # 'w.hood', 'w.ambform',  # for now
                    'ft.featid', 'ft.feats', 'ft.pos', 'ft.posx',
                    'l.pos', 'l.lemma', 'l.comparts', 'l.lemmac',
                    # 'l.amblemma',
                    ]
        for col in self.columns[table]:
            if table == 'wordfreqs':
                usetable = 'w'
            elif table == 'features':
                usetable = 'ft'
            # elif table == 'forms':
            #    usetable = 'f'
            # elif table == 'lemmaforms':
            #    usetable = 'lf'
            elif table == 'lemmas':
                usetable = 'l'
            usecol = f'{usetable}.{col}'
            if usecol == 'w.pos':
                usecol = 'w.posx as pos' if useposx else 'w.pos'
            elif usecol == 'w.frequency':
                if useposx:
                    usecol = 'w.frequencyx as frequency'
            elif usecol in dropcols:
                continue
            cols.append(usecol)
        # print(table, cols)
        return cols


def write_freqs_to_db(dbc: DatabaseConnection,
                      freqs: Freqs):
    """Write frequencies to SQLite database."""
    connection = dbc.get_connection()
    cursor = connection.cursor()
    # cursor.execute('PRAGMA journal_mode=wal')
    # print('Cursor mode:', cursor.fetchall())

    # FIXME: try to do an upsert? (update/insert)
    template = "INSERT INTO %s (%s) values (%s)"
    itemplate = "INSERT OR IGNORE INTO %s (%s) values (%s)"

    featmap = dbc.featmap()
    wordfields = ['lemma', 'form', 'pos', 'posx', 'frequency', 'len',
                  'revform',
                  'feats', 'featid',
                  'hood']
    featfields = ['feats', 'pos']

    for feat in sorted(featmap.keys()):
        featfields.append(featmap[feat])

    insert_tpl = ', '.join(list(wordfields))
    values_tpl = ', '.join(['?' for _ in wordfields])

    insert_template = template % ('wordfreqs', insert_tpl, values_tpl)
    print(insert_template)

    wordvalues = []
    featvalues = []

    uqfeats = set()

    for key, freq in freqs[0].items():
        lemma, word, pos, feats = key
        posx = 'VERB' if pos == 'AUX' else pos
        revword = word[::-1]
        wordvals = [lemma, word, pos, posx, freq, len(word), revword, feats, 0, 0]
        featvals = [feats, pos]
        featdict = freqs[1][key]
        for feat in sorted(featmap.keys()):
            featval = '_'
            # print(key, freq, featdict)
            if isinstance(featdict, dict) and feat in featdict:
                # print(feat, featdict[feat])
                featval = featdict[feat]
            # print(key, freq, featdict, featval)
            # print(recvals)
            featvals.append(featval)
        # print(recvals)
        wordvalues.append(wordvals)
        if (pos, feats) in uqfeats:
            ...
        else:
            uqfeats.add((pos, feats))
            featvalues.append(featvals)

    print(wordvalues[0])
    print(featvalues[0])

    chunklen = 100000
    totwordchunks = math.ceil(len(wordvalues)/chunklen)

    print(f'Inserting {len(wordvalues)} rows in {totwordchunks} chunks...')
    print(insert_template)

    for chunk in tqdm(chunks(wordvalues, chunklen=chunklen),
                      total=totwordchunks):
        try:
            cursor.executemany(insert_template, chunk)
            connection.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            connection.rollback()
            break

    insert_tpl = ', '.join(list(featfields))
    values_tpl = ', '.join(['?' for _ in featfields])

    insert_template = itemplate % ('features', insert_tpl, values_tpl)

    totfeatchunks = math.ceil(len(featvalues)/chunklen)

    print(f'Inserting {len(featvalues)} rows in {totfeatchunks} chunks...')
    print(insert_template)

    for chunk in tqdm(chunks(featvalues, chunklen=chunklen),
                      total=totfeatchunks):
        try:
            cursor.executemany(insert_template, chunk)
            connection.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            connection.rollback()


# FIXME: make this a query class
# FIXME: get supported features from database connection?
def parse_query(query: str,
                revfeatmap: Dict = None,
                relfieldmap: Dict = None) -> Tuple[List[List[str]], List]:
    """Parse query to SQL key-values."""
    parts = query.lower().split('and')
    kvparts = []
    errors: List[str] = []

    numkeys = ['frequency', 'len',
               'lemmafreq', 'lemmalen', 'amblemma',
               'hood', 'ambform',
               'initrigramfreq', 'fintrigramfreq', 'bigramfreq']
    strkeys = ['lemma', 'lemmac', 'form', 'pos',
               # 'nouncase', 'nnumber',
               # 'tense', 'person', 'verbform',
               # 'posspers', 'possnum',
               'start', 'middle', 'end',
               'top',
               # 'derivation', 'clitic'  # these my be complex
               ]
    strkeys.extend(revfeatmap.keys())
    # logger.debug('Supported morphological features: %s', list(revfeatmap.keys()))
    formkeys = ['start', 'middle', 'end']
    boolkeys = ['compound']
    stroperators = ['=', '!=', 'like', 'in', 'notin']
    formoperators = ['=', '!=', 'in', 'notin']
    numoperators = ['=', '!=', '<', '>', '<=', '>=']

    numadd = ['rel' + k for k in numkeys if 'freq' in k]
    numkeys.extend(numadd)

    shortcuts = {
        'freq': 'frequency',
        'relfreq': 'relfrequency',
        'case': 'nouncase',
        'number': 'nnumber',
        # 'lemma': 'lemmac',
    }

    # FIXME: use a queue mechanism for this?
    for part in parts:
        try:
            part = re.sub(r'not\s+in', 'notin', part, re.I)
            vals = part.split()
            bols = [w for w in vals if w in boolkeys]

            isok = False

            if bols:
                if bols[0] == 'compound':
                    key = 'lemma'
                    value = '%#%'
                    # key = 'comparts'
                    # value = 0
                    if len(vals) > 1:
                        if vals[0] == 'not':
                            comparator = 'not like'
                            # comparator = '='
                            isok = True
                        else:
                            errors.append(f"Invalid query part: '{part.strip()}'")
                    else:
                        comparator = 'like'
                        # comparator = '>'
                        isok = True

                else:
                    errors.append(f"Invalid query part: '{part.strip()}'")

            else:
                key, comparator, value = vals
                value = value.strip("'").strip('"')
                if key == 'lemma' and comparator != 'like':
                    key = 'lemmac'
                key = shortcuts.get(key, key)

                isok = False

                if key in numkeys:
                    if comparator in numoperators:
                        # print(f'Num ok: {key} {comparator}')
                        try:
                            fv = float(value)
                            try:
                                if key.startswith('rel'):
                                    total = relfieldmap[key][0][0]
                                    scale = 1000 if key == 'relbigramfreq' else 1e6
                                    # print(value, fv, total, scale)
                                    value = fv / scale * total
                                    key = key[3:]
                                isok = True
                            except Exception as e:
                                logging.exception("Can't get relative frequency scaler for %s/%st: %s", key, value, e)
                                errors.append(f"Can't get relative frequency scaler for {key}/{value}")
                        except ValueError as ve:
                            logging.exception("Can't cast %s as float: %s", value, ve)
                            errors.append(f"Query value for key '{key}' not ok: '{value}' is not a number")
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                elif key in formkeys:
                    if comparator in formoperators:
                        isok = True
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # print(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # logger.debug("Query comparator for '%s' not ok: '%s'", key, comparator)
                elif key in strkeys:
                    if comparator in stroperators:
                        isok = True
                    else:
                        errors.append(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # print(f"Query comparator for '{key}' not ok: '{comparator}'")
                        # logger.debug("Query comparator for '%s' not ok: '%s'", key, comparator)
                else:
                    errors.append(f"Query key '{key}' not ok")
                    # print(f"Query key '{key}' not ok")

            if isok:
                kvparts.append([key, comparator, value])
        except ValueError as e:
            logging.exception(e)
            errors.append(f"Invalid query part: '{part.strip()}'")

    return kvparts, errors


indexorder = ['w.form', 'w.revform', 'w.frequency', 'w.lemma', 'w.len',
              'c.clitic',
              'n.nouncase',
              'd.derivation',
              ]

# fields that have good indexes
indexfields = {
    'w.frequency': 'idx_wordfreqs_freq_len',
    # 'w.form': 'idx_wordfreqs_freq_form',
    'w.form': 'idx_wordfreqs_form_freq',
    'w.lemma': 'idx_wordfreqs_freq_lemma',
    'w.revform': 'idx_wordfreqs_freq_revform',
    'w.len': 'idx_wordfreqs_freq_len',
}


def parse_querystring(querystr: str,
                      revfeatmap: Dict = None,
                      relfieldmap: Dict = None) -> Tuple[str, List, List, List, List, bool]:
    """Parse the query string."""
    queryparts, errors = parse_query(querystr, revfeatmap, relfieldmap)
    # print(queryparts)

    whereparts = []
    wherestr = ""
    args = []
    useposx = True

    indexers = []
    notlikeindexers = []

    features = revfeatmap.keys()
#    features = ['nouncase', 'nnumber',
#                'tense', 'person', 'verbform',
#                'posspers', 'possnum',
#                'derivation', 'clitic'
#                ]
    lemmas = ['lemmac', 'lemmalen', 'lemmafreq', 'amblemma', 'comparts']
    # lemmaforms = ['ambform']
    # forms = ['len', 'hood', 'start', 'middle', 'end']
    # forms = []
    separatetables = ['derivation', 'clitic', 'nouncase']

    # FIXME: use a queue mechanism for this?
    for andpart in queryparts:
        k, c, v = andpart
        if k == 'top':
            continue
        usetable = 'w'
        if k in separatetables:
            if c in ('in', '=') and v == '_':
                usetable = 'ft'
            elif c == '!=':
                usetable = 'ft'
            else:
                usetable = k[0]
            v = ','.join([w.title() for w in v.split(',')])
        elif k in features:
            v = ','.join([w.title() for w in v.split(',')])
            usetable = 'ft'
        elif k in lemmas:
            usetable = 'l'
#        elif k in lemmaforms:
#            usetable = 'lf'
#        elif k in forms:
#            usetable = 'f'
        elif k.endswith('freq'):
            usetable = k[0]
            k = 'frequency'
        if k == 'pos':
            v = v.upper()
        fullcol = f'{usetable}.{k}'
        # print(f'{fullcol},{k},{c},{v}')
        if fullcol in indexorder:
            if c in ['like', 'not like']:
                # % not at the beginning of string of like query: no forced indexing
                if not v.startswith('%'):
                    indexers.append(fullcol)
            else:
                notlikeindexers.append(fullcol)
                indexers.append(fullcol)

        if c in ['in', 'notin']:
            invals = [w.strip() for w in v.split(',')]
            if k in ['derivationx', 'cliticx']:
                # This is the old implementation
                # usetable = k[0]
                usetable = 'ft'
                subargs = []
                whereor = []
                for val in invals:
                    subargs.append(f'{val}%')
                    subargs.append(f'%,{val}%')
                    whereor.append(f'{usetable}.{k} LIKE ?')
                    whereor.append(f'{usetable}.{k} LIKE ?')
                whereparts.append(f"({' OR '.join(whereor)})")
                args.extend(subargs)
            elif k in separatetables:
                if usetable != 'ft':
                    usetable = k[0]
                # Separate table for derivations and clitics is better
                qmarks = ','.join(['?'] * len(invals))
                # select * from wordfreqs where not (feats glob '*Case=Nom*' OR feats glob '*Case=Par*') limit 1000;
                # FIXME: Search directly from feats in main table?
                if c == 'notin':
                    c = 'not in'
                    usetable = 'ft'
                    # usetable = 'w'
                    # orparts = " OR ".join([f"{usetable}.feats GLOB ?" for _ in invals])
                    # whereparts.append(f'NOT ({orparts})')
                    # args.extend([f'Case=*{_}*' for _ in invals])
                    # args.extend(invals)
                else:
                    whereparts.append(f'w.featid = {usetable}.featid')
                whereparts.append(f'{usetable}.{k} {c} ({qmarks})')
                # whereparts.append(f'w.lemma = {usetable}.lemma and w.form = {usetable}.form and w.posx = {usetable}.pos and w.feats = {usetable}.feats')
                args.extend(invals)
            else:
                if k == 'pos':
                    if 'AUX' in invals:
                        useposx = False
                    else:
                        k = 'posx'
                qmarks = ','.join(['?'] * len(invals))
                if c == 'notin':
                    c = 'not in'

                # FIXME: IN query, NOT IN query middle
                if k in ['start', 'end']:
                    whereor = []
                    usecol = 'form'
                    if k == 'end':
                        usecol = 'revform'
                        invals = [v[::-1] for v in invals]
                    invals = [v + '*' for v in invals]
                    # invals = [v + '%' for v in invals]
                    for v in invals:
                        if c == 'in':
                            # whereor.append(f'{usetable}.{usecol} LIKE ?')
                            whereor.append(f'{usetable}.{usecol} GLOB ?')
                        else:
                            # whereor.append(f'{usetable}.{usecol} NOT LIKE ?')
                            whereor.append(f'{usetable}.{usecol} NOT GLOB ?')
                    whereparts.append(f"({' OR '.join(whereor)})")
                    args.extend(invals)
                elif k == 'middle':
                    if c == 'in':
                        whereor = []
                        for v in invals:
                            whereorparts = []
                            whereorparts.append(f'{usetable}.form GLOB ?')
                            args.append(f'?*{v}*?')
                            whereorparts.append(f'{usetable}.form NOT GLOB ?')
                            args.append(v + "*")
                            whereorparts.append(f'{usetable}.revform NOT GLOB ?')
                            args.append(v[::-1] + "*")
                            whereor.append(f"({' AND '.join(whereorparts)})")
                        whereparts.append(f"({' OR '.join(whereor)})")
                    else:
                        for v in invals:
                            whereparts.append(f'instr({usetable}.form, ?) == 0')
                            args.append(v)
                else:
                    whereparts.append(f'{usetable}.{k} {c} ({qmarks})')
                    args.extend(invals)
        else:
            if k == 'middle':
                if c == '=':
                    whereparts.append(f'{usetable}.form GLOB ?')
                    args.append(f'?*{v}*?')
                    whereparts.append(f'{usetable}.form NOT GLOB ?')
                    args.append(v + "*")
                    whereparts.append(f'{usetable}.revform NOT GLOB ?')
                    args.append(v[::-1] + "*")
                else:
                    whereparts.append(f'instr({usetable}.form, ?) == 0')
                    args.append(v)
                continue

            if k in ['start', 'end']:
                if k == 'end':
                    usecol = 'revform'
                    args.append(v[::-1] + "*")
                else:
                    usecol = 'form'
                    args.append(v + '*')
                if c == '=':
                    whereparts.append(f'{usetable}.{usecol} GLOB ?')
                else:
                    whereparts.append(f'{usetable}.{usecol} NOT GLOB ?')
                continue

            if k == 'pos':
                if v == 'AUX':
                    useposx = False
                else:
                    k = 'posx'
            # FIXME: take inequality from the correct table (features)
            whereparts.append(f'{usetable}.{k} {c} ?')
            args.append(v)

    if len(whereparts) > 0:
        wherestr = "WHERE " + " AND ".join(whereparts)
    if useposx:
        wherestr = wherestr.replace('w.frequency', 'w.frequencyx')
        indexers = [i.replace('w.frequency', 'w.frequencyx') for i in indexers]
        notlikeindexers = [i.replace('w.frequency', 'w.frequencyx') for i in notlikeindexers]

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
        indexers.add(querypart)
        qs = []
        for queryval in querydict[querypart]:
            # if querypart == 'lemma':
            #    whereparts.append('l.lemmac = ?')
            # else:
            #     whereparts.append(f'w.{querypart} = ?')
            args.append(queryval)
            qs.append('?')
        if querypart == 'lemma':
            whereparts.append(f"l.lemmac IN ({ ','.join(qs) })")
        else:
            whereparts.append(f"w.{querypart} IN ({ ','.join(qs) })")
    wherestr = "WHERE (" + " OR ".join(whereparts) + ") "
    return wherestr, args, errors, list(indexers), []


def get_indexer(indexers: List,
                notlikeindexers: List,
                orderby: str,
                useposx: bool) -> str:
    """Possibly force indexer."""
    logger.debug('Indexers: %s', indexers)
    # print(f'Indexers: {indexers}')
    logger.debug('Not LIKE indexers: %s', notlikeindexers)
    # print(f'Not LIKE indexers: {notlikeindexers}')

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
        if useposx:
            windexedby = windexedby.replace('_freq', '_freqx')
        logger.debug('Force indexer other than autoindex: %s', windexedby)
    return windexedby


def get_querystring(query: Union[str, Dict] = None,
                    revfeatmap: Dict = None,
                    orderby: str = 'w.frequency',
                    relfieldmap: Dict = None,
                    defaultindex: bool = False) -> Tuple[str, List[str], List[str], str, bool]:
    """Get final query string and other things."""
    useposx = True
    if isinstance(query, str):
        logger.info('Query: %s', query)
        wherestr, args, errors, indexers, notlikeindexers, useposx = parse_querystring(query, revfeatmap, relfieldmap)
        # print(errors)
    elif isinstance(query, dict):
        defaultindex = True
        wherestr, args, errors, indexers, notlikeindexers = parse_querydict(query)

    if useposx:
        orderby = orderby.replace('w.frequency', 'w.frequencyx')
    argshow = args
    whereshow = wherestr
    if len(args) > 20:
        argshow = argshow[:20]
        argshow.append('...')
    if len(whereshow) > 200:
        whereshow = whereshow[:200] + ' ...'
    logger.info('Wherestring, arguments: %s, %s', whereshow, argshow)
    # print(wherestr, args)
    windexedby = "" if defaultindex else get_indexer(indexers, notlikeindexers, orderby, useposx)
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
                            newconnection: bool = False,
                            lemmas: bool = False,
                            # aggregate: bool = True,
                            grams: bool = False) -> Tuple[pd.DataFrame, int, str]:
    """Get frequencies as dataframe."""
    # FIXME: validate rowlimit

    connection = dbconnection.new_connection() if newconnection else dbconnection.connection

    # FIXME: orderstring takes posx into account
    orderstring = get_orderby(orderby)
    # table = 'wordfreqs'
    # wherestr = ""
    # args: List[str] = []

    relfieldmap = {
        'rellemmafreq': dbconnection.lemmafreqs,
        'relfrequency': dbconnection.wordfreqs,
        'relbigramfreq': dbconnection.bifreqs,
        'relinitgramfreq': dbconnection.initfreqs,
        'relfingramfreq': dbconnection.finfreqs,
    }

    revfeats = dbconnection.featmap(reverse=True)
    wherestr, args, errors, windexedby, useposx = get_querystring(query, revfeats,
                                                                  orderstring, relfieldmap, defaultindex)

    if errors:
        raise ValueError('\n'.join(errors))

    selects = dbconnection.get_queryselects('wordfreqs', useposx)
    if useposx:
        orderstring = orderstring.replace('w.frequency', 'w.frequencyx')
        # wherestr = wherestr.replace('w.frequency', 'w.frequencyx')

    if len(wherestr) == 0:
        return pd.DataFrame(), -1, 'No valid query string'

    groupby = ""
    # haveposx = [w for w in selects if 'posx' in w]
    # if len(haveposx) > 0:
    #    groupby = "group by w.lemma, w.form, w.posx, w.feats"

    addfrom = ""
    addjoins = ""

    lindexedby = ""
    # if 'lemmac' in wherestr:
    #    lindexedby = "indexed by lemmas_lemmac_pos"
    # windexedby = "indexed by idx_wordfreqs_form_freqx"

    # jointables = ["wordfreqs w", "features ft", "forms f"]
    # jointables = ["wordfreqs w", "features ft"]
    fromtable = f"wordfreqs w {windexedby}, features ft"
    # fromtable = f"wordfreqs w {windexedby}, features ft, forms f"
    # fromtable = f"wordfreqs w, features ft"

    wherestr += " AND w.featid = ft.featid"
    # wherestr += " AND w.featid = ft.featid AND w.form = f.form"

    if (addfeats := dbconnection.get_queryselects('features')):
        selects.extend(addfeats)
    # if (addforms := dbconnection.get_queryselects('forms')):
    #    selects.extend(addforms)

    if lemmas:
        # fromtable += ", lemmas l indexed by lemmas_lemmac_pos"
        fromtable += f", lemmas l {lindexedby}"
        wherestr += " AND w.lemma = l.lemma AND w.posx = l.pos"
        selects.extend(dbconnection.get_queryselects('lemmas'))

#    for table in jointables:
#        if table == fromtable:
#            continue

    if 'd.derivation' in wherestr:
        addfrom += ", derivations d"
        wherestr += " AND w.featid = d.featid"
    if 'c.clitic' in wherestr:
        addfrom += ", clitics c"
        wherestr += " AND w.featid = c.featid"
    if 'n.nouncase' in wherestr:
        addfrom += ", nouncases n"
        wherestr += " AND w.featid = n.featid"

#    if lemmas:
#        selects.extend(dbconnection.get_queryselects('lemmas'))
#        addjoins += ' LEFT JOIN lemmas l ON w.lemma = l.lemma AND w.posx = l.pos'

        # selects.append(1-lf.formpct as ambform)
        # addjoins += ' LEFT JOIN lemmaforms lf ON w.lemma = lf.lemma AND w.form = lf.form AND w.posx = lf.pos'

    if grams:
        aliases = ['i', 'e', 'b']
        names = ['initgramfreq', 'fingramfreq', 'bigramfreq']
        tables = ['initgramfreqs', 'fingramfreqs', 'wordbigramfreqs']
        comps = ['substr(w.form, 1, 3)', 'substr(w.form, -3, 3)', 'w.form']

        for alias, aname, atable, wordcomp in zip(aliases, names, tables, comps):
            # print(alias, aname, atable, wordcomp)
            if alias in 'ie':
                selects.append(f'iif(length(w.form) > 3, {alias}.frequency, 0) as {aname}')
            else:
                selects.append(f'{alias}.frequency as {aname}')
            addjoins += f' LEFT JOIN {atable} {alias} ON {alias}.form = {wordcomp}'

    userowlimit = int(dbconnection.rowlimit() * 1.5) if useposx else dbconnection.rowlimit()
    sqlstr = f'SELECT {", ".join(selects)} FROM {fromtable} {addfrom} {addjoins} {wherestr} {groupby} ORDER BY {orderstring} LIMIT {userowlimit}'
    whereshow = wherestr
    if len(wherestr) > 200:
        whereshow = wherestr[:200] + ' ... [WHERE string arguments cut]'
    sqlshow = f'SELECT {", ".join(selects)} FROM {fromtable} {addfrom} {addjoins} {whereshow} {groupby} ORDER BY {orderstring} LIMIT {userowlimit}'
    logger.debug('SQL: %s', sqlshow)
    argshow = args
    if len(args) > 20:
        argshow = args[:20]
        argshow.append('...')
    logger.debug('Arguments: %s', argshow)
    # print(sqlstr)
    # print(args)

    querystatus = 0
    querymessage = 'success'

    try:
        explainer = pd.read_sql_query('explain query plan ' + sqlstr,
                                      connection,
                                      params=args)
        if len(explainer) > 20:
            showex = explainer[:20].copy()
            showex.loc[len(showex)] = [len(explainer), '-1', 0, '[Rest of output cut]']
            logger.debug('Query plan:\n%s', tabulate(showex, headers=explainer.columns))
        else:
            logger.debug('Query plan:\n%s', tabulate(explainer, headers=explainer.columns))

        starttime = time.perf_counter()
        sql_query = pd.read_sql_query(sqlstr,
                                      connection,
                                      params=args)

        df = pd.DataFrame(sql_query)
        if useposx:
            df = df.drop_duplicates(subset=['lemma', 'form', 'pos', 'feats'], keep='last').reset_index().drop('index', axis=1)
            df = df[:dbconnection.rowlimit()]
        df = reorder_columns(df).rename({'nouncase': 'case', 'nnumber': 'number'}, axis=1)

        endtime = time.perf_counter()
        logger.info('%d rows returned in %.1f seconds', len(df), endtime - starttime)
        # print()
        # print(f'{len(df)} rows returned in {endtime - starttime:.1f} seconds')

    except DatabaseError as e:
        logger.error(str(e))
        # print(str(e))
        _, errmsg = str(e).split(': ', 1)
        logger.error(errmsg)
        # print(errmsg)
        logging.exception(e)
        df = pd.DataFrame()
        querymessage = errmsg

    return df, querystatus, querymessage


def reorder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder dataframe columns."""
    ordermap = {
        'lemma': ['lemmalen', 'lemmafreq', 'amblemma'],
        'frequency': ['bigramfreq', 'initgramfreq', 'fingramfreq'],
        'len': ['hood', 'ambform']
    }
    columns = list(df.columns)
    for col, modlist in ordermap.items():
        anchoridx = columns.index(col)
        # print(col, anchoridx)
        addidx = 1
        for modcol in modlist:
            if modcol in columns:
                newidx = anchoridx + addidx
                # print(modcol, newidx)
                columns.remove(modcol)
                columns.insert(newidx, modcol)
                addidx += 1
            # print(columns)
    df = df.reindex(columns=columns)
    return df


def add_relative_frequencies(dbc: DatabaseConnection,
                             df: pd.DataFrame,
                             scale: float = 1e6,
                             drop: bool = False) -> pd.DataFrame:
    """Add relative frequencies."""
    resdf = df.copy()
    fieldmap = {
        'lemmafreq': dbc.lemmafreqs,
        'frequency': dbc.wordfreqs,
        'bigramfreq': dbc.bifreqs,
        'initgramfreq': dbc.initfreqs,
        'fingramfreq': dbc.finfreqs,
        }
    columns = df.columns
    addidx = 0
    for k, v in fieldmap.items():
        try:
            if k not in columns:
                continue
            kidx = list(columns).index(k)
            # print(k, kidx, v)
            # print(df[k], v, scale)
            if k == 'bigramfreq':
                scale = 1000
            newcol = np.array(df[k]) / v * scale
            # print(df[k], v, scale, newcol[0])
            # print(f'Inserting column rel{k} in position {kidx + 1 + addidx}')
            resdf.insert(kidx + 1 + addidx, f'rel{k}', newcol[0])
            if drop:
                resdf = resdf.drop(k, axis=1)
            else:
                addidx += 1
        except ValueError as e:
            # ignore
            print(e)
    return resdf


def get_wordinput(filename: str) -> Dict[str, List]:
    """Get word input for lemma, form or nonword."""
    wordinput = defaultdict(list)
    cats = ['lemma', 'form', 'nonword']
    got_type = None

    file_contents = get_file_contents(filename)
    for line in file_contents:
        # print(line.strip())
        try:
            if len(line.strip()) == 0:
                continue
            if line.startswith('#'):
                if not got_type:
                    # print('b', re.match('.*type\s*=\s*(\w+)', line.strip(), re.M))
                    if (matches := re.match('.*type\s*=\s*(\w+)', line.strip())) is not None:
                        got_type = matches.group(1)
                        if got_type not in cats:
                            # print(f'Invalid type: {got_type}')
                            got_type = None
                continue
            if got_type:
                kw = line.strip()
                wordinput[got_type].append(kw)
        except Exception as e:
            print(f'Error with line: {line}', e)
    # print(wordinput)
    return wordinput


def get_file_contents(filename: str) -> List[str]:
    """Get word input with specific encoding."""
    encodings = ['utf-8-sig', 'iso-8859-1']
    for encoding in encodings:
        try:
            logger.debug('Opening %s with encoding %s', filename, encoding)
            with open(filename, 'r', encoding=encoding) as f:
                lines = f.readlines()
                return lines
        except Exception as e:
            logger.exception(e)

    return []


def get_unword_bigrams(dbc: DatabaseConnection,
                       data: Dict[str, List]) -> pd.DataFrame:
    """Get bigram frequencies for nonwords."""
    formgrams = defaultdict(list)
    fetchbigs = set()
    for form in data['nonword']:
        grams = [form[i:j] for i, j in zip(range(0, len(form)-1), range(2, len(form)+1))]
        fetchbigs.update(grams)
        formgrams[form] = grams

    # print(fetchbigs)
    # print(formgrams)
    qmarks = ','.join([f"'{w}'" for w in fetchbigs])
    sql = f"select * from bigramfreqs where form in ({qmarks})"
    bigdf = adhoc_query(dbc.get_connection(), sql, todf=True)
    resdf = pd.DataFrame(formgrams.keys(), columns=['form'])

    formbigs = []
    for _idx, row in resdf.iterrows():
        form = row.form
        bgsum = 0
        for bg in formgrams[form]:
            bgsum += bigdf[bigdf.form == bg].frequency.values[0]
        # print(form, bgsum, bgsum / len(form))
        formbigs.append(int(bgsum / len(form)))

    # relbigs = np.array(formbigs) / dbc.wbifreqs * 1e6
    # print(wordbigramtotal, relbigs)
    resdf['bigramfreq'] = formbigs
    # resdf['relbigramfreq'] = relbigs[0]

    return resdf


def filter_dataframe(dbc: DatabaseConnection,
                     df: pd.DataFrame,
                     querystring: str) -> pd.DataFrame:
    """Filter dataframe based on querystring."""
    resdf = df.copy()
    relfieldmap = {
        'rellemmafreq': dbc.lemmafreqs,
        'relfrequency': dbc.wordfreqs,
        'relbigramfreq': dbc.bifreqs,
        'relinitgramfreq': dbc.initfreqs,
        'relfingramfreq': dbc.finfreqs,
    }
    revfeats = dbc.featmap(reverse=True)
    numkeys = ['frequency', 'len',
               'lemmafreq', 'lemmalen', 'amblemma',
               'hood', 'ambform',
               'initrigramfreq', 'fintrigramfreq', 'bigramfreq']
    formkeys = ['start', 'middle', 'end']

    top = -1

    # Reverse shortcuts
    shortcuts = {
        # 'freq': 'frequency',
        # 'relfreq': 'relfrequency',
        'case': 'nouncase',
        'number': 'nnumber',
        # 'lemma': 'lemmac',
    }
    revs = dict((v, k) for k, v in shortcuts.items())

    try:
        logger.debug('Querying dataframe for: %s', querystring)
        _wherestr, _args, errors, _indexers, _notlikeindexers, _useposx = parse_querystring(querystring, revfeats, relfieldmap)
        if len(errors) > 0:
            errstr = '\n'.join(errors)
            raise ValueError(errstr)
        # This produces an error if the query string is invalid
        qlist2, _errors = parse_query(querystring, revfeats, relfieldmap)
        resdf['lemmac'] = resdf.lemma.str.replace('#', '')
        for feat in qlist2:
            useval: Union[List[str], str] = ''
            format_string = None
            key, op, value = feat
            key = revs.get(key, key)
            if key == 'top':
                top = int(value)
                continue
            keyadd = ""
            if op == 'notin':
                op = 'not in'
            if op in ['not in', 'in']:
                useval = value.split(',')
            elif key in numkeys:
                useval = value
            elif key in formkeys:
                useval = [value]
            else:
                useval = f"'{value.lower()}'"
                keyadd = ".str.lower()"
            if key in formkeys:
                if op in ('=', 'in'):
                    if key == 'start':
                        format_string = " | ".join([f"form.str.startswith('{c}')" for c in useval])
                    elif key == 'end':
                        format_string = " | ".join([f"form.str.endswith('{c}')" for c in useval])
                    else:
                        strings = []
                        for c in useval:
                            str1 = f"form.str.contains('{c}')"
                            str2 = f"~form.str.startswith('{c}')"
                            str3 = f"~form.str.endswith('{c}')"
                            str_comb = f"({str1} & {str2} & {str3})"
                            strings.append(str_comb)
                        format_string = '|'.join(strings)
                else:
                    if key == 'start':
                        format_string = " & ".join([f"~form.str.startswith('{c}')" for c in useval])
                    elif key == 'end':
                        format_string = " & ".join([f"~form.str.endswith('{c}')" for c in useval])
                    else:
                        format_string = " & ".join([f"~form.str.contains('{c}')" for c in useval])
            else:
                format_string = f"{key}{keyadd} {op} {useval}"
                if op == '=':
                    format_string = f"{key}{keyadd} == {useval}"
                elif op == 'like':
                    useval = useval.replace('%', '')
                    format_string = f"{key}.str.contains({useval}, case=False)"
                elif op == 'not like':
                    useval = useval.replace('%', '')
                    format_string = f"~{key}.str.contains({useval}, case=False)"

            logger.debug("Using format_string: %s", format_string)
            len1 = len(resdf)
            resdf = resdf.query(format_string)
            len2 = len(resdf)
            logger.debug("Filtering dataframe with '%s': %d -> %d results",
                         format_string, len1, len2)

    except Exception as e:
        raise e
    resdf = resdf.drop('lemmac', axis=1)
    if top > 0:
        forms = resdf.groupby(['form']).aggregate({'form': 'count'})
        for form, row in forms.iterrows():
            # print(idx, row)
            ct = row['form']
            if ct > top:
                # print(form, ct)
                format_string = f"form.str.lower() == '{form}'"
                # print(format_string)
                xx = resdf.query(format_string).sort_values('frequency',
                                                            ascending=False)
                dropindexes = xx[top:].index
                # print(xx)
                logger.debug("Filter: dropping %d least frequent indexes for form %s",
                             len(dropindexes), form)
                # print(dropindexes)
                resdf = resdf.drop(dropindexes)
    return resdf
