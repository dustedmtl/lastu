"""UI for wordmill application."""

# Copyright (C) 2022 University of Turku
# License: CC-BY-4.0
#
# Starter code based on https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/

# pylint: disable=invalid-name

import sys
from os.path import exists, getsize, dirname, realpath, join, split
from pathlib import Path
import time
import logging
import pandas as pd

from PyQt6.QtWidgets import (
    QTableView, QApplication, QMainWindow, QWidget,
    QGridLayout,
    QAbstractScrollArea,
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

from lib import dbutil

homedir = Path.home()
logger = logging.getLogger('ui-qt6')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(join(homedir, 'ui-qt6.txt'))
logger.addHandler(handler)


class TableModel(QAbstractTableModel):
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        # super(TableModel, self).__init__()
        self._data = data

    def data(self, index: QModelIndex, role: int = None):
        if role == Qt.ItemDataRole.DisplayRole:
            # print(index.row(), index.column(), self._data.iloc[index.row()][index.column()])
            return str(self._data.iloc[index.row()][index.column()])
        return None

    def rowCount(self, _parent: QModelIndex = None):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, _parent: QModelIndex = None):
        # Return number of columns
        return len(self._data.columns)

    def headerData(self, section: int,
                   orientation: Qt.Orientation, role: int = None):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section]+1)
        return None


def get_macos_path(currentdir: str):
    """Get correct working directory for MacOS."""
    while True:
        parent, lastdir = split(currentdir)
        print(parent, lastdir)
        if lastdir in ['Contents', 'MacOS'] or lastdir.endswith('.app'):
            currentdir = parent
        else:
            break
    return currentdir


class MainWindow(QMainWindow):

    def __init__(self, dbconnection, df=None):
        super().__init__()
        # super(MainWindow, self).__init__()
        self.setWindowTitle("WM2")

        self.connection = dbconnection

        self.layout = QGridLayout()

        self.querybox = QLineEdit()
        self.querybox.returnPressed.connect(self.enter)
        self.layout.addWidget(self.querybox, 0, 0)

        button = QPushButton("Query")
        button.clicked.connect(self.setQueryData)
        self.layout.addWidget(button, 0, 1)

        self.statusfield = QLabel()
        self.layout.addWidget(self.statusfield, 1, 0, 1, 2)

        self.table = QTableView()
        # self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)

        # cell width is based on their contents
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        # view.setSelectionBehavior(QTableView.SelectRows)

        # FIXME: font

        self.setData(df)

        self.layout.addWidget(self.table, 2, 0, 2, 2)

        self.copyleft = QLabel('Copyright (c) 2022 University of Turku')
        self.layout.addWidget(self.copyleft)
        self.copyleft.setAlignment(Qt.AlignmentFlag.AlignRight)
        # FIXME: smaller font

        widget = QWidget()
        widget.setLayout(self.layout)

        self.setCentralWidget(widget)

    def enter(self):
        # print('enter pressed')
        self.setQueryData()

    def setQueryData(self):
        querytext = self.getQuery()
        # FIXME: ensure that the below text shows
        self.statusfield.setText(f'Executing query {querytext}')

        start = time.perf_counter()
        querydf = self.dbquery(querytext)

        if querydf is not None:
            self.setData(querydf)
            end = time.perf_counter()

            self.statusfield.setText(f'Executing query.. done: {len(querydf)} rows returned in {end - start:.1f} seconds')

            sizehint = self.layout.sizeHint()
            width = sizehint.width()
            print(f'Setting window width to {width}')
            # self.setFixedSize(self.layout.sizeHint())
            self.setFixedWidth(width+10)
            # self.setMinimumSize(width, 0)

    def getQuery(self):
        text = self.querybox.text()
        return text

    def dbquery(self, text: str):
        try:
            newdf, querystatus, querymessage = dbutil.get_frequency_dataframe(self.connection, query=text, grams=True)
            print(querystatus, querymessage)
            if querystatus < 0:
                raise Exception(querymessage)
            return newdf
        except Exception as e:
            logger.error("Issue with query %s: %s", query, e)
            self.statusfield.setText(f'Issue with query {text}: {e}')
            return None

#    def setData(self, df: Optional[pd.DataFrame]):
    def setData(self, df: pd.DataFrame = None):
        if df is None:
            df = pd.DataFrame()
        self.model = TableModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()


if __name__ == "__main__":

    basedir1 = dirname(__file__)
    basedir2 = dirname(realpath(__file__))
    basedir3 = dirname(sys.argv[0])
    basedir4 = dirname(sys.executable)

    logger.debug('basedir1: %s', basedir1)
    logger.debug('basedir2: %s', basedir2)
    logger.debug('basedir3: %s', basedir3)
    logger.debug('basedir4: %s', basedir4)

    # FIXME: detect whether app is frozen or not
    # FIXME: detect OS -> proper path
    # FIXME: read database info from ini file

    if len(basedir3) > 0:
        basedir = get_macos_path(basedir3)
    else:
        basedir = '.'

    logger.info("basedir: %s", basedir)

    # dbfile = f'{basedir}/data/gutenberg_c1.db'
    dbfile = f'{basedir}/data/s24_c1.db'

    if not exists(dbfile) or getsize(dbfile) == 0:
        logger.error("No such file: %s", dbfile)
        raise FileNotFoundError(dbfile)

    try:
        logger.info("Connecting to %s...", dbfile)
        sqlcon = dbutil.get_connection(dbfile)
    except Exception as e:
        logger.error("Couldn't connect to %s: %s", dbfile, e)

    app = QApplication(sys.argv)

    w = MainWindow(sqlcon)
    query = "form = 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and form = 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6 and bigramfreq > 6000000"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6"

    # initial query
    w.querybox.setText(query)
    w.setQueryData()
    w.show()
    app.exec()
