#!/usr/bin/env python3
"""Convert text data to conllu format."""

# pylint: disable=invalid-name

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import argparse
from lib import corpus, dbutil

import logging

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

parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Verbose')

parser.add_argument('-o', '--origcase',
                    action='store_true',
                    help='Original case')

parser.add_argument('-c', '--count',
                    type=int,
                    help='File count')

args = parser.parse_args()


if not exists(args.input):
    logger.warning('No such file: %s', args.input)
    sys.exit()

sqlcon = None

if not exists(args.dbfile):
    if args.newfile:
        print(f'Creating database at {args.dbfile}')
        sqlcon = dbutil.get_connection(args.dbfile)
        cursor = sqlcon.cursor()
        with open('sql/wordfreqs.sql', 'r', encoding='utf8') as schemafile:
            sqldata = schemafile.read()
            cursor.executescript(sqldata)
    else:
        logger.warning('No such file: %s', args.dbfile)
        sys.exit()

# FIXME: check that dbfile is a SQLite database?

data = corpus.conllu_reader(args.input,
                            verbose=args.verbose,
                            origcase=args.origcase,
                            count=args.count)
# print(len(data))

# FIXME: empty SQLite databse file?

print(f'Storing {len(data[0])} unigram frequencies to database {args.dbfile}')
if not sqlcon:
    sqlcon = dbutil.get_connection(args.dbfile)
dbutil.write_freqs_to_db(sqlcon, data)
