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
from UliPlot.XLSX import auto_adjust_xlsx_column_width

from PyQt6.QtWidgets import (
    QTableView, QApplication, QMainWindow, QWidget,
    QGridLayout,
    QAbstractScrollArea,
    QFileDialog,
    QMessageBox,
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtGui import QAction, QKeySequence
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
            value = self._data.iloc[index.row()][index.column()]
            # return str(self._data.iloc[index.row()][index.column()])
            if isinstance(value, float):
                return "%.3f" % value
            return str(value)

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


class MainWindow(QMainWindow):

    def __init__(self, dbconnection, df=None, appconfig=None):
        super().__init__()
        # super(MainWindow, self).__init__()
        self.setWindowTitle("WM2")

        self.dbconnection = dbconnection
        self.appconfig = appconfig
        self._otherwindows = []
        self.layout = QGridLayout()

        # newbutton = QPushButton("New window")
        # newbutton.clicked.connect(self.newWindow)
        # self.layout.addWidget(newbutton, 0, 1, 1, 1)

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

        self.setData(df)

        self.layout.addWidget(self.table, 3, 0, 1, 2)

        self.copyleft = QLabel('Copyright (c) 2022 University of Turku')
        self.copyleft.setObjectName('copyleft')
        self.layout.addWidget(self.copyleft, 4, 0, 1, 2)
        self.copyleft.setAlignment(Qt.AlignmentFlag.AlignRight)

        menu = self.menuBar()

        menuaction_input = QAction("&Input", self)
        menuaction_input.setStatusTip("Input from wordlist")
        menuaction_input.setShortcut(QKeySequence("Ctrl+i"))
        menuaction_input.triggered.connect(self.inputFileQuery)

        menuaction_export = QAction("&Export", self)
        menuaction_export.setStatusTip("Export to file")
        menuaction_export.setShortcut(QKeySequence("Ctrl+s"))
        menuaction_export.triggered.connect(self.exportFile)

        menuaction_new = QAction("&New window", self)
        menuaction_new.setStatusTip("New window")
        menuaction_new.setShortcut(QKeySequence("Ctrl+n"))
        menuaction_new.triggered.connect(self.newWindow)

        menuaction_close = QAction("&Close window", self)
        menuaction_close.setStatusTip("Close current window")
        menuaction_close.setShortcut(QKeySequence("Ctrl+w"))
        menuaction_close.triggered.connect(self.closeWindow)

        menuaction_clipcopy = QAction("&Copy", self)
        menuaction_clipcopy.setStatusTip("Copy to clipboard")
        menuaction_clipcopy.setShortcut(QKeySequence("Ctrl+e"))
        menuaction_clipcopy.triggered.connect(self.copyToClip)

        file_menu = menu.addMenu("&File")
        file_menu.addAction(menuaction_input)
        file_menu.addAction(menuaction_export)
        file_menu.addAction(menuaction_clipcopy)
        file_menu.addSeparator()
        file_menu.addAction(menuaction_new)
        file_menu.addAction(menuaction_close)

        # edit_menu = menu.addMenu("&Edit")

        menuaction_smaller = QAction("&Smaller fontsize", self)
        menuaction_smaller.setStatusTip("Smaller fontsize")
        menuaction_smaller.setShortcut(QKeySequence("Ctrl+-"))
        menuaction_smaller.triggered.connect(self.smallerFont)

        menuaction_bigger = QAction("&Bigger fontsize", self)
        menuaction_bigger.setStatusTip("Bigger fontsize")
        menuaction_bigger.setShortcut(QKeySequence("Ctrl++"))
        menuaction_bigger.triggered.connect(self.biggerFont)

        window_menu = menu.addMenu("&Window")
        window_menu.addSeparator()
        window_menu.addAction(menuaction_smaller)
        window_menu.addAction(menuaction_bigger)

        # tablevfont = self.table.verticalHeader().font()
        # print(dir(tablevfont))

        widget = QWidget()
        widget.setLayout(self.layout)
        self.centralwidget = widget
        self.setCentralWidget(widget)
        self.setCopyleftFont()

    def newWindow(self):
        w2 = MainWindow(self.dbconnection, appconfig=self.appconfig)
        w2.querybox.setText(self.querybox.text())
        self._otherwindows.append(w2)
        w2.setData(self.data)

        widget = self.centralwidget
        currentfont = widget.font()
        w2widget = w2.centralwidget
        w2widget.setFont(currentfont)
        w2.setFonts()

        w2.table.resizeColumnsToContents()
        w2.resizeWidthToContents()

        # sizehint = w2.layout.sizeHint()
        # width = sizehint.width()
        # w2.setFixedWidth(width+10)
        w2.show()

    def closeWindow(self):
        self.close()

    def resizeWidthToContents(self):
        sizehint = self.layout.sizeHint()
        width = sizehint.width()
        print(f'Setting window width to {width}')
        # self.setFixedSize(self.layout.sizeHint())
        self.setFixedWidth(width+5)
        # self.setMinimumSize(width, 0)

    def setCopyleftFont(self):
        widget = self.centralwidget
        currentfont = widget.font()
        currentfontsize = currentfont.pointSize()
        newfontsize = currentfontsize - 1
        currentfont.setPointSize(newfontsize)
        self.copyleft.setFont(currentfont)

    def setFonts(self):
        self.setCopyleftFont()
        currentfontsize = self.centralwidget.font().pointSize()
        tablefontsize = currentfontsize - 1
        tableheaderfont = self.table.verticalHeader().font()
        tableheaderfont.setPointSize(tablefontsize)
        self.table.verticalHeader().setFont(tableheaderfont)
        self.table.horizontalHeader().setFont(tableheaderfont)
        self.table.resizeColumnsToContents()
        self.resizeWidthToContents()

    def biggerFont(self):
        widget = self.centralwidget
        currentfont = widget.font()
        currentfontsize = currentfont.pointSize()
        newfontsize = currentfontsize + 1
        print(f'Changing font size from {currentfontsize} to {newfontsize}')
        currentfont.setPointSize(newfontsize)
        widget.setFont(currentfont)
        self.setFonts()

    def smallerFont(self):
        widget = self.centralwidget
        currentfont = widget.font()
        currentfontsize = currentfont.pointSize()
        newfontsize = currentfontsize - 1
        print(f'Changing font size from {currentfontsize} to {newfontsize}')
        currentfont.setPointSize(newfontsize)
        widget.setFont(currentfont)
        self.setFonts()

    def enter(self):
        # print('enter pressed')
        self.textQuery()

    def textQuery(self):
        querytext = self.querybox.text()
        # FIXME: ensure that the below text shows. Issue with threads?
        self.statusfield.setText(f'Executing query: {querytext}')
        self.doQuery(querytext)

    def doQuery(self, queryinput):
        start = time.perf_counter()
        querydf = self.dbquery(queryinput)

        if querydf is not None:
            self.setData(querydf)
            end = time.perf_counter()

            self.statusfield.setText(f'Executing query.. done: {len(querydf)} rows returned in {end - start:.1f} seconds')
            self.resizeWidthToContents()

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

    def exportFile(self):
        print("Export file called")
        caption = "Save As"

        file_filters = [
            "Microsoft Excel (*.xlsx)",
            "Comma Separated Values (*.csv)",
            "Tab Separated Values (*.tsv)"
        ]

        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            caption=caption,
            directory='',
            filter=';;'.join(file_filters),
            initialFilter=file_filters[0],
        )

        print(filename, selected_filter)

        if filename:
            if exists(filename):
                # Existing file, ask the user for confirmation.
                write_confirmed = QMessageBox.question(
                    self,
                    "Overwrite file?",
                    f"The file {filename} exists. Are you sure you want to overwrite it?",
                )
            else:
                # File does not exist, always-confirmed.
                write_confirmed = True

            if write_confirmed:
                df = self.data
                if 'csv' in selected_filter or 'tsv' in selected_filter:
                    separator = ',' if 'csv' in selected_filter else '\t'
                    df.to_csv(filename, sep=separator, index=False)
                elif 'xlsx' in selected_filter:
                    with pd.ExcelWriter(filename) as excelwriter:
                        df.to_excel(excelwriter, sheet_name='WM2 words', index=False)
                        auto_adjust_xlsx_column_width(df, excelwriter, sheet_name='WM2 words', index=False)

    def copyToClip(self):
        print("Copy to clipboard")
        df = self.data
        df.to_clipboard(index=False)

    def nullAction(self):
        print("Action not implemented")

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
            newdf, querystatus, querymessage = dbutil.get_frequency_dataframe(self.dbconnection, query=text, grams=True)
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
        dbconn = dbutil.DatabaseConnection(dbfp)
    except Exception as e:
        logger.error("Couldn't connect to %s: %s", dbfp, e)

    app = QApplication(sys.argv)

    w = MainWindow(dbconn, appconfig=appconfig)
    query = "form = 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and form = 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6 and bigramfreq > 6000000"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6"

    # initial query
    w.querybox.setText(query)
    w.textQuery()
    w.show()

    app.exec()
