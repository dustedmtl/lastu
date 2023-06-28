"""Get database statistics."""

# pylint: disable=invalid-name, consider-using-with

from typing import Tuple, Dict
from os.path import exists
import sys
import argparse
import logging
import logging.config

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


def get_db_stats(dbfile: str,
                 verbose: bool = False,
                 index: bool = False) -> Tuple[Dict, int, int]:
    """Get database statistic."""
    sqlcon = dbutil.get_connection(dbfile)

    if index:
        freqindex_str = "CREATE INDEX IF NOT EXISTS idx_wordfreqs_freq_len ON wordfreqs(frequency DESC, len DESC)"

        print('Adding index if missing..')
        dbutil.adhoc_query(sqlcon, freqindex_str)

    print('Determining row word count..')
    rows = dbutil.adhoc_query(sqlcon, "select count(*) from wordfreqs")
    freqs = dbutil.adhoc_query(sqlcon, "select sum(frequency) from wordfreqs")

    _metadata = dbutil.adhoc_query(sqlcon, "select * from metadata")
    metadata = {}
    for t in _metadata:
        k, v = t
        metadata[k] = v

    if verbose:
        print()
        print(f'Stats for database file {dbfile}')
        print()
        print(f'Rows: {rows[0][0]}')
        print(f'Cumulative frequency: {freqs[0][0]}')
        print(metadata)

    return metadata, rows[0][0], freqs[0][0]


if __name__ == '__main__':

    parser = argparse.ArgumentParser(prog='database stats',
                                     description='Database statistics')

    parser.add_argument('dbfile',
                        type=str,
                        # required=True,
                        help='input database')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Verbose')

    args = parser.parse_args()

    inputfile = args.dbfile
    if not exists(inputfile):
        logger.warning('No such file: %s', inputfile)
        sys.exit()

    print(f'Using {inputfile} as database')
    meta, _rows, _tokens = get_db_stats(inputfile, verbose=True, index=True)
