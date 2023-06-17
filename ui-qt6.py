"""UI for wordmill application."""

# Copyright (C) 2022-2023 University of Turku
# License: CC-BY-4.0
#
# Starter code based on https://www.pythonguis.com/tutorials/pyqt6-qtableview-modelviews-numpy-pandas/

# pylint: disable=invalid-name

import sys
# import faulthandler; faulthandler.enable()
from typing import Optional
from os.path import exists, getsize, join
import configparser
# from collections import defaultdict
from pathlib import Path
import time
from datetime import datetime
import inspect
import argparse
import logging
import logging.config
import pandas as pd
from UliPlot.XLSX import auto_adjust_xlsx_column_width

from PyQt6.QtWidgets import (
    QTableView, QApplication, QMainWindow, QWidget,
    QHeaderView,
    QGridLayout,
    QSizePolicy,
    QAbstractScrollArea,
    QFileDialog,
    QMessageBox,
    # QCheckBox,
    # QToolBar,
    QLineEdit, QPushButton, QLabel
)
from PyQt6.QtGui import QAction, QKeySequence, QActionGroup
from PyQt6.QtCore import (
    QAbstractTableModel,
    # QSortFilterProxyModel,
    Qt,
    QModelIndex,
    QObject,
    QRunnable,
    QThreadPool,
    # QTimer,
    pyqtSlot,
    pyqtSignal,
)


from lib import dbutil, uiutil

homedir = Path.home()


class LogQueryFilter(logging.Filter):
    """Query logging filter."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Reject log lines that don't start with 'Query:'."""
        message = record.message
        if message.startswith('Query:'):
            record.query = message[7:]
            return True

        return False


wm2logconfig = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'handlers': ['console', 'file_handler', 'history_handler'],
        'level': 'DEBUG',
    },
    'filters': {
        "justquery": {
            '()': LogQueryFilter,
        },
    },
    'formatters': {
        'default_formatter': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%d.%m.%Y %H:%M:%S'
        },
        'just_msg_mam': {
            'format': '%(query)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default_formatter',
            'level': 'INFO'
        },
        'file_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'default_formatter',
            # 'filename': join(homedir, 'last_log.txt'),
            'level': 'DEBUG'
        },
        'history_handler': {
            'class': 'logging.FileHandler',
            'formatter': 'just_msg_mam',
            # 'filename': join(homedir, 'lastu_history.txt'),
            'filters': ['justquery'],
            'level': 'INFO'
        }
    },
}

cfg, currdir = uiutil.get_config('lastu.ini')
# print(cfg, currdir)

try:
    logconfig = uiutil.log_handler(wm2logconfig, currdir)
    logging.config.dictConfig(logconfig)
    logger = logging.getLogger('wm2')
    logger.debug('Starting logger')
except ValueError as ve:
    logconfig = uiutil.log_handler(wm2logconfig, homedir)
    logging.config.dictConfig(logconfig)
    logger = logging.getLogger('wm2')
    logger.debug('Starting logger')
    logger.warning('Exception: %s', ve)
    logger.warning('Could not write logs to directory %s: writing to directory %s instead', currdir, homedir)


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
            if isinstance(value, str) and len(value) > 60:
                value = value[:60] + "..."
            return str(value)

        elif role == Qt.ItemDataRole.ToolTipRole:
            value = self._data.iloc[index.row()][index.column()]
            # return str(self._data.iloc[index.row()][index.column()])
            if isinstance(value, str) and len(value) > 60:
                return value
            return None

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

class WMTableView(QTableView):

    def keyPressEvent(self, event):
        selectWholeRows = True
        # logger.info('Key pressed: %s, %s', event.key(), event.modifiers())
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Get the selected cells
            model = self.model()
            if model is not None:
                selection = self.selectionModel().selection()
                if not selection.isEmpty():
                    # Build the table data as a string
                    table = ""
                    rows = sorted(index.row() for index in selection.indexes())
                    cols = sorted(index.column() for index in selection.indexes())
                    indexes = selection.indexes()

                    if selectWholeRows:
                        for row in range(rows[0], rows[-1]+1):
                            for col in range(cols[0], cols[-1]+1):
                                index = model.index(row, col)
                                if self.isIndexHidden(index):
                                    # Skip hidden cells
                                    continue
                                text = str(index.data())
                                table += text
                                # print(row, col, text)
                                if col != cols[-1]:
                                    table += "\t"
                            if row != rows[-1]:
                                table += "\n"
                    else:
                        lastrow = -1
                        # lastcol = -1
                        for index in sorted(indexes):
                            if self.isIndexHidden(index):
                                # Skip hidden cells
                                continue
                            text = str(index.data())
                            row = index.row()
                            col = index.column()
                            if lastrow == -1:
                                # first element
                                pass
                            elif lastrow == row:
                                # same row
                                table += "\t"
                            else:
                                # change of row
                                table += "\n"

                            # print(index.row(), index.column(), text)
                            table += text
                            lastrow = row
                            # lastcol = col
                    # Copy the table data to the clipboard
                    clipboard = QApplication.clipboard()
                    clipboard.setText(table)
        else:
            # Let the base class handle the event
            super().keyPressEvent(event)

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
                                                                              grams=True,
                                                                              lemmas=True)
            if querystatus < 0:
                raise Exception(querymessage)
            end = time.perf_counter()
            diff = end - start
            logger.debug('Query finished in %.1f seconds', diff)
            self.signals.finished.emit()
            self.signals.result.emit(diff, newdf)
        except Exception as we:
            logger.error("Issue with query '%s':\n%s", self.querytxt, we)
            self.signals.error.emit(self.querytxt, str(we))
            self.signals.finished.emit()


class ConfigFile():
    def __init__(self, appcfg=None):
        super().__init__()
        self.cfgdict = {}
        if appcfg:
            for section in appcfg.sections():
                for key, value in appcfg[section].items():
                    value = value.strip('"').strip("'")
                    if value.isnumeric():
                        value = int(value)
                    if value == 'True':
                        value = True
                    elif value == 'False':
                        value = False
                    self.cfgdict[f'{section}.{key}'] = value

    def getConfigValue(self, key, defaultvalue=None):
        return self.cfgdict.get(key, defaultvalue)


class MainWindow(QMainWindow):

    def __init__(self,
                 dbconnection,
                 df=None,
                 appconfig=None,
                 original=True):
        super().__init__()
        # super(MainWindow, self).__init__()
        self.setWindowTitle("LASTU")
        self.dbconnection = dbconnection
        # self.originaldata = df
        self.appversion = uiutil.get_application_version()
        self.data = df
        self.fulldata = None
        self.hidecolumns = set()
        self.query_ongoing = False
        self.query_desc = ""
        self.appconfig = appconfig
        self.config = ConfigFile(appconfig)
        self._otherwindows = []
        self.layout = QGridLayout()
        self.mode = "database"
        self.inputfilename = None
        self.inputprocessfilename = None

        self.clearresultsifempty = False
        # self.lemmacb = QCheckBox()
        # self.formcb = QCheckBox()
        # self.freqcb = QCheckBox()
        # self.featcb = QCheckBox()
        # self.lemmacb.setCheckState(Qt.CheckState.Checked)
        # self.formcb.setCheckState(Qt.CheckState.Checked)
        # self.freqcb.setCheckState(Qt.CheckState.Checked)
        # self.featcb.setCheckState(Qt.CheckState.Checked)
        # self.lemmacb.stateChanged.connect(self.nullAction)
        # self.formcb.stateChanged.connect(self.nullAction)
        # self.freqcb.stateChanged.connect(self.nullAction)
        # self.featcb.stateChanged.connect(self.nullAction)

        # toolbar = QToolBar("Data")
        # toolbar.addWidget(QLabel('Data'))
        # toolbar.addSeparator()
        # toolbar.addWidget(QLabel('Lemmas'))
        # toolbar.addWidget(self.lemmacb)
        # toolbar.addWidget(QLabel('Forms'))
        # toolbar.addWidget(self.formcb)
        # toolbar.addWidget(QLabel('Frequencies'))
        # toolbar.addWidget(self.freqcb)
        # toolbar.addWidget(QLabel('Features'))
        # toolbar.addWidget(self.featcb)
        # self.layout.addWidget(toolbar, 1, 0, 1, 1)

        self.querybox = QLineEdit()
        self.querybox.returnPressed.connect(self.enter)
        self.layout.addWidget(self.querybox, 1, 0, 1, 2)

        button = QPushButton("Query")
        button.clicked.connect(self.textQuery)
        self.layout.addWidget(button, 1, 2, 1, 1)
        button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)

        self.statusfield = QLabel()
        # self.layout.addWidget(self.statusfield, 1, 0, 1, 2)
        self.layout.addWidget(self.statusfield, 2, 0, 1, 3)

        # filebutton = QPushButton("Input")
        # filebutton.clicked.connect(self.inputFileQuery)
        # self.layout.addWidget(filebutton, 2, 1, 1, 1)

        self.table = WMTableView()
        # self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        # cell width is based on their contents
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        # view.setSelectionBehavior(QTableView.SelectRows)

        self.layout.addWidget(self.table, 3, 0, 1, 3)

        self.dbnamefield = QLabel()
        self.setDbNameField()
        # self.dbnamefield = QLabel(f'Database file: {self.dbconnection.dbfile}')
        self.dbnamefield.setObjectName('dbfile')
        self.layout.addWidget(self.dbnamefield, 4, 0, 1, 1)
        # self.dbnamefield.setAlignment(Qt.AlignmentFlag.AlignRight)

        copylefttext = 'Copyright (c) 2022-2023 University of Turku'
        # print(f'-{self.appversion}-')
        if self.appversion is not None and len(self.appversion) > 0:
            copylefttext = f'LASTU version {self.appversion}. {copylefttext}'
        self.copyleft = QLabel(copylefttext)
        self.copyleft.setObjectName('copyleft')
        self.layout.addWidget(self.copyleft, 4, 1, 1, 2)
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

        menuaction_newempty = QAction("&New empty window", self)
        menuaction_newempty.setStatusTip("New empty window")
        menuaction_newempty.setShortcut(QKeySequence("Shift+Ctrl+n"))
        menuaction_newempty.triggered.connect(self.newEmptyWindow)

        menuaction_close = QAction("&Close window", self)
        menuaction_close.setStatusTip("Close current window")
        menuaction_close.setShortcut(QKeySequence("Ctrl+w"))
        menuaction_close.triggered.connect(self.closeWindow)

        menuaction_opendb = QAction("&Open database", self)
        menuaction_opendb.setStatusTip("Open database")
        menuaction_opendb.setShortcut(QKeySequence("Ctrl+d"))
        menuaction_opendb.triggered.connect(self.openDatabase)

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
        file_menu.addAction(menuaction_newempty)
        file_menu.addAction(menuaction_close)
        file_menu.addSeparator()
        file_menu.addAction(menuaction_opendb)
        file_menu.addSeparator()
        file_menu.addAction(menuaction_quit)

        # edit_menu = menu.addMenu("&Edit")

        self.freq_all = QAction("&Show both frequencies", self)
        self.freq_abs = QAction("&Show absolute frequencies", self)
        self.freq_rel = QAction("&Show relative frequencies", self)

        self.freq_all.setShortcut(QKeySequence("Ctrl+1"))
        self.freq_abs.setShortcut(QKeySequence("Ctrl+2"))
        self.freq_rel.setShortcut(QKeySequence("Ctrl+3"))

        self.freq_all.triggered.connect(self.filterColumns)
        self.freq_abs.triggered.connect(self.filterColumns)
        self.freq_rel.triggered.connect(self.filterColumns)

        self.freq_all.setCheckable(True)
        self.freq_abs.setCheckable(True)
        self.freq_abs.setChecked(True)
        self.freq_rel.setCheckable(True)

        freq_boxes = QActionGroup(self)
        freq_boxes.setExclusionPolicy(QActionGroup.ExclusionPolicy.Exclusive)

        ag1 = freq_boxes.addAction(self.freq_all)
        ag2 = freq_boxes.addAction(self.freq_abs)
        ag3 = freq_boxes.addAction(self.freq_rel)

        self.hide_empty_columns = QAction("&Hide empty columns", self)
        self.hide_empty_columns.setShortcut(QKeySequence("Ctrl+4"))
        self.hide_empty_columns.setCheckable(True)
        self.hide_empty_columns.triggered.connect(self.filterColumns)

        data_menu = menu.addMenu("&Data")
        data_submenu = data_menu.addMenu("Frequencies")
        data_submenu.addAction(ag1)
        data_submenu.addAction(ag2)
        data_submenu.addAction(ag3)
        data_menu.addAction(self.hide_empty_columns)

        self.cataction_lemma = QAction("&Show lemmas", self)
        self.cataction_lemma.setCheckable(True)
        self.cataction_lemma.setChecked(True)
        self.cataction_lemma.setShortcut(QKeySequence("Ctrl+5"))
        self.cataction_lemma.triggered.connect(self.filterColumns)

        self.cataction_form = QAction("&Show forms", self)
        self.cataction_form.setCheckable(True)
        self.cataction_form.setChecked(True)
        self.cataction_form.setShortcut(QKeySequence("Ctrl+6"))
        self.cataction_form.triggered.connect(self.filterColumns)

        self.cataction_freq = QAction("&Show frequencies", self)
        self.cataction_freq.setCheckable(True)
        self.cataction_freq.setChecked(True)
        self.cataction_freq.setShortcut(QKeySequence("Ctrl+7"))
        self.cataction_freq.triggered.connect(self.filterColumns)

        self.cataction_feat = QAction("&Show features", self)
        self.cataction_feat.setCheckable(True)
        self.cataction_feat.setChecked(True)
        self.cataction_feat.setShortcut(QKeySequence("Ctrl+8"))
        self.cataction_feat.triggered.connect(self.filterColumns)

        data_catmenu = data_menu.addMenu("Categories")
        data_catmenu.addAction(self.cataction_lemma)
        data_catmenu.addAction(self.cataction_form)
        data_catmenu.addAction(self.cataction_freq)
        data_catmenu.addAction(self.cataction_feat)

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

        if df:
            self.setData(df)
            # self.filterColumns()

        widget = QWidget()
        widget.setLayout(self.layout)
        self.centralwidget = widget
        self.setCentralWidget(widget)
        if original:
            self.table.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.DescendingOrder)
            if (fontsize := self.config.getConfigValue('style.fontsize')) is not None:
                self.setFonts(fontsize)
            self.table.horizontalHeader().sectionClicked.connect(self.sortData)
        # print(widget.font().pointSize(), self.table.verticalHeader().font().pointSize())
        # self.setFonts()
        # self.setCopyleftFont()

    def newWindow(self, dbconnection: None) -> QMainWindow:

        dbc = self.dbconnection
        if dbconnection:
            logger.info('Opening new window with database %s', dbconnection.dbfile)
            dbc = dbconnection
        else:
            logger.info('Opening new window with existing database')

        w2 = MainWindow(dbc, original=False)

        # w2.originaldata = w2.data
        w2.appconfig = self.appconfig
        w2.config = self.config
        w2.querybox.setText(self.querybox.text())
        # FIXME: proper way to manage windows?
        self._otherwindows.append(w2)
        w2.hidecolumns = self.hidecolumns
        if self.fulldata is not None:
            w2.fulldata = self.fulldata
        w2.setData(self.data)
        # w2.filterColumns()
        widget = self.centralwidget
        currentfont = widget.font()
        w2widget = w2.centralwidget
        w2widget.setFont(currentfont)
        w2.setFonts()

        # Inherit menu checkboxes
        w2.freq_all.setChecked(self.freq_all.isChecked())
        w2.freq_abs.setChecked(self.freq_abs.isChecked())
        w2.freq_rel.setChecked(self.freq_rel.isChecked())
        w2.hide_empty_columns.setChecked(self.hide_empty_columns.isChecked())

        w2.cataction_lemma.setChecked(self.cataction_lemma.isChecked())
        w2.cataction_form.setChecked(self.cataction_form.isChecked())
        w2.cataction_freq.setChecked(self.cataction_freq.isChecked())
        w2.cataction_feat.setChecked(self.cataction_feat.isChecked())

        # Inherit sort order
        sortcol = self.table.horizontalHeader().sortIndicatorSection()
        sortorder = self.table.horizontalHeader().sortIndicatorOrder()
        w2.table.horizontalHeader().setSortIndicator(sortcol, sortorder)
        # w2.table.horizontalHeader().sortIndicatorChanged.connect(w2.sortData)
        w2.table.horizontalHeader().sectionClicked.connect(w2.sortData)

        w2.mode = self.mode
        w2.inputfilename = self.inputfilename
        if w2.mode == 'inputfile':
            w2.setDbNameField(self.inputfilename)
            # w2.dbnamefield.setText(f'Database file: {self.dbconnection.dbfile}\nInput file: {self.inputfilename}')
        w2.show()

        # The query is inherited from the previous window.
        # If the results of this query are empty, also show empty window.
        w2.clearresultsifempty = True

        return w2

    def newEmptyWindow(self) -> QMainWindow:
        w2 = self.newWindow(self.dbconnection)
        w2.mode = "database"
        w2.fulldata = None
        w2.setData(None)
        w2.setDbNameField()
        # w2.dbnamefield.setText(f'Database file: {self.dbconnection.dbfile}')
        w2.querybox.setText("")

    def setDbNameField(self,
                       inputfilename: Optional[str] = None):
        dbname = self.dbconnection.dbfile
        parts = dbname.replace('\\', '/').split('/')
        showlength = 2
        if len(parts) > showlength:
            showdbname = '.../' + '/'.join(parts[-showlength:])
        else:
            showdbname = dbname

        logger.debug("Setting dbname field as %s", showdbname)

        if inputfilename is not None:
            ifparts = inputfilename.replace('\\', '/').split('/')
            if len(ifparts) > showlength:
                showifname = '.../' + '/'.join(ifparts[-showlength:])
            else:
                showifname = inputfilename
            logger.debug("Setting inputfile field as %s", showifname)
            self.dbnamefield.setText(f'Database file: {showdbname}\nInput file: {showifname}')
        else:
            self.dbnamefield.setText(f'Database file: {showdbname}')

    def closeWindow(self):
        self.close()

    def openDatabase(self):
        choosedb = selectDataBase()
        logger.info('Database chosen with file dialog: %s', choosedb)
        if choosedb:
            try:
                logger.info("Connecting to %s...", choosedb)
                dbconn = dbutil.DatabaseConnection(choosedb)
                metadata = dbutil.adhoc_query(dbconn.connection, 'select * from metadata')
                logger.info('Database metadata: %s', metadata)
                if (rowlimit := configfile.getConfigValue('query.fetchrows')) is not None:
                    logger.debug('Setting row limit to %d', rowlimit)
                    dbconn.rowlimit(rowlimit)

                    if (opendbwithnew := configfile.getConfigValue('general.opendbwithnewwindow')) is True:
                        if self.mode == 'inputfile':
                            logger.info("Previous had input file mode, opening new empty window")
                            neww = self.newWindow(dbconnection=dbconn)
                            neww.mode = "database"
                            neww.fulldata = None
                            neww.setData(None)
                            neww.setDbNameField()
                            # neww.dbnamefield.setText(f'Database file: {neww.dbconnection.dbfile}')
                            neww.querybox.setText("")
                        else:
                            neww = self.newWindow(dbconnection=dbconn)
                            neww.mode = "database"
                            neww.setDbNameField()
                            # neww.dbnamefield.setText(f'Database file: {neww.dbconnection.dbfile}')
                            neww.textQuery()
                    else:
                        self.dbconnection = dbconn
                        if self.mode == 'inputfile':
                            logger.info("Previous had input file mode, emptying window")
                            self.querybox.setText("")
                            self.fulldata = None
                            self.setData(None)
                            self.statusfield.setText('')
                        self.setDbNameField()
                        # self.dbnamefield.setText(f'Database file: {self.dbconnection.dbfile}')
                        self.mode = "database"
            except Exception as e:
                logger.error("Couldn't connect to %s: %s", dbfile, e)

    def unique_cols(self, df):
        a = df.to_numpy()
        return (a[0] == a).all(0)

    def hideEmpty(self):
        df = self.data
        values = list(df.loc[0].values)
        columns = df.columns
        uniques = self.unique_cols(df)
        hide = []
        for col, val, unique in zip(columns, values, uniques):
            # print(col, val, unique)
            if val == '_' and unique:
                hide.append(col)
        if hide:
            logger.debug('Hiding empty columns: %s', hide)
        return hide

    def hideCategories(self):
        df = self.data
        shows = {
            'lemma': self.cataction_lemma.isChecked(),
            'form': self.cataction_form.isChecked(),
            'bigramfreq': self.cataction_freq.isChecked(),
            'feats': self.cataction_feat.isChecked(),
        }
        hide = []
        columns = list(df.columns)
        anchors = ['lemma', 'form', 'bigramfreq', 'feats']
        mode = None
        for col in columns:
            if col in anchors:
                mode = col
            if mode:
                if mode not in shows:
                    continue
                if not shows[mode]:
                    hide.append(col)
        if hide:
            logger.debug('Hiding category columns: %s', hide)

        return hide

    def hideFrequencies(self):
        fields = [
            'lemmafreq',
            'frequency',
            'bigramfreq',
            'initgramfreq',
            'fingramfreq',
        ]
        hide = []

        if self.freq_abs.isChecked():
            # remove relative freqs
            hide = ['rel' + f for f in fields]
        elif self.freq_rel.isChecked():
            # remove absolute freqs
            hide = fields

        if hide:
            logger.debug('Hiding frequency columns: %s', hide)

        return hide

    def filterColumns(self):

        # for f in inspect.stack():
        #    print('-', inspect.getframeinfo(f[0]))

        hidecolumns = set()
        hidefreqs = self.hideFrequencies()
        hidecats = self.hideCategories()
        hidecolumns.update(hidefreqs)
        hidecolumns.update(hidecats)
        if self.hide_empty_columns.isChecked():
            hideempty = self.hideEmpty()
            hidecolumns.update(hideempty)
        self.hidecolumns = hidecolumns

        # assume dataframe has been stored to data
        header = self.table.horizontalHeader()
        columns = list(self.data.columns)

        for colidx, col in enumerate(columns):
            if col in self.hidecolumns:
                # print('Hiding', col, colidx)
                header.hideSection(colidx)
            else:
                header.showSection(colidx)

        self.resizeWidthToContents()

    def quit(self):
        logger.debug("Application quit called")
        app.quit()

    def resizeWidthToContents(self):
        sizehint = self.layout.sizeHint()
        width = sizehint.width()
        # for s in inspect.stack():
        #    print(s)
        if self.config.getConfigValue('general.autoresize', False):
            logger.debug('Setting window width to %d', width)
            self.setFixedWidth(width+5)
        if width < 600:
            self.setMinimumSize(600, 0)

    def setCopyleftFont(self):
        widget = self.centralwidget
        currentfont = widget.font()
        currentfontsize = currentfont.pointSize()
        newfontsize = currentfontsize - 1
        currentfont.setPointSize(newfontsize)
        self.copyleft.setFont(currentfont)

    def setFonts(self, size: int = None):
        if size:
            widget = self.centralwidget
            currentfont = widget.font()
            logger.debug('Setting font size to %d', size)
            currentfont.setPointSize(size)
            widget.setFont(currentfont)

        # self.setCopyleftFont()
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
        if self.mode == "inputfile":
            logger.info("Input file mode - filtering existing dataframe")
            try:
                if self.fulldata is None:
                    self.fulldata = self.data
                # logger.info('Fulldata %d', len(self.fulldata))
                if len(querytext.strip()) > 0:
                    logger.info('Filter: %s', querytext)
                    nudf = dbutil.filter_dataframe(self.dbconnection, self.fulldata, querytext)
                    # logger.info('Data %d', len(self.data))
                    self.setData(nudf)
                else:
                    logger.info('No filter, showing full data')
                    self.setData(self.fulldata)
                # logger.info('Data %d', len(self.data))
                # logger.info('Fulldata %d', len(self.fulldata))
                self.statusfield.setText('')
            except Exception as e:
                logging.exception(e)
                error = str(e)
                if '\n' in error:
                    self.statusfield.setText('Issue with query:\n%s' % error)
                else:
                    self.statusfield.setText(f'Issue with query: {error}')
        else:
            self.statusfield.setText(f'Executing query: {querytext}')
            self.query_desc = querytext
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
            self.querybox.setEnabled(False)
            threadpool.start(worker)

    def setQueryFinished(self):
        # print('Query finished')
        self.querybox.setEnabled(True)
        self.query_ongoing = False

    def setQueryResult(self, exectime: float, querydf: pd.DataFrame):
        logger.debug('Clear results if empty: %s', self.clearresultsifempty)
        if querydf is not None and len(querydf) > 0:
            df = dbutil.add_relative_frequencies(self.dbconnection, querydf)
            self.statusfield.setText(f'Executing query: {self.query_desc} .. done: {len(querydf)} rows returned in {exectime:.1f} seconds')
            self.setData(df)
            # self.table.horizontalHeader().sectionClicked.connect(self.sortData)
            if self.mode == "inputfileprocess":
                self.mode = "inputfile"
                self.inputfilename = self.inputprocessfilename
                self.setDbNameField(self.inputfilename)
                # self.dbnamefield.setText(f'Database file: {self.dbconnection.dbfile}\nInput file: {self.inputfilename}')
            # self.table.horizontalHeader().sortIndicatorChanged.connect(self.sortData)
            # self.filterColumns()
            # self.resizeWidthToContents()
        else:
            self.statusfield.setText(f'Executing query {self.query_desc} .. done: no results in {exectime:.1f} seconds')
            if self.clearresultsifempty:
                df = pd.DataFrame()
                self.setData(df)
        self.clearresultsifempty = False

    def setQueryError(self, _text: str, error: str):
        if '\n' in error:
            self.statusfield.setText('Issue with query:\n%s' % error)
        else:
            self.statusfield.setText(f'Issue with query: {error}')

    def inputFileQuery(self):
        fileinput = QFileDialog()
        fileinput.setFileMode(QFileDialog.FileMode.ExistingFile)
        fileinput.setNameFilter("Text files (*.txt)")
        fileinput.setViewMode(QFileDialog.ViewMode.Detail)

        listtypes = ['lemma', 'form', 'nonword']

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
                if inputkeys[0] == 'nonword':
                    self.query_desc = ''
                    unworddf = dbutil.get_unword_bigrams(self.dbconnection, wordinput)
                    self.inputfilename = filename
                    self.setQueryResult(0, unworddf)
                    self.mode = "inputfile"
                else:
                    logger.info('Executing query from input file %s', filename)
                    self.statusfield.setText(f'Executing query from input file {filename}')
                    self.mode = "inputfileprocess"
                    self.inputprocessfilename = filename
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

        initialformat = self.config.getConfigValue('output.outformat',
                                                   'xlsx')
        initialfull = file_filters[0]

        # print(self.config.cfgdict)
        for outformat in file_filters:
            if initialformat in outformat:
                initialfull = outformat
                logger.debug('Choosing initial output format: %s', initialfull)
                break

        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            caption=caption,
            directory='',
            filter=';;'.join(file_filters),
            initialFilter=initialfull,
        )

        logger.info('Output from export file dialog: %s', filename)

        if filename:
            warnoverwrite = self.config.getConfigValue('output.warnoverwrite',
                                                       False)
            if warnoverwrite and exists(filename):
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
                        df.to_excel(excelwriter, sheet_name='LASTU words', index=False)
                        auto_adjust_xlsx_column_width(df, excelwriter, sheet_name='LASTU words', index=False)

    def copyToClip(self):
        logger.debug("Copy to clipboard called")
        df = self.data
        df.to_clipboard(index=False)

    def nullAction(self):
        logger.info("Action not implemented")

    # @dbutil.query_timing
    def setData(self, df: pd.DataFrame = None):
        # for f in inspect.stack():
        #    print('-', inspect.getframeinfo(f[0]))
        if df is None:
            df = pd.DataFrame()
        self.data = df
        # print(self.table.horizontalHeader().sortIndicatorSection())
        # print(self.table.horizontalHeader().sortIndicatorOrder())
        self.setSortedData()
        self.model = TableModel(self.data)

        # self.proxyModel = QSortFilterProxyModel()
        # self.proxyModel.setSourceModel(self.model)
        # self.table.setModel(self.proxyModel)
        self.table.setModel(self.model)

        self.hideRows()
        self.table.resizeColumnsToContents()
        self.filterColumns()
        # print(dir(self.table))
        # print(dir(self.model))
        # print(dir(self.table.horizontalHeader()))
        # self.resizeWidthToContents()

    def hideRows(self):
        df = self.data
        showrows = self.config.getConfigValue('query.showrows', 1000)
        if len(df) > showrows:
            # for f in inspect.stack():
            #    logger.debug(inspect.getframeinfo(f[0]))
            logger.info('Showing maximum %d rows of %d', showrows, len(df))
            # self.model = TableModel(df[:showrows])
            rowheader = self.table.verticalHeader()
            # rowcount = rowheader.count()
            for rowidx in range(showrows, len(df)):
                # print('Hiding row', rowidx, rowcount)
                rowheader.hideSection(rowidx)

    def setSortedData(self):
        # for f in inspect.stack():
        #     logger.debug(inspect.getframeinfo(f[0]))
        if self.data is not None:
            col = None
            colidx = self.table.horizontalHeader().sortIndicatorSection()
            # print(colidx)
            if colidx == -1:
                try:
                    columns = list(self.data.columns)
                    colidx = columns.index('frequency')
                    col = 'frequency'
                    direction = Qt.SortOrder.DescendingOrder
                    self.table.horizontalHeader().setSortIndicator(colidx, direction)
                except Exception as e:
                    logger.warning('Issue with sorting: %s', e)
            else:
                try:
                    col = list(self.data.columns)[colidx]
                    direction = self.table.horizontalHeader().sortIndicatorOrder()
                except IndexError as ie:
                    logger.debug("Couldn't get column %d from column list: %s", colidx, list(self.data.columns))

            if col:
                ascending = direction == Qt.SortOrder.AscendingOrder
                # print(col, colidx, ascending)
                logger.info('Sorting data based on column %d/%s, %s',
                            colidx, col, direction)
                df = self.data.sort_values(by=col, ascending=ascending)
                # print(df)
                self.data = df

    def sortData(self, _colidx, _direction=None):
        # print('Sorting', colidx, direction)
        self.setData(self.data)
#        self.setSortedData()
#        if self.data is not None:
#            col = list(self.data.columns)[colidx]
#            ascending = direction == Qt.SortOrder.AscendingOrder
#            # print(col, colidx, ascending)
#            df = self.data.sort_values(by=col, ascending=ascending)
#            self.setData(df)

        # self.table.sortByColumn(col, direction)
        # self.hideRows()
        # self.table.resizeColumnsToContents()
        # self.resizeWidthToContents()


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
    else:
        dbdir = dbdir.strip('"')
    if not dbf:
        dbf = 'lastudatabase.db'
    else:
        dbf = dbf.strip('"')

    dbpath = join(dbdir, dbf)
    logger.info("Trying database file in path %s", dbpath)
    if not exists(dbpath) or getsize(dbpath) == 0:
        dbpath = join('data', dbf)
        logger.info("File not found: %s; trying current directory for finding data file", dbpath)
        if not exists(dbpath) or getsize(dbpath) == 0:
            choosedb = selectDataBase()
            logger.info('Database chosen with file dialog: %s', choosedb)
            if not choosedb:
                logger.error("No such file: %s", dbpath)
                raise FileNotFoundError(dbpath)
            dbpath = choosedb

    return dbpath


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='lastu',
                                     description='lastu UI')
    parser.add_argument('-e', '--exit',
                        action='store_true',
                        help='Exit from GUI')
    args = parser.parse_args()
    if args.exit:
        print('Exiting from GUI')
        sys.exit()

    logger.info('Launching application at %s', datetime.now())
    inifile = 'lastu.ini'
    appconfig, currdir = uiutil.get_config(inifile)
    # print(appconfig, currworkdir)
    if not appconfig:
        logger.warning("Configuration file '%s' not found", inifile)
        # FIXME: error window if ini file not found
    configfile = ConfigFile(appconfig)
    app = QApplication(sys.argv)
    dbfile = getDataBaseFile(appconfig, currdir)

    threadpool = QThreadPool()
    logger.debug("Multithreading with maximum %d threads",
                 threadpool.maxThreadCount())

    logger.debug('Got final database file: %s', dbfile)

    try:
        logger.info("Connecting to %s...", dbfile)
        dbconn = dbutil.DatabaseConnection(dbfile)
        if (rowlimit := configfile.getConfigValue('query.fetchrows')) is not None:
            logger.debug('Setting row limit to %d', rowlimit)
            dbconn.rowlimit(rowlimit)
    except Exception as e:
        logger.error("Couldn't connect to %s: %s", dbfile, e)

    w = MainWindow(dbconn, appconfig=appconfig)

    # initial query
    # finquery = "form = 'silmäsi' and frequency > 10"
    iniquery = "freq > 100"
    query = configfile.getConfigValue('query.defaultquery', iniquery)
    w.querybox.setText(query)
    w.textQuery()
    w.show()

    app.exec()
