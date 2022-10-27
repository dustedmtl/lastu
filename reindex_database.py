#!/usr/bin/env python3
"""Convert text data to conllu format."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import argparse
from tqdm import tqdm
from lib import dbutil

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('reindex-database')

parser = argparse.ArgumentParser(prog='reindex-database',
                                 description='Reindex database')

parser.add_argument('-d', '--dbfile',
                    type=str,
                    required=True,
                    help='DBfile')

parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Verbose')

args = parser.parse_args()

sqlcon = dbutil.get_connection(args.dbfile)
if not exists(args.dbfile):
    logger.warning('No such file: %s', args.dbfile)
    sys.exit()

selectsql = "select name, tbl_name from sqlite_master where tbl_name = ?"
cursor = sqlcon.cursor()
dest = sqlcon.cursor()

rows = cursor.execute(selectsql, ['wordfreqs'])
indexes = []
for row in tqdm(rows.fetchall()):
    index_name = row[0]
    if index_name == 'wordfreqs' or index_name.startswith('sqlite'):
        continue
    indexes.append(row[0])

print('Dropping indexes..')
for index in (pbar := tqdm(indexes)):
    pbar.set_description(f'{index}')
    sql = "DROP INDEX " + index
    cursor.execute(sql)
print('Reindexing..')
with open('sql/wordfreqs.sql', 'r', encoding='utf8') as schemafile:
    sqldata = schemafile.read()
    cursor.executescript(sqldata)
