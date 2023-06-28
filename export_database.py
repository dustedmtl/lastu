"""Export all tables in database to CSV/TSV files."""

# pylint: disable=invalid-name, consider-using-with

from typing import Dict
import sys
from os import mkdir, walk
from os.path import exists, join, relpath
import argparse
import logging
import logging.config
from shutil import copy, rmtree
import tempfile
import zipfile
# from tqdm.autonotebook import tqdm
from db_stats import get_db_stats
from export_tables import export_tables

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


def print_readme(readmeout: str,
                 source: str,
                 metadata: Dict[str, str],
                 rows: int,
                 freqs: int):
    """Print readme."""
    language = metadata['language']
    langcode = metadata['langcode']
    dbtext = f"""
This archive contains a database for the LASTU program.

LASTU (Lexical Application for STimulus Unearthing) is a program for generating stimulus words for psycholinguistic research.
It has been primarily developed for Finnish.

Executable applications, documentation and databases can be found from OSF: https://osf.io/j8v6b/.
The source code for application is available at GitHub: https://github.com/dustedmtl/lastu.

# Database metadata
Source: {source}
Language: {language}
Language code: {langcode}
Rows: {rows}
Cumulative frequency: {freqs}

# Licenses
This database is licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

https://creativecommons.org/licenses/by-sa/4.0/
"""
    with open(readmeout, 'w', encoding='utf8') as of:
        print(dbtext, file=of)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='export-database',
                                     description='Export database')

    parser.add_argument('-i', '--input',
                        type=str,
                        required=True,
                        help='input database(s)')

    parser.add_argument('-s', '--source',
                        type=str,
                        required=True,
                        help='database source')

    parser.add_argument('-o', '--outfile',
                        type=str,
                        required=True,
                        help='output file')

    args = parser.parse_args()
    inputfile = args.input
    outfile = args.outfile

    if not exists(inputfile):
        logger.warning('No such file: %s', inputfile)
        sys.exit()

    if exists(outfile):
        logger.warning('File already exists: %s', outfile)
        sys.exit()

    tempdir = tempfile.mkdtemp()
    logger.debug("Temporary directory: %s", tempdir)
    try:
        tablesdir = join(tempdir, 'tables')
        mkdir(tablesdir)
        # Database statistics
        metadata, rows, freqs = get_db_stats(inputfile, verbose=True)
        # Insert readme file
        readmefile = join(tempdir, 'README.txt')
        print_readme(readmefile, args.source, metadata, rows, freqs)
        logger.info("Exporting tables to: %s", tablesdir)
        export_tables(inputfile, tablesdir)
        # Copy database file
        logger.info("Copying database file")
        copy(inputfile, tempdir)
        # Making final zip file
        logger.info("Zipping to: %s", outfile)
        with zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in walk(tempdir):
                for file in files:
                    file_path = join(root, file)
                    zip_file.write(file_path, relpath(file_path, tempdir))

    finally:
        # Clean up the temporary directory
        # pass
        rmtree(tempdir)
