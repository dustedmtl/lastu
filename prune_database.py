#!/usr/bin/env python3
"""Generate init/fin/bigram frequencies to database."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import shutil
import argparse
from sqlite3 import IntegrityError
from tqdm import tqdm

from lib import dbutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('prune-database')

parser = argparse.ArgumentParser(prog='prune-database',
                                 description='Prune database')

parser.add_argument('-i', '--input',
                    type=str,
                    required=True,
                    help='input DB')

parser.add_argument('-o', '--output',
                    type=str,
                    required=True,
                    help='input DB')

parser.add_argument('-n', '--newfile',
                    action='store_true',
                    help='New db file')

parser.add_argument('-f', '--frequency',
                    type=int,
                    default=10,
                    help='Frequency filter')

parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Verbose')

args = parser.parse_args()

if not exists(args.input):
    logger.warning('No such file: %s', args.input)
    sys.exit()

sqlcon = None
if not exists(args.output):
    if args.newfile:
        print(f'Creating database at {args.output}')
        sqlcon = dbutil.get_connection(args.output)
        cursor = sqlcon.cursor()
        with open('sql/wordfreqs.sql', 'r', encoding='utf8') as schemafile:
            sqldata = schemafile.read()
            cursor.executescript(sqldata)
    else:
        logger.warning('No such file: %s', args.output)
        sys.exit()

if not sqlcon:
    sqlcon = dbutil.get_connection(args.output)
origcon = dbutil.get_connection(args.input)

selectsql = "select * from wordfreqs where frequency >= ?"
insertpat = "insert into wordfreqs values (%s)"

src = origcon.cursor()
dest = sqlcon.cursor()

rows = src.execute(selectsql, [args.frequency])
for row in tqdm(rows.fetchall()):
    num = len(row)
    ins = insertpat % ','.join(['?'] * num)
    dest.execute(ins, row)
    sqlcon.commit()
    # break
