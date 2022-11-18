#!/usr/bin/env python3
"""Convert text data to conllu format."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import argparse
import logging
from lib import corpus, dbutil


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('build-database')

parser = argparse.ArgumentParser(prog='build-database',
                                 description='Generate SQL database from CoNLL file')

parser.add_argument('-i', '--input',
                    type=str,
                    required=True,
                    help='Input directory/file')

parser.add_argument('-d', '--dbfile',
                    type=str,
                    required=True,
                    help='DBfile')

parser.add_argument('-n', '--newfile',
                    action='store_true',
                    help='New db file')

parser.add_argument('-N', '--noindex',
                    action='store_true',
                    help='Do not add wordfreqs indexes to the database')

parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Verbose')

parser.add_argument('-c', '--count',
                    type=int,
                    help='File count')

parser.add_argument('-s', '--sentencecount',
                    type=int,
                    help='Sentence count')

parser.add_argument('-t', '--trashfile',
                    type=str,
                    help='Trash file')

parser.add_argument('-o', '--origcase',
                    action='store_true',
                    help='Original case')

args = parser.parse_args()


if not exists(args.input):
    logger.warning('No such file: %s', args.input)
    sys.exit()

dbc = None

if not exists(args.dbfile):
    if args.newfile:
        creationscripts = ['wordfreqs2.sql', 'features.sql']
        print(f'Creating database at {args.dbfile}')
        dbc = dbutil.DatabaseConnection(args.dbfile)
        sqlcon = dbc.get_connection()
        cursor = sqlcon.cursor()
        for sqlfile in creationscripts:
            with open(f'sql/{sqlfile}', 'r', encoding='utf8') as schemafile:
                sqldata = schemafile.read()
                cursor.executescript(sqldata)
                sqlcon.commit()
    else:
        logger.warning('No such file: %s', args.dbfile)
        sys.exit()

# FIXME: check that dbfile is a SQLite database?

if not dbc:
    dbc = dbutil.DatabaseConnection(args.dbfile)

trashfh = None

if args.trashfile:
    print(f'Storing discarded strings to file {args.trashfile}')
    trashfh = open(args.trashfile, 'w', encoding='utf-8')

data = corpus.conllu_reader(args.input,
                            verbose=args.verbose,
                            origcase=args.origcase,
                            sentencecount=args.sentencecount,
                            trashfile=trashfh,
                            filecount=args.count)
if trashfh:
    trashfh.close()

print(f'Storing {len(data[0])} unigram frequencies to database {args.dbfile}')
dbutil.write_freqs_to_db(dbc.get_connection(), data)

if not args.noindex:
    print('Adding indexes..')
    indexscripts = ['wordfreqs_indexes.sql']

    sqlcon = dbc.get_connection()
    cursor = sqlcon.cursor()
    for sqlfile in indexscripts:
        with open(f'sql/{sqlfile}', 'r', encoding='utf8') as schemafile:
            sqldata = schemafile.read()
            cursor.executescript(sqldata)
            sqlcon.commit()
