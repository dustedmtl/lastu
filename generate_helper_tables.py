#!/usr/bin/env python3
"""Convert text data to conllu format."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
import sys
import argparse
import logging
import math
from collections import Counter
# import pandas as pd
import sqlite3
from sqlite3 import IntegrityError
from tqdm.autonotebook import tqdm
from symspellpy import SymSpell, Verbosity
from uralicNLP import uralicApi
from lib import dbutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('build-database')

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

# parser.add_argument('-p', '--posx',
#                    action='store_true',
#                    help='Create posx column')

# parser.add_argument('-r', '--reverse',
#                    action='store_true',
#                    help='Create reverse column')

# parser.add_argument('-c', '--compound',
#                    action='store_true',
#                    help='Create compound column')

parser.add_argument('-f', '--forms',
                    action='store_true',
                    help='Forms tables')

parser.add_argument('-l', '--lemmas',
                    action='store_true',
                    help='Lemmas tables')

parser.add_argument('-F', '--features',
                    action='store_true',
                    help='Features tables')

parser.add_argument('-H', '--hood',
                    action='store_true',
                    help='Neighbourhood')

args = parser.parse_args()

dbc = dbutil.DatabaseConnection(args.dbfile)
sqlcon = dbc.get_connection()
cursor = None

print(f'Adding helper tables to {args.dbfile}')
if args.forms or args.all:
    print('Adding forms.sql...')
    with open('sql/forms.sql', 'r', encoding='utf8') as schemafile:
        cursor = sqlcon.cursor()
        sqldata = schemafile.read()
        cursor.executescript(sqldata)

if args.lemmas or args.all:
    print('Adding lemmas.sql...')
    with open('sql/lemmas.sql', 'r', encoding='utf8') as schemafile:
        cursor = sqlcon.cursor()
        sqldata = schemafile.read()
        cursor.executescript(sqldata)

if args.features or args.all:
    print('Adding features.sql...')
    with open('sql/features.sql', 'r', encoding='utf8') as schemafile:
        cursor = sqlcon.cursor()
        sqldata = schemafile.read()
        cursor.executescript(sqldata)

cursor = sqlcon.cursor()

# FIXME: if table already has data..
#  - empty?

# if args.posx or args.all:
#    # FIXME: check if column already exists (use database connection class)
#    # FIXME: drop this option
#    prepstatements = [
#        "alter table wordfreqs drop column posx",
#        "alter table wordfreqs add column posx VARCHAR(16) NOT NULL DEFAULT ''"
#        ]
#    statements = [
#        "update wordfreqs set posx = pos",
#        "update wordfreqs set posx = 'VERB' where posx = 'AUX'"
#    ]
#
#    for statement in statements:
#        dbutil.adhoc_query(sqlcon, statement, verbose=True)

# if args.reverse or args.all:
#    # FIXME: check if column already exists (use database connection class)
#    # FIXME: combine with forms table creation
#    statements = [
#        "alter table wordfreqs add column revform VARCHAR(256) NOT NULL DEFAULT ''"
#        ]
#
#    for statement in statements:
#        dbutil.adhoc_query(sqlcon, statement, verbose=True)
#
#    formdf = dbutil.adhoc_query(sqlcon, "select form from forms", todf=True, verbose=True)
#    formrev = [form[::-1] for form in formdf.form]
#    updatestatement = "update wordfreqs set revform = ? where form = ?"
#    insvalues = []
#    for form, rev in zip(formdf.form, formrev):
#        insvalues.append([rev, form])
#    for i in tqdm(range(0, len(insvalues), 1000)):
#        slc = insvalues[i:i+1000]
#        try:
#            cursor.executemany(updatestatement, slc)
#            sqlcon.commit()
#        except IntegrityError as e:
#            logging.exception(e)
#            sqlcon.rollback()

# if args.compound or args.all:
#    print('Adding compounds...')
#    # FIXME: check if column already exists (use database connection class)
#    # FIXME: combine with lemmas table creation
#    statements = [
#        "alter table wordfreqs add column compounds INT NOT NULL DEFAULT 0"
#        ]
#
#    for statement in statements:
#        dbutil.adhoc_query(sqlcon, statement, verbose=True)
#
#    lemmadf = dbutil.adhoc_query(sqlcon, "select lemma from lemmas where instr(lemma, '#') > 0", todf=True, verbose=True)
#    print(f'Fetched {len(lemmadf)} compound lemmas')
#    updatestatement = "update wordfreqs set compounds = ? where lemma = ?"
#    insvalues = []
#    for lemma in lemmadf.lemma:
#        compval = lemma.count('#')
#        insvalues.append([compval, lemma])
#    for i in tqdm(range(0, len(insvalues), 10000)):
#        slc = insvalues[i:i+10000]
#        try:
#            cursor.executemany(updatestatement, slc)
#            sqlcon.commit()
#        except IntegrityError as e:
#            logging.exception(e)
#            sqlcon.rollback()
#        # break

if args.forms or args.all:
    print('Checking table lemmaforms...')
    have = dbutil.adhoc_query(sqlcon, 'select * from lemmaforms limit 1')
    if len(have) > 0:
        print('Table forms already has content, not inserting')
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
        formsql = "insert into forms select form, sum(frequency) as frequency, length(form) as len, count(*) as numforms, 0 as hood, '' as revform from lemmaforms group by form order by frequency desc"
        dbutil.adhoc_query(sqlcon, formsql)

    print('Adding reverse forms...')
    formdf = dbutil.adhoc_query(sqlcon, "select form from forms where revform = ''", todf=True, verbose=True)
    formrev = [form[::-1] for form in formdf.form]
    updatestatement = "update forms set revform = ? where form = ?"
    insvalues = []
    for form, rev in zip(formdf.form, formrev):
        insvalues.append([rev, form])

    chunklen = 1000
    total = math.ceil(len(insvalues)/chunklen)
    for chunk in tqdm(dbutil.chunks(insvalues, chunklen=chunklen), total=total):
        try:
            cursor.executemany(updatestatement, chunk)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            logging.exception(e)
            sqlcon.rollback()

if args.hood or args.all:
    print('Loading form information')
    sdf = dbutil.adhoc_query(sqlcon, "select * from forms limit 10000", todf=True)
    sym_spell = SymSpell(max_dictionary_edit_distance=1)

    for idx, row in tqdm(sdf.iterrows(), total=len(sdf)):
        word = row.form
        freq = row.frequency
        sym_spell.create_dictionary_entry(word, freq)

    autofreq = 10000
    minfreq = 100
    finals = {}  # type: ignore

    for idx, row in tqdm(sdf.iterrows(), total=len(sdf)):
        form = row.form
        freq = row.frequency
        suggestions = sym_spell.lookup(form, Verbosity.ALL)
        formfinals = []

        # Drop suggestion when 1) low frequency and 2) no morph analysis
        for suggestion in suggestions:
            ok = False
            res = uralicApi.analyze(suggestion.term, "fin")
            if suggestion.distance == 0:
                ...
            elif suggestion.count >= autofreq:
                ...
                ok = True
            elif suggestion.count < minfreq:
                ...
            else:
                if len(res) > 0:
                    ok = True
            if ok:
                formfinals.append((suggestion.term, suggestion.count, len(res)))
        finals[form] = formfinals
        break

    levdict = Counter()  # type: ignore
    hamdict = Counter()  # type: ignore

    for key, analysis in finals.items():
        levs = [w for w, _, _ in analysis]
        hams = [w for w, _, _ in analysis if len(w) == len(key)]
        levdict[key] = len(levs)
        hamdict[key] = len(hams)

    print(levdict)
    print(hamdict)

if args.lemmas or args.all:
    print('Checking table lemmas...')
    have = dbutil.adhoc_query(sqlcon, 'select * from lemmas limit 1')
    if len(have) > 0:
        print('Table lemmas already has content, not inserting')
    else:
        print('Inserting aggregates into lemmas table...')
        # lemmasql = "insert into lemmas select lemma, posx as pos, sum(frequency) as lemmafreq, length(lemma) as lemmalen, 0 as amblemma from wordfreqs where lemma like 's%' group by lemma, pos order by frequency desc"
        lemmasql = "insert into lemmas select lemma, posx as pos, sum(frequency) as lemmafreq, length(lemma) as lemmalen, 0 as amblemma, 0 and comparts from wordfreqs group by lemma, posx order by frequency desc"
        dbutil.adhoc_query(sqlcon, lemmasql)

    lemmadf = dbutil.adhoc_query(sqlcon, "select lemma from lemmas where instr(lemma, '#') > 0", todf=True, verbose=True)
    print(f'Fetched {len(lemmadf)} compound lemmas')
    updatestatement = "update lemmas set comparts = ? where lemma = ?"
    insvalues = []
    for lemma in lemmadf.lemma:
        compval = lemma.count('#')
        insvalues.append([compval, lemma])
    for i in tqdm(range(0, len(insvalues), 10000)):
        slc = insvalues[i:i+10000]
        try:
            cursor.executemany(updatestatement, slc)
            sqlcon.commit()
        except IntegrityError as e:
            logging.exception(e)
            sqlcon.rollback()
        # break

if args.features or args.all:
    print('Adding feature index...')
    featuresql = "select featid, feats, pos from features"
    features = dbutil.adhoc_query(sqlcon, featuresql, todf=True, verbose=True)
    have = dbutil.adhoc_query(sqlcon, 'select count(*) from wordfreqs where featid = 0')
    if have[0][0] == 0:
        print('No feature ids to update')
    else:
        sys.exit()
        updatestatement = "update wordfreqs set featid = ? where feats = ? and pos = ?"
        insvalues = []
        for featid, feats, pos in zip(features.featid, features.feats, features.pos):
            insvalues.append([featid, feats, pos])

            chunklen = 100
            total = math.ceil(len(insvalues)/chunklen)
            for chunk in tqdm(dbutil.chunks(insvalues, chunklen=chunklen), total=total):
                try:
                    cursor.executemany(updatestatement, chunk)
                    sqlcon.commit()
                except IntegrityError as e:
                    # this is not ok
                    logging.exception(e)
                    sqlcon.rollback()


def create_feature_table(connection: sqlite3.Connection, table: str, feat: str):
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

        ccursor = connection.cursor()
        print(f'Inserting content for {table} table...')
        for row in tqdm(res):
            gotfeatid, gotfeat = row
            for choice in gotfeat.split(','):
                values.append([gotfeatid, choice])
        try:
            insertsql = inserttpl % (table, feat)
            ccursor.executemany(insertsql, values)
            sqlcon.commit()
        except IntegrityError as ex:
            logging.exception(ex)
            sqlcon.rollback()


if args.features or args.all:
    create_feature_table(sqlcon, 'derivations', 'derivation')
    create_feature_table(sqlcon, 'clitics', 'clitic')
    create_feature_table(sqlcon, 'nouncases', 'nouncase')
