#!/usr/bin/env python3
"""Manage database."""

# pylint: disable=invalid-name, consider-using-with

# import os
# from os.path import isdir, isfile, exists
from os.path import exists
import sys
import argparse
from sqlite3 import IntegrityError
from shutil import copy
import math
from tqdm.autonotebook import tqdm
import logging

from lib import dbutil, buildutil


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('manage-database')

parser = argparse.ArgumentParser(prog='manage-database',
                                 description='Prune database')

parser.add_argument('-i', '--input',
                    type=str,
                    nargs='+',
                    required=True,
                    help='input database(s)')

parser.add_argument('-o', '--output',
                    type=str,
                    # required=True,
                    help='output database(s)')

parser.add_argument('-c', '--cmd',
                    type=str,
                    required=True,
                    help='Command to execute')

parser.add_argument('-f', '--frequency',
                    type=int,
                    default=1,
                    help='Frequency filter for pruning')

parser.add_argument('-v', '--verbose',
                    action='store_true',
                    help='Verbose')

parser.add_argument('-e', '--allowempty',
                    action='store_true',
                    help='Allow empty target file')

parser.add_argument('-y', '--yes',
                    action='store_true',
                    help='Do not ask for confirmation')

args = parser.parse_args()
cmd = args.cmd

if cmd == 'prune':
    # only take the first input into account
    inputfile = args.input[0]
    if not exists(inputfile):
        logger.warning('No such file: %s', inputfile)
        sys.exit()

    print(f'Using {inputfile} as source database')
    sqlcon = dbutil.get_connection(inputfile)
    # Determine how much stuff will be deleted
    total = dbutil.adhoc_query(sqlcon, "select count(*) from wordfreqs")
    topurge = dbutil.adhoc_query(sqlcon, f"select count(*) from wordfreqs where frequency <= {args.frequency}")
    print(f'About to delete {topurge[0][0]} rows of {total[0][0]}')
    if not args.yes:
        ok = input('Ok? y/N: ')
        if not ok.lower().startswith('y'):
            print('Not doing anything')
            sys.exit()

    # Copy database if so desired
    if args.output:
        if exists(args.output):
            raise FileExistsError(args.output)
        print(f'Copying {inputfile} to {args.output}')
        copy(inputfile, args.output)
        sqlcon = dbutil.get_connection(args.output)

    # Drop extraneous information:
    #  - helper tables
    #  - wordfreqs indexes, except unique
    #  - nullify computed wordfreqs info: hood, ambform

    print('Dropping helper tables...')
    buildutil.drop_helper_tables(sqlcon)
    print('Dropping wordfreqs indexes...')
    buildutil.drop_indexes(sqlcon, 'wordfreqs')
    print('Nullifying computed information...')
    buildutil.nullify_wordfreqs(sqlcon)

    # Deletion
    print('Dropping matching rows...')
    buildutil.delete_rows(sqlcon, args.frequency)

    # Rebuild
    print('Re-adding indexes and tables...')
    buildutil.add_schema(sqlcon, 'wordfreqs_indexes.sql')
    buildutil.add_schema(sqlcon, 'features.sql')
    print('Re-linking features information...')
    buildutil.add_features(sqlcon)

    print('Remember to add grams and helper tables!')

if cmd == 'concat':
    if not args.output:
        print('Need to provide output file')
        sys.exit()

    notfound = []
    for fn in args.input:
        if not exists(fn):
            notfound.append(fn)

    if notfound:
        logger.warning('Missing input files: %s', notfound)
        sys.exit()

    # New database
    if args.output:
        if exists(args.output):
            if args.allowempty:
                print(f'Target file {args.output} already exists, allowing')
            else:
                raise FileExistsError(args.output)
        else:
            print(f'Creating new database at {args.output}')
            buildutil.create_database(args.output)

    targetcon = dbutil.get_connection(args.output)
    cursor = targetcon.cursor()

    print(f'Inserting data from {len(args.input)} files')
    insertpat = "insert into wordfreqs (%s) values (%s) on conflict(lemma, form, pos, feats) do update set frequency = frequency + excluded.frequency"
    insertsql = ""
    columns = None
    chunklen = 100000
    # chunklen = 1

    for fn in args.input:
        print(f'Inserting data from {fn}...')
        sqlcon = dbutil.get_connection(fn)
        dbdata = dbutil.adhoc_query(sqlcon, "SELECT * FROM wordfreqs", todf=True).drop('id', axis=1)
        if columns is None:
            columns = dbdata.columns
            print(columns)
            qs = ['?'] * len(columns)
            # print(qs)
            insertsql = insertpat % (', '.join(columns), ','.join(qs))
            print(insertsql)

        totwordchunks = math.ceil(len(dbdata)/chunklen)

        print(f'Inserting {len(dbdata)} rows in {totwordchunks} chunks...')

        for chunk in tqdm(dbutil.chunks(dbdata, chunklen=chunklen),
                          total=totwordchunks):
            try:
                cursor.executemany(insertsql, chunk)
                targetcon.commit()
            except IntegrityError as e:
                # this is not ok
                logging.exception(e)
                targetcon.rollback()
            # break
        # break


# selectsql = "select * from wordfreqs where frequency >= ?"

# src = origcon.cursor()
# dest = sqlcon.cursor()

# rows = src.execute(selectsql, [args.frequency])
# for row in tqdm(rows.fetchall()):
#    num = len(row)
#    ins = insertpat % ','.join(['?'] * num)
#    dest.execute(ins, row)
#    sqlcon.commit()
#    # break
