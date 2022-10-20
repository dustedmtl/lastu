#!/usr/bin/env python3
"""Generate init/fin/bigram frequencies to database."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import argparse
from lib import dbutil

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('generate-freqs')

parser = argparse.ArgumentParser(prog='generate-freqs',
                                 description='Generate frequencies')

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

args = parser.parse_args()

if not exists(args.dbfile):
    logger.warning('No such file: %s', args.dbfile)
    sys.exit()

sqlcon = dbutil.get_connection(args.dbfile)

# FIXME: drop existing tables feature
if args.newfile:
    print(f'Add frequency tables to {args.dbfile}')
    with open('sql/gramfreqs.sql', 'r', encoding='utf8') as schemafile:
        cursor = sqlcon.cursor()
        sqldata = schemafile.read()
        cursor.executescript(sqldata)

print('Generating gram frequencies..')
gramfreqs = dbutil.get_trigram_freqs(sqlcon)

init, fin, bi = gramfreqs
print(f'Got {len(init)} {len(fin)} {len(bi)} init/fin/bigram frequencies')

print('Inserting trigram frequencies..')
dbutil.insert_trigram_freqs(sqlcon, init, fin, bi)

print('Inserting bigram frequencies..')
dbutil.insert_bigram_freqs(sqlcon, bi)
