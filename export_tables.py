"""Export all tables in database to CSV/TSV files."""

# pylint: disable=invalid-name, consider-using-with

from typing import Optional
import sys
from os import remove, system
from os.path import exists, isdir
import sqlite3
import csv
import argparse
import logging
import logging.config
from tqdm.autonotebook import tqdm
from lib import dbutil

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


def tqdm_generator(curs, cs: int):
    """Yield generator for cursor."""
    while True:
        rowss = curs.fetchmany(cs)
        if not rowss:
            break
        yield rowss


def export_normalized_freqs(inputf: str,
                            output: str,
                            tsv: bool = False,
                            freq: Optional[int] = None,
                            limit: Optional[int] = None):
    """Export word frequencies in a single file."""
    # Connect to the SQLite database
    dbconnection = dbutil.DatabaseConnection(inputf)
    conn = dbconnection.get_connection()
    cursor = conn.cursor()

    totlemmafreq = dbconnection.lemmafreqs[0][0]
    totfreq = dbconnection.wordfreqs[0][0]
    # totinitgramfreq = dbconnection.initfreqs[0][0]
    # totfingramfreq = dbconnection.finfreqs[0][0]
    # totbigramfreq = dbconnection.bifreqs[0][0]

    limitstr = ""
    freqstr = ""
    sqlargs = []

    if limit:
        limitstr = f"LIMIT {limit}"

    if freq:
        freqstr = "w.frequencyx > ? AND "
        sqlargs.append(freq)

    sqlquery = f"""
SELECT w.lemma, l.lemmafreq, round(l.lemmafreq * 1000000000.0 / {totlemmafreq}) / 1000.0 as rellemmafreq, l.lemmalen, round(1000*l.amblemma)/1000.0, w.form, w.posx as pos, w.len, w.hood, round(1000*w.ambform)/1000.0, w.frequencyx as frequency, round(w.frequencyx * 1000000000.0 / {totfreq}) / 1000.0 as relfrequency, w.feats, ft.nouncase, ft.nnumber, ft.mood, ft.tense, ft.person, ft.verbform, ft.clitic, ft.derivation, ft.posspers, ft.possnum, iif(length(w.form) > 3, i.frequency, 0) as initgramfreq, iif(length(w.form) > 3, e.frequency, 0) as fingramfreq, b.frequency as bigramfreq FROM wordfreqs w , features ft, lemmas l    LEFT JOIN initgramfreqs i ON i.form = substr(w.form, 1, 3) LEFT JOIN fingramfreqs e ON e.form = substr(w.form, -3, 3) LEFT JOIN wordbigramfreqs b ON b.form = w.form WHERE {freqstr} w.featid = ft.featid AND w.lemma = l.lemma AND w.posx = l.pos ORDER BY w.frequencyx DESC {limitstr};
"""

    # FIXME: add relative frequencies for all freqs

    # FIXME: features are language-specific; these are only for Finnish
    column_names = ['lemma',
                    'lemmafreq',
                    'rellemmafreq',
                    'lemmalen', 'amblemma',
                    'form',
                    'pos', 'len', 'hood', 'ambform',
                    'frequency',
                    'relfrequency',
                    'feats',
                    'case', 'number', 'mood', 'tense', 'person', 'verbform',
                    'clitic', 'derivation',
                    'posspers', 'possnum',
                    'initgramfreq',
                    # 'relinitgramfreq',
                    'fingramfreq',
                    # 'relfingramfreq',
                    'bigramfreq',
                    # 'relbigramfreq'
                    ]

    # Export wordfreqs as a single table
    csv_file = f"{output}/wordfreqs_input.csv"

    # Chunk size for fetching and writing data
    chunk_size = 100000

    logger.info('Exporting wordfreqs table')
    logger.debug(sqlquery)
    logger.debug(sqlargs)
    cursor.execute(sqlquery, sqlargs)

    with open(csv_file, 'w', newline='', encoding='utf8') as f:
        if tsv:
            writer = csv.writer(f, delimiter='\t')
        else:
            writer = csv.writer(f)

        # Write column headers
        writer.writerow(column_names)

        # Fetch and write data in chunks
        for rows in tqdm(tqdm_generator(cursor, chunk_size)):
            if not rows:
                break
            writer.writerows(rows)

    # Close the database connection
    conn.close()

    # De-duplicate word
    system(f"uniq {output}/wordfreqs_input.csv > {output}/wordfreqs_combined.csv")
    remove(f"{output}/wordfreqs_input.csv")


def export_tables(inputf: str,
                  output: str,
                  tsv: bool = False):
    """Export database to tables."""
    # Connect to the SQLite database
    conn = sqlite3.connect(inputf)
    cursor = conn.cursor()

    # Get a list of all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    # Chunk size for fetching and writing data
    chunk_size = 100000

    # Export each table as a separate CSV file
    for table in tables:
        table_name = table[0]
        csv_file = f"{output}/{table_name}.csv"
        cursor.execute(f"SELECT * FROM {table_name};")

        column_names = [description[0] for description in cursor.description]

        with open(csv_file, 'w', newline='', encoding='utf8') as f:
            logger.info('Exporting table %s', table_name)
            if tsv:
                writer = csv.writer(f, delimiter='\t')
            else:
                writer = csv.writer(f)

            # Write column headers
            writer.writerow(column_names)

            # Fetch and write data in chunks
            for rows in tqdm(tqdm_generator(cursor, chunk_size)):
                if not rows:
                    break
                writer.writerows(rows)

    # Close the database connection
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='export-tables',
                                     description='Export tables')

    parser.add_argument('-i', '--input',
                        type=str,
                        required=True,
                        help='input database(s)')

    parser.add_argument('-o', '--output',
                        type=str,
                        # required=True,
                        help='output directory')

    parser.add_argument('-n', '--normalized',
                        action='store_true',
                        help='normalized export')

    parser.add_argument('-t', '--tsv',
                        action='store_true',
                        help='Verbose')

    parser.add_argument('-l', '--limit',
                        type=int,
                        help='limit rows')

    parser.add_argument('-f', '--frequency',
                        type=int,
                        help='minimum frequency')

    args = parser.parse_args()
    inputfile = args.input
    outdir = args.output

    if not exists(inputfile):
        logger.warning('No such file: %s', inputfile)
        sys.exit()

    if not isdir(outdir):
        logger.warning('No such directory: %s', outdir)
        sys.exit()

    if args.normalized:
        export_normalized_freqs(inputfile, outdir, tsv=args.tsv, limit=args.limit, freq=args.frequency)
    else:
        export_tables(inputfile, outdir, tsv=args.tsv)
