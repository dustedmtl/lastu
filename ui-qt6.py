"""UI for wordmill application."""

# Copyright (C) 2022 University of Turku
# License: CC-BY-4.0
#
# Starter code based on https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/

# pylint: disable=invalid-name

import sys
from typing import Optional
from os.path import exists, getsize, join
import configparser
# from collections import defaultdict
from pathlib import Path
import time
from datetime import datetime
# import inspect
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
from PyQt6.QtGui import QAction, QKeySequence, QActionGroup
from PyQt6.QtCore import (
    QAbstractTableModel,
    Qt,
    QModelIndex,
    QObject,
    QRunnable,
    QThreadPool,
    QTimer,
    pyqtSlot,
    pyqtSignal,
)


from lib import dbutil, uiutil

homedir = Path.home()
logger = logging.getLogger('wm2')
log_format = logging.Formatter('%(asctime)s %(levelname)s %(message)s',
                               datefmt='%d.%m.%Y %H:%M:%S')
# log_format = '[%(asctime)s] [%(levelname)s] - %(message)s'
# logger.setFormat(log_format)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%d.%m.%Y %H:%M:%S')
logger.setLevel(logging.DEBUG)
logfile_handler = logging.FileHandler(join(homedir, 'wm2log.txt'))
logfile_handler.setFormatter(log_format)
logfile_handler.setLevel(logging.DEBUG)

# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(log_format)
# stream_handler.setLevel(logging.DEBUG)

logger.addHandler(logfile_handler)
# logger.addHandler(stream_handler)


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
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
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


class Signals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str, str)
    result = pyqtSignal(float, pd.DataFrame)


class DBWorker(QRunnable):
    def __init__(self, dbconnection, querytxt: str):
        super().__init__()
        self.signals = (
            Signals()
        )
        self.dbconnection = dbconnection
        self.querytxt = querytxt

    @pyqtSlot()
    def run(self):
        start = time.perf_counter()
        try:
            newdf, querystatus, querymessage = dbutil.get_frequency_dataframe(self.dbconnection,
                                                                              query=self.querytxt,
                                                                              newconnection=True,
                                                                              grams=True)
            if querystatus < 0:
                raise Exception(querymessage)
            end = time.perf_counter()
            diff = end - start
            logger.debug('Query finished in %.1f seconds', diff)
            self.signals.finished.emit()
            self.signals.result.emit(diff, newdf)
        except Exception as we:
            logger.error("Issue with query %s: %s", self.querytxt, we)
            self.signals.error.emit(self.querytxt, str(we))
            self.signals.finished.emit()


class MainWindow(QMainWindow):

    def __init__(self, dbconnection, df=None, appconfig=None):
        super().__init__()
        # super(MainWindow, self).__init__()
        self.setWindowTitle("WM2")
        self.dbconnection = dbconnection
        self.originaldata = df
        self.query_ongoing = False
        self.query_desc = ""
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

        menuaction_quit = QAction("&Quit application", self)
        menuaction_quit.setStatusTip("Quit application")
        menuaction_quit.setShortcut(QKeySequence("Ctrl+q"))
        menuaction_quit.triggered.connect(self.quit)

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
        file_menu.addSeparator()
        file_menu.addAction(menuaction_quit)

        # edit_menu = menu.addMenu("&Edit")

        freq_abs = QAction("&Show absolute frequencies", self)
        freq_rel = QAction("&Show relative frequencies", self)
        freq_all = QAction("&Show both frequencies", self)

        freq_all.triggered.connect(self.showBothFrequencies)
        freq_abs.triggered.connect(self.showAbsoluteFrequencies)
        freq_rel.triggered.connect(self.showRelativeFrequencies)

        freq_all.setCheckable(True)
        freq_abs.setCheckable(True)
        freq_abs.setChecked(True)
        freq_rel.setCheckable(True)

        freq_boxes = QActionGroup(self)
        freq_boxes.setExclusionPolicy(QActionGroup.ExclusionPolicy.Exclusive)

        ag1 = freq_boxes.addAction(freq_all)
        ag2 = freq_boxes.addAction(freq_abs)
        ag3 = freq_boxes.addAction(freq_rel)

        data_menu = menu.addMenu("&Data")
        data_submenu = data_menu.addMenu("Frequencies")
        data_submenu.addAction(ag1)
        data_submenu.addAction(ag2)
        data_submenu.addAction(ag3)

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

        widget = QWidget()
        widget.setLayout(self.layout)
        self.centralwidget = widget
        self.setCentralWidget(widget)
        # print(widget.font().pointSize(), self.table.verticalHeader().font().pointSize())
        # self.setFonts()
        # self.setCopyleftFont()

    def newWindow(self):
        w2 = MainWindow(self.dbconnection, df=self.data, appconfig=self.appconfig)
        w2.originaldata = w2.data
        w2.querybox.setText(self.querybox.text())
        self._otherwindows.append(w2)
        # w2.setData(self.data)
        widget = self.centralwidget
        currentfont = widget.font()
        w2widget = w2.centralwidget
        w2widget.setFont(currentfont)
        w2.setFonts()

        # w2.table.resizeColumnsToContents()
        # w2.resizeWidthToContents()

        # sizehint = w2.layout.sizeHint()
        # width = sizehint.width()
        # w2.setFixedWidth(width+10)
        w2.show()

    def closeWindow(self):
        self.close()

    def showBothFrequencies(self):
        logger.debug("Show both frequencies called")
        df = dbutil.add_relative_frequencies(self.dbconnection,
                                             self.originaldata)
        self.setFilteredData(df)
        self.resizeWidthToContents()

    def showAbsoluteFrequencies(self):
        logger.debug("Show absolute frequencies called")
        self.setData(self.originaldata)
        self.resizeWidthToContents()

    def showRelativeFrequencies(self):
        logger.debug("Show relative frequencies called")
        df = dbutil.add_relative_frequencies(self.dbconnection,
                                             self.originaldata,
                                             drop=True)
        self.setFilteredData(df)
        self.resizeWidthToContents()

    def quit(self):
        logger.debug("Application quit called")
        app.quit()

    def resizeWidthToContents(self):
        sizehint = self.layout.sizeHint()
        width = sizehint.width()
        # for s in inspect.stack():
        #    print(s)
        logger.debug('Setting window width to %d', width)
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
        tablefontsize = currentfontsize - 2
        tableheaderfont = self.table.verticalHeader().font()
        tableheaderfont.setPointSize(tablefontsize)
        # print(currentfontsize, self.table.verticalHeader().font().pointSize(), tablefontsize)
        self.table.verticalHeader().setFont(tableheaderfont)
        self.table.horizontalHeader().setFont(tableheaderfont)
        self.table.resizeColumnsToContents()
        self.resizeWidthToContents()

    def biggerFont(self):
        widget = self.centralwidget
        currentfont = widget.font()
        currentfontsize = currentfont.pointSize()
        newfontsize = currentfontsize + 1
        logger.debug('Changing font size from %d to %d', currentfontsize, newfontsize)
        currentfont.setPointSize(newfontsize)
        widget.setFont(currentfont)
        self.setFonts()

    def smallerFont(self):
        widget = self.centralwidget
        currentfont = widget.font()
        currentfontsize = currentfont.pointSize()
        newfontsize = currentfontsize - 1
        logger.debug('Changing font size from %d to %d', currentfontsize, newfontsize)
        currentfont.setPointSize(newfontsize)
        widget.setFont(currentfont)
        self.setFonts()

    def enter(self):
        # print('enter pressed')
        self.textQuery()

    def textQuery(self):
        querytext = self.querybox.text()
        self.statusfield.setText(f'Executing query: {querytext}')
        self.query_desc = ''
        self.doQuery(querytext)

    def doQuery(self, queryinput):
        # start = time.perf_counter()
        if self.query_ongoing:
            logger.warning('Query already ongoing, please wait')
        else:
            # FIXME: disable some input menu actions for the duration of the query?
            worker = DBWorker(dbconnection=self.dbconnection,
                              querytxt=queryinput)
            worker.signals.result.connect(self.setQueryResult)
            worker.signals.finished.connect(self.setQueryFinished)
            worker.signals.error.connect(self.setQueryError)
            self.query_ongoing = True
            threadpool.start(worker)

    def setQueryFinished(self):
        # print('Query finished')
        self.query_ongoing = False

    def setQueryResult(self, exectime: float, querydf: pd.DataFrame):
        if querydf is not None and len(querydf) > 0:
            self.setData(querydf)
            self.originaldata = self.data
            self.statusfield.setText(f'Executing query{self.query_desc} .. done: {len(querydf)} rows returned in {exectime:.1f} seconds')
            self.resizeWidthToContents()

    def setQueryError(self, text: str, error: str):
        self.statusfield.setText(f'Issue with query {text}: {error}')

    def inputFileQuery(self):
        fileinput = QFileDialog()
        fileinput.setFileMode(QFileDialog.FileMode.ExistingFile)
        fileinput.setNameFilter("Text files (*.txt)")
        fileinput.setViewMode(QFileDialog.ViewMode.Detail)

        listtypes = ['lemma', 'form', 'unword']

        if fileinput.exec():
            filenames = fileinput.selectedFiles()
            filename = filenames[0]
            wordinput = dbutil.get_wordinput(filename)
            self.querybox.setText('')
            self.query_desc = f' from file {filename}'
            # print(wordinput)
            inputkeys = list(wordinput.keys())
            try:
                if len(inputkeys) != 1:
                    raise ValueError(f'No valid data found in file {filename}')
                if inputkeys[0] not in listtypes:
                    raise ValueError(f'No valid data found in file {filename}')
                if inputkeys[0] == 'unword':
                    self.query_desc = ''
                    unworddf = dbutil.get_unword_bigrams(self.dbconnection, wordinput)
                    self.setQueryResult(0, unworddf)
                else:
                    self.statusfield.setText(f'Executing query from input file {filename}')
                    self.doQuery(wordinput)
            except ValueError as ve:
                self.statusfield.setText(str(ve))

    def exportFile(self):
        logger.debug("Export file called")
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

        logger.debug('Output from export file dialog: %s', filename)

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
        logger.debug("Copy to clipboard called")
        df = self.data
        df.to_clipboard(index=False)

    def nullAction(self):
        logger.info("Action not implemented")

    def setData(self, df: pd.DataFrame = None):
        if df is None:
            df = pd.DataFrame()
        self.data = df
        self.model = TableModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()

    def setFilteredData(self, df: pd.DataFrame):
        self.data = df
        self.model = TableModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()


def selectDataBase() -> Optional[str]:
    """Database selector."""
    fileinput = QFileDialog(caption="Choose database file to load")
    fileinput.setFileMode(QFileDialog.FileMode.ExistingFile)
    fileinput.setNameFilter("Database files (*.db)")
    fileinput.setViewMode(QFileDialog.ViewMode.Detail)

    if fileinput.exec():
        filenames = fileinput.selectedFiles()
        filename = filenames[0]
        return filename

    return None


def getDataBaseFile(cfg: configparser.ConfigParser, currdir: str) -> Optional[str]:
    """Get database file using various methods."""
    dbdir = uiutil.get_configvar(cfg, 'input', 'datadir')
    dbf = uiutil.get_configvar(cfg, 'input', 'database')

    if not dbdir:
        if not currdir:
            logger.error('No data directory found')
            raise uiutil.ConfigurationError('No data directory found')
        dbdir = join(currdir, 'data')
        logger.info('No data directory specified, using current working directory %s', currdir)
    if not dbf:
        dbf = 'wm2database.db'

    dbpath = join(dbdir, dbf)
    logger.info("Trying database file in path %s", dbpath)
    if not exists(dbpath) or getsize(dbpath) == 0:
        dbpath = join('data', dbf)
        logger.info("File not found: %s; trying current directory for finding data file", dbpath)
        if not exists(dbpath) or getsize(dbpath) == 0:
            choosedb = selectDataBase()
            logger.debug('Database chosen with file dialog: %s', choosedb)
            if not choosedb:
                logger.error("No such file: %s", dbpath)
                raise FileNotFoundError(dbpath)
            dbpath = choosedb

    return dbpath

if __name__ == "__main__":

    logger.info('Launching application at %s', datetime.now())
    inifile = 'wm2.ini'
    appconfig, currdir = uiutil.get_config(inifile)
    # print(appconfig, currworkdir)
    if not appconfig:
        logger.warning("Configuration file '%s' not found", inifile)
        # FIXME: error window if ini file not found

    app = QApplication(sys.argv)
    dbfile = getDataBaseFile(appconfig, currdir)

    threadpool = QThreadPool()
    logger.debug("Multithreading with maximum %d threads",
                 threadpool.maxThreadCount())

    logger.debug('Got final database file: %s', dbfile)

    try:
        logger.info("Connecting to %s...", dbfile)
        dbconn = dbutil.DatabaseConnection(dbfile)
    except Exception as e:
        logger.error("Couldn't connect to %s: %s", dbfile, e)

    w = MainWindow(dbconn, appconfig=appconfig)

    # initial query
    query = "form = 'silmäsi' and frequency > 10"
    w.querybox.setText(query)
    w.textQuery()
    w.show()

    app.exec()
