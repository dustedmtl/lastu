#!/usr/bin/env python3
"""Convert text data to conllu format."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import argparse
import logging
import pandas as pd
from sqlite3 import IntegrityError
from tqdm.autonotebook import tqdm
from lib import dbutil

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('build-database')

parser = argparse.ArgumentParser(prog='generate-helper-tables',
                                 description='Generate helper tables')

parser.add_argument('-d', '--dbfile',
                    type=str,
                    required=True,
                    help='DBfile')

parser.add_argument('-n', '--newfile',
                    action='store_true',
                    help='Import table schema')

parser.add_argument('-a', '--all',
                    action='store_true',
                    help='All tables')

parser.add_argument('-f', '--forms',
                    action='store_true',
                    help='Forms tables')

parser.add_argument('-l', '--lemmas',
                    action='store_true',
                    help='Lemmas tables')

parser.add_argument('-F', '--features',
                    action='store_true',
                    help='Features tables')

args = parser.parse_args()

sqlcon = dbutil.get_connection(args.dbfile)
cursor = None

# FIXME: automatic schema addition?

if args.newfile:
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

if not cursor:
    cursor = sqlcon.cursor()

# FIXME: if table already has data..
#  - empty?

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
        # formsql = "insert into forms select form, sum(frequency) as frequency, count(*) as numforms, 0 as hood from lemmaforms where form like 's%' group by form order by frequency desc"
        formsql = "insert into forms select form, sum(frequency) as frequency, count(*) as numforms, 0 as hood from lemmaforms group by form order by frequency desc"
        # formsql = "insert into forms select form, sum(frequency) as frequency, count(*) as numforms, max(frequency)/cast(sum(frequency) as real) as maxpct, 0 as hood from lemmaforms group by form order by frequency desc"

        dbutil.adhoc_query(sqlcon, formsql)

if args.lemmas or args.all:
    print('Checking table lemmas...')
    have = dbutil.adhoc_query(sqlcon, 'select * from lemmas limit 1')
    if len(have) > 0:
        print('Table lemmas already has content, not inserting')
    else:
        print('Inserting aggregates into lemmas table...')
        # lemmasql = "insert into lemmas select lemma, posx as pos, sum(frequency) as lemmafreq, length(lemma) as lemmalen, 0 as amblemma from wordfreqs where lemma like 's%' group by lemma, pos order by frequency desc"
        lemmasql = "insert into lemmas select lemma, posx as pos, sum(frequency) as lemmafreq, length(lemma) as lemmalen, 0 as amblemma from wordfreqs group by lemma, posx order by frequency desc"
        dbutil.adhoc_query(sqlcon, lemmasql)

if args.features or args.all:
    inserttpl = 'INSERT INTO %s (lemma, form, pos, feats, %s) values (?, ?, ?, ?, ?)'
    print('Checking table derivations...')
    have = dbutil.adhoc_query(sqlcon, 'select * from derivations limit 1')
    if len(have) > 0:
        print('Table derivations already has content, not inserting')
    else:
        print('Fetching content for derivations table...')
        derfetchsql = "select lemma, form, pos, feats, derivation from wordfreqs where derivation != '_' group by lemma, form, posx, feats"
        res = dbutil.adhoc_query(sqlcon, derfetchsql)
        # res = cursor.execute(derfetchsql)
        values = []

        print('Inserting content for derivations table...')
        for row in tqdm(res):
            lemma, form, pos, feats, der = row
            # if ',' in der:
            #    print(row)
            for choice in der.split(','):
                values.append([lemma, form, pos, feats, choice])
        try:
            insertsql = inserttpl % ('derivations', 'derivation')
            cursor.executemany(insertsql, values)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            print('Issue', e)
            sqlcon.rollback()

    print('Checking table clitics...')
    have = dbutil.adhoc_query(sqlcon, 'select * from clitics limit 1')
    if len(have) > 0:
        print('Table clitics already has content, not inserting')
    else:
        print('Fetching content for clitics table...')
        clfetchsql = "select lemma, form, pos, feats, clitic from wordfreqs where clitic != '_' group by lemma, form, posx, feats"
        res = dbutil.adhoc_query(sqlcon, clfetchsql)
        # res = cursor.execute(derfetchsql)
        values = []

        print('Inserting content for clitics table...')
        for row in tqdm(res):
            lemma, form, pos, feats, der = row
            # if ',' in der:
            #    print(row)
            for choice in der.split(','):
                values.append([lemma, form, pos, feats, choice])
        try:
            insertsql = inserttpl % ('clitics', 'clitic')
            cursor.executemany(insertsql, values)
            sqlcon.commit()
        except IntegrityError as e:
            # this is not ok
            print('Issue', e)
            sqlcon.rollback()
            
