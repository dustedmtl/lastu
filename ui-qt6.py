"""UI for wordmill application."""

# Copyright (C) 2022 University of Turku
# License: CC-BY-4.0
#
# Starter code based on https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/

# pylint: disable=invalid-name

import sys
from os.path import exists, getsize, join, split
from collections import defaultdict
from pathlib import Path
import time
from datetime import datetime
import logging
import pandas as pd

from PyQt6.QtWidgets import (
    QTableView, QApplication, QMainWindow, QWidget,
    QGridLayout,
    QAbstractScrollArea,
    QFileDialog,
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex

from lib import dbutil, uiutil

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
        self._otherwindows = []
        self.layout = QGridLayout()

        newbutton = QPushButton("New window")
        newbutton.clicked.connect(self.newWindow)
        self.layout.addWidget(newbutton, 0, 1, 1, 1)

        self.querybox = QLineEdit()
        self.querybox.returnPressed.connect(self.enter)
        self.layout.addWidget(self.querybox, 1, 0, 1, 1)

        button = QPushButton("Query")
        button.clicked.connect(self.textQuery)
        self.layout.addWidget(button, 1, 1, 1, 1)

        self.statusfield = QLabel()
        # self.layout.addWidget(self.statusfield, 1, 0, 1, 2)
        self.layout.addWidget(self.statusfield, 2, 0, 1, 1)

        filebutton = QPushButton("Input")
        filebutton.clicked.connect(self.inputFileQuery)
        self.layout.addWidget(filebutton, 2, 1, 1, 1)

        self.table = QTableView()
        # self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)

        # cell width is based on their contents
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        # view.setSelectionBehavior(QTableView.SelectRows)

        # FIXME: font

        self.setData(df)

        self.layout.addWidget(self.table, 3, 0, 1, 2)

        self.copyleft = QLabel('Copyright (c) 2022 University of Turku')
        self.layout.addWidget(self.copyleft, 4, 0, 1, 2)
        self.copyleft.setAlignment(Qt.AlignmentFlag.AlignRight)
        # FIXME: smaller font

        widget = QWidget()
        widget.setLayout(self.layout)

        self.setCentralWidget(widget)

    def newWindow(self):
        w2 = MainWindow(self.connection)
        w2.querybox.setText(self.querybox.text())
        self._otherwindows.append(w2)
        w2.setData(self.data)
        sizehint = w2.layout.sizeHint()
        width = sizehint.width()
        w2.setFixedWidth(width+10)
        w2.show()

    def enter(self):
        # print('enter pressed')
        self.textQuery()

    def textQuery(self):
        querytext = self.querybox.text()
        # FIXME: ensure that the below text shows
        self.statusfield.setText(f'Executing query {querytext}')
        self.doQuery(querytext)

    def doQuery(self, queryinput):
        start = time.perf_counter()
        querydf = self.dbquery(queryinput)

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

    def inputFileQuery(self):
        fileinput = QFileDialog()
        fileinput.setFileMode(QFileDialog.FileMode.ExistingFile)
        fileinput.setNameFilter("Text files (*.txt)")
        fileinput.setViewMode(QFileDialog.ViewMode.Detail)

        if fileinput.exec():
            filenames = fileinput.selectedFiles()
            filename = filenames[0]
            wordinput = self.get_wordinput(filename)
            self.statusfield.setText(f'Executing query from input file {filename}')
            self.querybox.setText('')
            self.doQuery(wordinput)

    def get_wordinput(self, filename):
        wordinput = defaultdict(list)
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                try:
                    if len(line.strip()) == 0:
                        continue
                    if line.startswith('#'):
                        continue
                    kw, value = line.strip().split('=')
                    kw = kw.strip()
                    value = value.strip()
                    print(f'-{kw}-{value}-')
                    if kw not in ['lemma', 'form', 'unword']:
                        print(f'Invalid category: {line}')
                    else:
                        wordinput[kw].append(value)
                except Exception as e:
                    print(f'Invalid input: {line}', e)
        return wordinput

    def dbquery(self, text: str):
        try:
            newdf, querystatus, querymessage = dbutil.get_frequency_dataframe(self.connection, query=text, grams=True)
            # print(querystatus, querymessage)
            if querystatus < 0:
                raise Exception(querymessage)
            return newdf
        except Exception as e:
            logger.error("Issue with query %s: %s", query, e)
            self.statusfield.setText(f'Issue with query {text}: {e}')
            return None

    def setData(self, df: pd.DataFrame = None):
        if df is None:
            df = pd.DataFrame()
        self.data = df
        self.model = TableModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()


if __name__ == "__main__":

    logger.info('\nLaunching application at %s', datetime.now())
    inifile = 'wm2.ini'
    appconfig, currworkdir = uiutil.get_config(inifile)
    # print(appconfig, currworkdir)
    if not appconfig:
        logger.info("Configuration file '%s' not found", inifile)
        # FIXME: error window if ini file not found

    dbdir = uiutil.get_configvar(appconfig, 'input', 'datadir')
    dbfile = uiutil.get_configvar(appconfig, 'input', 'database')

    if not dbdir:
        if not currworkdir:
            logger.error('No data directory found')
            raise uiutil.ConfigurationError('No data directory found')
        dbdir = join(currworkdir, 'data')
        logger.info('No data directory specified, using current working directory %s', currworkdir)
    if not dbfile:
        dbfile = 's24_c2.db'

    dbfp = join(dbdir, dbfile)
    logger.info("Using database file path %s", dbfp)
    if not exists(dbfp) or getsize(dbfp) == 0:
        logger.debug("File not found: %s; trying current directory for finding data file", dbfp)
        dbfp = join('data', dbfile)
        if not exists(dbfp) or getsize(dbfp) == 0:
            logger.error("No such file: %s", dbfp)
            raise FileNotFoundError(dbfp)

    try:
        logger.info("Connecting to %s...", dbfp)
        sqlcon = dbutil.get_connection(dbfp)
    except Exception as e:
        logger.error("Couldn't connect to %s: %s", dbfp, e)

    app = QApplication(sys.argv)

    w = MainWindow(sqlcon)
    query = "form = 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and form = 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6 and bigramfreq > 6000000"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6"

    # initial query
    w.querybox.setText(query)
    w.textQuery()
    w.show()

    app.exec()
