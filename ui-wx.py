
# pylint: disable=invalid-name
import os
import sys

import wx
import wx.grid
from lib import dbutil
EVEN_ROW_COLOUR = '#CCE6FF'
GRID_LINE_COLOUR = '#ccc'

basedir1 = os.path.dirname(__file__)
basedir2 = os.path.dirname(os.path.realpath(__file__))
basedir3 = os.path.dirname(sys.argv[0])
basedir4 = os.path.dirname(sys.executable)


class DataTable(wx.grid.GridTableBase):
    def __init__(self, data=None):
        wx.grid.GridTableBase.__init__(self)
        self.headerRows = 1
        self.data = data

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.data.columns) + 1

    def GetValue(self, row, col):
        if col == 0:
            return self.data.index[row]
        return self.data.iloc[row, col-1]

    def GetColLabelValue(self, col):
        if col == 0:
            return 'Index' if self.data.index.name is None else self.data.index.name
        return self.data.columns[col-1]

    def GetTypeName(self, row, col):
        return wx.grid.GRID_VALUE_STRING

    def GetAttr(self, row, col, prop):
        attr = wx.grid.GridCellAttr()
        if row % 2 == 1:
            attr.SetBackgroundColour(EVEN_ROW_COLOUR)
        return attr


class AppFrame(wx.Frame):
    """Application frame."""

    def __init__(self, df=None):
        wx.Frame.__init__(self, None, wx.ID_ANY, "Default title", size=(1200, 500))
        self._baseGui(df)
        self.Layout()
        self.Show()

    def _baseGui(self, df=None):

        # text_box = wx.BoxSizer(wx.VERTICAL) # Vertical orientation
        # self.textbox = wx.TextCtrl(self, style=wx.TE_LEFT)
        # text_box.Add(self.textbox, flag=wx.EXPAND | wx.TOP | wx.BOTTOM, border=10)

        # textgrid = wx.GridSizer(5, 5, 50, 50) # Rows, columns, vertical gap, horizontal gap
        # text_box.Add(textgrid, proportion=2, flag=wx.EXPAND)
        # self.SetSizer(text_box)

        dftable = DataTable(data=df)
        grid = wx.grid.Grid(self, -1)
        grid.SetTable(dftable, takeOwnership=True)
        grid.AutoSizeColumns()
        grid.AutoSize()

        # gridsizer = wx.BoxSizer(wx.HORIZONTAL)
        # gridsizer.Add(grid, 0, wx.EXPAND)

    def exit(self, _event):
        self.Destroy()


if __name__ == "__main__":

    print(f'basedir1: {basedir1}')
    print(f'basedir2: {basedir2}')
    print(f'basedir3: {basedir3}')
    print(f'basedir4: {basedir4}')

    if len(basedir3) > 0:
        print(f'Using basedir3: {basedir3}')
        basedir = basedir3
    else:
        print('Using basedir .')
        basedir = '.'

    dbfile = f'{basedir}/data/gutenberg_c1.db'
    print(f'dbfile: {dbfile}')
    sqlcon = dbutil.get_connection(dbfile)
    # query = "pos = 'NOUN' and form like 'silmäsi' and frequency > 10"
    # query = "pos = 'NOUN' and frequency > 10 and len > 6 and bigramfreq > 6000000"
    query = "pos = 'NOUN' and frequency > 10 and len > 6"

    df = dbutil.get_frequency_dataframe(sqlcon, query=query)

    app = wx.App()
    appframe = AppFrame(df)
    # appframe.Show()
    app.MainLoop()
