"""Convert text data to conllu format."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from typing import Dict, List, Iterator, Tuple
# import sys
import argparse
import logging
import logging.config
import math
from collections import Counter
import sqlite3
from sqlite3 import IntegrityError
import pandas as pd
from tqdm.autonotebook import tqdm
from symspellpy import SymSpell, Verbosity
from uralicNLP import uralicApi
from lib import dbutil, buildutil

wm2logconfig = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'formatters': {
        'default_formatter': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%d.%m.%Y %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
            'level': 'DEBUG'
        },
    },
}

logging.config.dictConfig(wm2logconfig)
logger = logging.getLogger('wm2')

# FIXME: if table already has data.. empty?


def record_pos_frequency(sqlcon: sqlite3.Connection):
    """Aggregate frequency for pos/posx."""
    # dbutil.adhoc_query(sqlcon, "alter table wordfreqs add column frequencyx INT default 0")
    # dbutil.adhoc_query(sqlcon, "update wordfreqs set frequencyx = frequency")

    updatestatement = "update wordfreqs set frequencyx = frequency"
    dbutil.adhoc_query(sqlcon, updatestatement, verbose=True)

    print('Fetching information for recording aggregate frequencies...')
    posdf = dbutil.adhoc_query(sqlcon, "select id, lemma, form, frequency, frequencyx, pos, posx, feats from wordfreqs where posx = 'VERB'", todf=True)

    posagg1 = posdf.groupby(['lemma', 'form',
                             'posx', 'feats']).aggregate({'id': 'first', 'pos': 'first', 'frequency': 'sum'},
                                                         ).sort_values(by='id').reset_index()
    posagg2 = posdf.groupby(['lemma', 'form',
                             'posx', 'feats']).aggregate({'id': 'last', 'pos': 'last', 'frequency': 'sum'},
                                                         ).sort_values(by='id').reset_index()

    posagg = posagg1.merge(posagg2, how='outer').sort_values(by='id').reset_index()
    posagg = posagg.reindex(columns=['id', 'lemma', 'form', 'frequency', 'frequencyx', 'pos', 'posx', 'feats'])

    posdf2 = posdf.copy().sort_values(by='id').reset_index()
    posdf2.frequencyx = posagg.frequency

    # Only update the changed values
    changedf = posdf2[(posdf2.frequency != posdf2.frequencyx)].sort_values(by='frequencyx', ascending=False)
    updatestatement = "update wordfreqs set frequencyx = ? where id = ?"
    updates = [[row.frequencyx, row.id] for _idx, row in changedf.iterrows()]
    cursor = sqlcon.cursor()

    try:
        cursor.executemany(updatestatement, updates)
        sqlcon.commit()
    except IntegrityError as e:
        # this is not ok
        logging.exception(e)
        sqlcon.rollback()


def generate_form_aggregates(sqlcon: sqlite3.Connection):
    """Generate form aggregates."""
    print('Checking table lemmaforms...')
    have = dbutil.adhoc_query(sqlcon, 'select * from lemmaforms limit 1')
    if len(have) > 0:
        print('Table lemmaforms already has content, not inserting')
    else:
        print('Inserting aggregates into lemmaforms table...')
        formsql = "insert into lemmaforms select lemma, form, posx as pos, sum(frequency) as frequency, 0 as formpct, 0 as formsum from wordfreqs group by lemma, form, posx order by frequency desc"
        dbutil.adhoc_query(sqlcon, formsql)

    formcounts = "update lemmaforms set formsum = (select sum(l.frequency) from lemmaforms l where l.form = lemmaforms.form group by form)"
    dbutil.adhoc_query(sqlcon, formcounts, verbose=True)

    formpct = "update lemmaforms set formpct = frequency / cast(formsum as real)"
    dbutil.adhoc_query(sqlcon, formpct, verbose=True)

    print('Checking table forms...')
    have = dbutil.adhoc_query(sqlcon, 'select * from forms limit 1')
    if len(have) > 0:
        print('Table forms already has content, not inserting')
    else:
        print('Inserting aggregates into forms table...')
        formsql = "insert into forms select form, sum(frequency) as frequency, count(*) as numforms, 0 as hood from lemmaforms group by form order by frequency desc"
        dbutil.adhoc_query(sqlcon, formsql)


def record_hood(sqlcon: sqlite3.Connection, counts: Dict):
    """Record neighbourhood to forms table."""
    updatestatement = "update forms set hood = ? where form = ?"
    updvalues = []
    for form, hood in counts.items():
        updvalues.append([hood, form])

    chunklen = 1000
    total = math.ceil(len(updvalues)/chunklen)
    cursor = sqlcon.cursor()
    print(f'Updating {len(updvalues)} hood values to forms table...')
    for chunk in tqdm(dbutil.chunks(updvalues, chunklen=chunklen), total=total):
        try:
            cursor.executemany(updatestatement, chunk)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            sqlcon.rollback()


def get_form_suggestions(df: pd.DataFrame, sym_spell) -> Iterator[Tuple[str, List[Tuple[str, int]]]]:
    """Get iterator for form suggestions."""
    # sym_spell = SymSpell(max_dictionary_edit_distance=1)
    autofreq = 10000
    minfreq = 100

    for _idx, row in tqdm(df.iterrows(), total=len(df)):
        form = row.form
        # freq = row.frequency
        suggestions = sym_spell.lookup(form, Verbosity.ALL)
        formfinals = []

        # Drop suggestion when 1) low frequency and 2) no morph analysis
        for suggestion in suggestions:
            ok = False
            res = []
            if suggestion.distance == 0:
                ...
            elif suggestion.count >= autofreq:
                ok = True
            elif suggestion.count < minfreq:
                ...
            else:
                res = uralicApi.analyze(suggestion.term, "fin")
                if len(res) > 0:
                    ok = True
            if ok:
                formfinals.append((suggestion.term, suggestion.count))

        yield form, formfinals


def generate_hood(sqlcon: sqlite3.Connection):
    """Generate neighbourhood to forms table."""
    print('Loading form information for neighbourhood calculation...')
    sdf = dbutil.adhoc_query(sqlcon, "select * from forms", todf=True)
    sym_spell = SymSpell(max_dictionary_edit_distance=1)

    print('Generating spelling dictionary...')
    for _idx, row in tqdm(sdf.iterrows(), total=len(sdf)):
        form = row.form
        freq = row.frequency
        sym_spell.create_dictionary_entry(form, freq)

    # autofreq = 10000
    # minfreq = 100
    finals = {}  # type: ignore

    print('Generating edit distances...')
    for form, formfinals in get_form_suggestions(sdf, sym_spell):
        finals[form] = formfinals

#    for _idx, row in tqdm(sdf.iterrows(), total=len(sdf)):
#        form = row.form
#        freq = row.frequency
#        suggestions = sym_spell.lookup(form, Verbosity.ALL)
#        formfinals = []
#
#        # Drop suggestion when 1) low frequency and 2) no morph analysis
#        for suggestion in suggestions:
#            ok = False
#            res = []
#            if suggestion.distance == 0:
#                ...
#            elif suggestion.count >= autofreq:
#                ok = True
#            elif suggestion.count < minfreq:
#                ...
#            else:
#                res = uralicApi.analyze(suggestion.term, "fin")
#                if len(res) > 0:
#                    ok = True
#            if ok:
#                formfinals.append((suggestion.term, suggestion.count))
#        finals[form] = formfinals
#        # break

    levdict = Counter()  # type: ignore
    hamdict = Counter()  # type: ignore

    for key, analysis in finals.items():
        levs = [w for w, _ in analysis]
        hams = [w for w, _ in analysis if len(w) == len(key)]
        levdict[key] = len(levs)
        hamdict[key] = len(hams)

    # print(levdict)
    # print(hamdict)
    record_hood(sqlcon, hamdict)


def update_table(sqlcon: sqlite3.Connection,
                 table: str,
                 statement: str,
                 values: List,
                 chunklen: int = 1000):
    """Run update statements."""
    ...
    total = math.ceil(len(values)/chunklen)
    cursor = sqlcon.cursor()
    print(f'Updating {len(values)} values to {table} table...')
    print(statement)
    print(values[0])
    for chunk in tqdm(dbutil.chunks(values, chunklen=chunklen), total=total):
        try:
            cursor.executemany(statement, chunk)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            sqlcon.rollback()


def copy_to_wordfreqs(sqlcon: sqlite3.Connection):
    """Copy info to wordfreqs table."""
    fetchst = "select hood, form from forms"
    data = dbutil.adhoc_query(sqlcon, fetchst)
    print('Getting hood information from forms table...')
    updatestatement = "update wordfreqs set hood = ? where form = ? and hood = 0"
    update_table(sqlcon, 'wordfreqs', updatestatement, data)

    fetchst = "select 1-formpct, lemma, form, pos from lemmaforms"
    data = dbutil.adhoc_query(sqlcon, fetchst)
    print('Getting ambform information from lemmaforms table...')
    updatestatement = "update wordfreqs set ambform = ? where lemma = ? and form = ? and posx = ? and ambform = 0"
    update_table(sqlcon, 'wordfreqs', updatestatement, data)


def generate_lemma_aggregates(sqlcon: sqlite3.Connection):
    """Generate lemma aggregates."""
    print('Checking table lemmas...')
    have = dbutil.adhoc_query(sqlcon, 'select * from lemmas limit 1')
    if len(have) > 0:
        print('Table lemmas already has content, not inserting')
    else:
        print('Inserting aggregates into lemmas table...')
        lemmasql = "insert into lemmas select lemma, replace(lemma, '#', '') as lemmac, posx as pos, sum(frequency) as lemmafreq, length(lemma) as lemmalen, 0 as amblemma, 0 as comparts from wordfreqs group by lemma, posx order by lemmafreq desc"
        dbutil.adhoc_query(sqlcon, lemmasql)
        updatestatement = "update lemmas set lemmalen = length(lemmac)"
        dbutil.adhoc_query(sqlcon, updatestatement)

    lemmadf = dbutil.adhoc_query(sqlcon, "select lemma from lemmas where instr(lemma, '#') > 0", todf=True, verbose=True)
    updatestatement = "update lemmas set comparts = ? where lemma = ?"
    insvalues = []
    for lemma in lemmadf.lemma:
        compval = lemma.count('#')
        insvalues.append([compval, lemma])

    chunklen = 10000
    total = math.ceil(len(insvalues)/chunklen)
    cursor = sqlcon.cursor()
    print(f'Updating {len(lemmadf)} compound lemmas')
    for chunk in tqdm(dbutil.chunks(insvalues, chunklen=chunklen), total=total):
        try:
            cursor.executemany(updatestatement, chunk)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            sqlcon.rollback()

    print('Generating amblemma percentages...')
    lffreqsql = "select lf.lemma, lf.pos, sum(lf.frequency) as lfreq, l.lemmafreq, (select sum(lx.frequency) from lemmaforms lx, forms fx where (fx.numforms = 1 OR lx.formpct > 0.99) and lx.form = fx.form and lx.lemma = lf.lemma and lx.pos = lf.pos group by lx.lemma, lx.pos) as numfreq from lemmaforms lf, lemmas l where lf.lemma = l.lemma and lf.pos = l.pos group by lf.lemma, lf.pos order by lfreq desc"
    lffreqdf = dbutil.adhoc_query(sqlcon, lffreqsql, todf=True, verbose=True)
    print(f'Fetched {len(lffreqdf)} lemma, pos frequencies')

    l2 = lffreqdf.copy()
    l2['amblemma'] = (l2.lfreq - l2.numfreq) / l2.lfreq
    l2.loc[l2.amblemma.isnull(), 'amblemma'] = 1
    updvalues = l2[['amblemma', 'lemma', 'pos']].values

#    updvalues2 = []
#    for _idx, row in lffreqdf.iterrows():
#        lemma = row.lemma
#        pos = row.pos
#        tot = row.lemmafreq
#        uniques = row.numfreq
#        if math.isnan(uniques):
#            pct = 1
#        else:
#            pct = (tot-uniques)/tot
#        # print(lemma, pos, tot, uniques, pct)
#        updvalues2.append([pct, lemma, pos])

    # print(lffreqdf[lffreqdf.lemma == 'ilman'][:10])
    # print(lffreqdf[lffreqdf.numfreq.isnull()][:10])

    updatestatement = "update lemmas set amblemma = ? where lemma = ? and pos = ?"
    # chunklen = 1
    print('Updating amblemma frequencies...')
    total = math.ceil(len(updvalues)/chunklen)
    cursor = sqlcon.cursor()
    for chunk in tqdm(dbutil.chunks(updvalues, chunklen=chunklen), total=total):
        try:
            cursor.executemany(updatestatement, chunk)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            print(chunk)
            logging.exception(e)
            sqlcon.rollback()


def add_feat_pos_indexes(sqlcon: sqlite3.Connection):
    """Add feats/pos indexes for building features tables."""
    idx_sql = 'CREATE INDEX IF NOT EXISTS idx_wordfreqs_feats_pos_featid_partial on wordfreqs(feats, pos, featid) where featid = 0'
    dbutil.adhoc_query(sqlcon, idx_sql)


def add_feature_index(sqlcon: sqlite3.Connection):
    """Add feature index to wordfreqs table."""
    # print('Adding feature index...')
    featuresql = "select featid, feats, pos from features"
    features = dbutil.adhoc_query(sqlcon, featuresql, todf=True, verbose=True)
    have = dbutil.adhoc_query(sqlcon, 'select count(*) from wordfreqs where featid = 0')
    if have[0][0] == 0:
        print('No feature ids to update')
    else:
        print("Updating featid to wordfreqs table...")
        updatestatement = "update wordfreqs set featid = ? where feats = ? and pos = ? and featid = 0"
        insvalues = []
        for featid, feats, pos in tqdm(zip(features.featid, features.feats, features.pos), total=len(features)):
            insvalues.append([featid, feats, pos])

            chunklen = 100
            # total = math.ceil(len(insvalues)/chunklen)
            cursor = sqlcon.cursor()
            for chunk in dbutil.chunks(insvalues, chunklen=chunklen):
                try:
                    cursor.executemany(updatestatement, chunk)
                    sqlcon.commit()
                except IntegrityError as e:
                    # this is not ok
                    logging.exception(e)
                    sqlcon.rollback()


# def drop_indexes(sqlcon: sqlite3.Connection,
#                 match: str):
#    """Drop matching indexes."""
#    indexes = dbutil.adhoc_query(sqlcon, "SELECT * FROM sqlite_master WHERE type = 'index'")
#    droplist = []
#    for idx in indexes:
#        idxname = idx[1]
#        if match in idxname:
#            droplist.append(idxname)
#    for idx in droplist:
#        print(f'Dropping index {idx}...')
#        sqlstr = f'DROP INDEX {idx}'
#        dbutil.adhoc_query(sqlcon, sqlstr)


# def add_indexes(sqlcon: sqlite3.Connection,
#                sqlfile: str):
#    """Add indexes from a SQL file."""
#    cursor = sqlcon.cursor()
#    print(f'Adding indexes from {sqlfile}...')
#    with open(f'sql/{sqlfile}', 'r', encoding='utf8') as sschemafile:
#        ssqldata = sschemafile.read()
#        cursor.executescript(ssqldata)
#        sqlcon.commit()


def create_feature_table(sqlcon: sqlite3.Connection, table: str, feat: str):
    """Populate a separate feature table from features."""
    inserttpl = 'INSERT INTO %s (featid, %s) values (?, ?)'
    print(f'Checking table {table}...')
    haveit = dbutil.adhoc_query(sqlcon, f'select * from {table} limit 1')
    if len(haveit) > 0:
        print(f'Table {table} already has content, not inserting')
    else:
        print(f'Fetching content for {table} table...')
        fetchsql = f"select featid, {feat} from features where {feat} != '_'"
        res = dbutil.adhoc_query(sqlcon, fetchsql)
        values = []

        cursor = sqlcon.cursor()
        print(f'Inserting content for {table} table...')
        for row in tqdm(res):
            gotfeatid, gotfeat = row
            for choice in gotfeat.split(','):
                values.append([gotfeatid, choice])
        try:
            insertsql = inserttpl % (table, feat)
            cursor.executemany(insertsql, values)
            sqlcon.commit()
        except IntegrityError as ex:
            logging.exception(ex)
            sqlcon.rollback()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='generate-helper-tables',
                                     description='Generate helper tables and columns')

    parser.add_argument('-d', '--dbfile',
                        type=str,
                        required=True,
                        help='DBfile')

    # parser.add_argument('-n', '--newfile',
    #                    action='store_true',
    #                    help='Import table schema')

    parser.add_argument('-a', '--all',
                        action='store_true',
                        help='All tables')

    parser.add_argument('-p', '--posx',
                        action='store_true',
                        help='Record aggregate posx frequency')

    parser.add_argument('-F', '--features',
                        action='store_true',
                        help='Generate features tables')

    parser.add_argument('-l', '--lemmas',
                        action='store_true',
                        help='Calculate lemma aggregates')

    parser.add_argument('-f', '--forms',
                        action='store_true',
                        help='Calculate form aggregates')

    parser.add_argument('-H', '--hood',
                        action='store_true',
                        help='Calculate orthographic neighbourhood')

    parser.add_argument('-c', '--copy',
                        action='store_true',
                        help='Copy computed forms information to wordfreqs table')

    args = parser.parse_args()

    dbc = dbutil.DatabaseConnection(args.dbfile, aggregates=False)
    sqlconn = dbc.get_connection()

    print(f'Generating helper table info to {args.dbfile}')
    buildutil.add_schema(sqlconn, "wordfreqs_indexes.sql")

    if args.forms or args.all:
        print('Adding forms.sql...')
        with open('sql/forms.sql', 'r', encoding='utf8') as schemafile:
            ccursor = sqlconn.cursor()
            sqldata = schemafile.read()
            ccursor.executescript(sqldata)

    if args.lemmas or args.all:
        print('Adding lemmas.sql...')
        with open('sql/lemmas.sql', 'r', encoding='utf8') as schemafile:
            ccursor = sqlconn.cursor()
            sqldata = schemafile.read()
            ccursor.executescript(sqldata)

    if args.features or args.all:
        print('Adding features.sql...')
        with open('sql/features.sql', 'r', encoding='utf8') as schemafile:
            ccursor = sqlconn.cursor()
            sqldata = schemafile.read()
            ccursor.executescript(sqldata)

    # These two are necessary for the operation of the database
    if args.posx or args.all:
        buildutil.drop_indexes(sqlconn, "_freqx")
        record_pos_frequency(sqlconn)
        buildutil.add_schema(sqlconn, "wordfreqs_indexes.sql")

    if args.features or args.all:
        # buildutil.drop_indexes(sqlconn, "_wordfreqs_featid")
        buildutil.add_features(dbc)
        add_feat_pos_indexes(sqlconn)
        add_feature_index(sqlconn)
        buildutil.drop_indexes(sqlconn, "featid_partial")
        # buildutil.add_schema(sqlconn, "wordfreqs_indexes.sql")
        create_feature_table(sqlconn, 'derivations', 'derivation')
        create_feature_table(sqlconn, 'clitics', 'clitic')
        create_feature_table(sqlconn, 'nouncases', 'nouncase')

    # These are optional
    # Forms aggregates need to be present before amblemma is calculated
    if args.forms or args.all:
        generate_form_aggregates(sqlconn)

    if args.lemmas or args.all:
        generate_lemma_aggregates(sqlconn)

    if args.hood or args.all:
        generate_hood(sqlconn)

    if args.copy:
        copy_to_wordfreqs(sqlconn)
