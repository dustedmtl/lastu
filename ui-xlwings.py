"""UI for exporting dataframe to Excel."""

# pylint: disable=invalid-name

import xlwings as xw
import pandas as pd

from lib import dbutil


if __name__ == '__main__':
    sqlcon = dbutil.get_connection('data/gutenberg_c1.db')
    query = "pos = 'NOUN' and form like 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6 and bigramfreq > 6000000"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6"

    book = xw.Book()
    print(book)

    nudf = dbutil.get_frequency_dataframe(sqlcon, query=query, grams=True)
    print(nudf)

    sheet = book.sheets[0]
    # sheet['A1'].value = nudf
    # data = sheet['A1'].expand().options(pd.DataFrame).value
