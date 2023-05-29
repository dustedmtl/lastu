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
import logging
import logging.config
from tqdm.autonotebook import tqdm

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
                    help='Minimum frequency for pruning')

parser.add_argument('-p', '--pos',
                    type=str,
                    help='Parts-of-speech to remove for pruning')

parser.add_argument('-l', '--maxlength',
                    type=int,
                    help='Maximum word length for pruning')

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

prunepos = []
# print(args.pos)
if args.pos is not None:
    prunepos.extend(args.pos.split(','))

if cmd == 'prune':
    # only take the first input into account
    inputfile = args.input[0]
    if not exists(inputfile):
        logger.warning('No such file: %s', inputfile)
        sys.exit()

    if not args.pos and not args.maxlength and not args.frequency:
        print('No pruning criteria provided - exiting')
        sys.exit()

    print(f'Using {inputfile} as source database')
    dbconn = dbutil.DatabaseConnection(inputfile)
    sqlcon = dbconn.get_connection()
    if args.output:
        print(f'Copy database to {args.output}')
    # Determine how much stuff will be deleted
    print('Determining total word count..')
    total = dbutil.adhoc_query(sqlcon, "select count(*) from wordfreqs")
    total = total[0][0]
    print('Determining deletion word count..')

    mods = 0
    if args.pos is not None:
        mods += 1
        pp = ["'" + p + "'" for p in prunepos]
        pp2 = ','.join(pp)
        # print(pp2)
        sqlquery = f"select count(*) from wordfreqs where pos in ({pp2})"
        # print(sqlquery)
        topurge = dbutil.adhoc_query(sqlcon, sqlquery)
        topurge_pos = topurge[0][0]
        toremain_pos = total - topurge_pos
        print(f'About to delete {topurge_pos} rows of {total}, with {toremain_pos} remaining')

    if args.frequency is not None:
        mods += 1
        topurge = dbutil.adhoc_query(sqlcon, f"select count(*) from wordfreqs where frequency < {args.frequency}")
        topurge_freq = topurge[0][0]
        toremain_freq = total - topurge_freq
        print(f'About to delete {topurge_freq} rows of {total}, with {toremain_freq} remaining')

    if args.maxlength is not None:
        mods += 1
        topurge = dbutil.adhoc_query(sqlcon, f"select count(*) from wordfreqs where len > {args.maxlength}")
        topurge_len = topurge[0][0]
        toremain_len = total - topurge_len
        print(f'About to delete {topurge_len} rows of {total}, with {toremain_len} remaining')

    if mods > 1:
        print('Multiple pruning criteria provided - the total amount of pruned rows may differ from the information provided above.')

    if args.output:
        print('The original database is not modified, the changes will be made to a copied database.')

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
    if args.pos is None:
        buildutil.drop_indexes(sqlcon, 'wordfreqs', exclude='freq_len')
    print('Nullifying computed information...')
    buildutil.nullify_wordfreqs(sqlcon)

    print('Dropping matching rows...')
    # Deletion
    if args.pos is not None:
        buildutil.delete_pos_rows(sqlcon, prunepos)

    if args.frequency is not None:
        buildutil.delete_rows(sqlcon, args.frequency)

    if args.maxlength is not None:
        buildutil.delete_len_rows(sqlcon, args.maxlength)

    # Rebuild
    print('Re-adding indexes and tables...')
    buildutil.add_schema(sqlcon, 'wordfreqs_indexes.sql')
    buildutil.add_schema(sqlcon, 'features.sql')
    print('Re-linking features information...')
    buildutil.add_features(dbconn)

    # FIXME: run vacuum
    # buildutil.vacuum(sqlcon)

    print('Remember to run the scripts for adding grams and helper tables!')

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
    # FIXME: get database metadata from first input file to determine language
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
