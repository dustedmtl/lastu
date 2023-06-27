"""Export all tables in database to CSV/TSV files."""

# pylint: disable=invalid-name, consider-using-with

import sys
from os.path import exists, isdir
import sqlite3
import csv
import argparse
import logging
import logging.config
from tqdm.autonotebook import tqdm

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

    parser.add_argument('-t', '--tsv',
                        action='store_true',
                        help='Verbose')

    args = parser.parse_args()
    inputfile = args.input
    outdir = args.output

    if not exists(inputfile):
        logger.warning('No such file: %s', inputfile)
        sys.exit()

    if not isdir(outdir):
        logger.warning('No such directory: %s', outdir)
        sys.exit()

    export_tables(inputfile, outdir, tsv=args.tsv)
