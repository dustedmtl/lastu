"""Testing sqlite database connection."""

# pylint: disable=invalid-name, redefined-outer-name

import sys
import os
import os.path
import pytest
from pytest_check import check
import pandas as pd

currdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currdir)
sys.path.append(parentdir)

from lib import dbutil, uiutil


@pytest.fixture(scope="session")
def inifile():
    """Read init file."""
    init, _ = uiutil.get_config('wm2.ini')
    return init


@pytest.fixture(scope="session")
def datafile_ini(inifile):
    """Get datafile path."""
    if (datadir := uiutil.get_configvar(inifile, 'input', 'datadir')) is None:
        datadir = '.'
    if (dbfile := uiutil.get_configvar(inifile, 'input', 'database')) is None:
        dbfile = "wm2database.db"
    return os.path.join(datadir, dbfile)


@pytest.fixture(scope="session")
def datafile():
    """Get fixed datafile."""
    datadir = "tests"
    dbfile = "fi_gutenberg_70M_100.db"
    return os.path.join(datadir, dbfile)


@pytest.fixture(scope="session")
def dbc(datafile):
    """Get connection to database."""
    print(f'Calling dbc with {datafile}')
    conn = dbutil.DatabaseConnection(datafile)
    return conn


@pytest.fixture(scope="session")
def df(dbc):
    """Select from wordfreqs table, return as dataframe."""
    frame = dbutil.adhoc_query(dbc.get_connection(),
                               "select * from wordfreqs limit 10",
                               todf=True)
    return frame


def test_df(df):
    """Check that a dataframe is returned."""
    print('Must be a dataframe')
    assert isinstance(df, pd.DataFrame)


def test_basic(dbc):
    """Check that a basic query is done properly."""
    q1 = "form = voi and ambform < 0.9"
    q2 = "form = voi and ambform > 0.9"
    df1, _, _ = dbutil.get_frequency_dataframe(dbc, query=q1,
                                               grams=True,
                                               lemmas=True)
    df2, _, _ = dbutil.get_frequency_dataframe(dbc, query=q2,
                                               grams=True,
                                               lemmas=True)
    print('Must be a dataframe')
    check.is_true(isinstance(df1, pd.DataFrame))
    print('Must be a dataframe')
    check.is_true(isinstance(df2, pd.DataFrame))
    # assert isinstance(df2, pd.DataFrame)
    print(f'{q1}: Must not have rows with ambform > 0.9')
    check.equal(len(df1[df1.ambform > 0.9]), 0)
    # assert len(df1[df1.ambform > 0.9]) == 0
    print(f'{q2}: Must not have rows with ambform < 0.9')
    check.equal(len(df2[df2.ambform < 0.9]), 0)
    # assert len(df2[df2.ambform < 0.9]) == 0
    print(f"{q2}: All forms must be 'voi'")
    check.equal(len(df2[df2.form != 'voi']), 0)
    # assert len(df2[df2.form != 'voi']) == 0


def test_clitic(dbc):
    """Check that clitics are queried properly."""
    q1 = "clitic != _"
    q2 = "clitic = _"
    q3 = "clitic in _"
    q4 = "clitic not in _"
    q5 = "clitic not in Kin,Kaan"
    q6 = "clitic != Kin"

    df1, _, _ = dbutil.get_frequency_dataframe(dbc, query=q1,
                                               grams=True,
                                               lemmas=True)
    df2, _, _ = dbutil.get_frequency_dataframe(dbc, query=q2,
                                               grams=True,
                                               lemmas=True)
    df3, _, _ = dbutil.get_frequency_dataframe(dbc, query=q3,
                                               grams=True,
                                               lemmas=True)
    df4, _, _ = dbutil.get_frequency_dataframe(dbc, query=q4,
                                               grams=True,
                                               lemmas=True)
    df5, _, _ = dbutil.get_frequency_dataframe(dbc, query=q5,
                                               grams=True,
                                               lemmas=True)
    df6, _, _ = dbutil.get_frequency_dataframe(dbc, query=q6,
                                               grams=True,
                                               lemmas=True)
    print(f'{q1}: result must not contain _')
    check.equal(len(df1[df1.clitic == '_']), 0)
    # assert len(df1[df1.clitic == '_']) == 0
    print(f'{q2}: result must not contain results other than _')
    check.equal(len(df2[df2.clitic != '_']), 0)
    print(f'{q2}: have results')
    check.greater(len(df2[df2.clitic == '_']), 0)
    # assert len(df2[df2.clitic != '_']) == 0
    print(f'{q3}: result must not contain results other than _')
    check.equal(len(df3[df3.clitic != '_']), 0)
    print(f'{q3}: have results')
    check.greater(len(df3[df3.clitic == '_']), 0)
    # assert len(df3[df3.clitic != '_']) == 0
    print(f'{q4}: result must not contain _')
    check.equal(len(df4[df4.clitic == '_']), 0)
    # assert len(df4[df4.clitic == '_']) == 0
    print(f'{q5}: result must not contain _')
    check.greater(len(df5[df5.clitic == '_']), 0)
    # assert len(df5[df5.clitic == '_']) > 0
    print(f'{q6}: result must not contain _')
    check.greater(len(df6[df6.clitic == '_']), 0)
    # assert len(df6[df6.clitic == '_']) > 0


def test_compound(dbc):
    """Check that compounds queried properly."""
    # q1 = "lemma = autotalli"
    # q2 = "lemma = autotalli and compound"
    q1 = "lemma = valtakunta"
    q2 = "lemma = valtakunta and compound"

    df1, _, _ = dbutil.get_frequency_dataframe(dbc, query=q1,
                                               grams=True,
                                               lemmas=True)
    df2, _, _ = dbutil.get_frequency_dataframe(dbc, query=q2,
                                               grams=True,
                                               lemmas=True)

    print(f'{q1}: some lemmas should contain #')
    check.greater(len(df1[df1.lemma.str.contains('#')]), 0)
    # assert len(df1[df1.lemma.str.contains('#')]) > 0
    print(f'{q2}: all lemmas must contain #')
    check.equal(len(df2[~df2.lemma.str.contains('#')]), 0)
    # assert len(df2[~df2.lemma.str.contains('#')]) == 0


def test_form(dbc):
    """Check that form wildcards queried properly."""
    # q1 = "form like auto%"
    q2 = "start = auto"
    q3 = "end in ssa,ssä"
    q4 = "middle = la"
    q5 = "start = la and middle = la"
    q6 = "start = la and middle != la"
    q7 = "start = la"

    # df1, _, _ = dbutil.get_frequency_dataframe(dbc, query=q1,
    #                                            grams=True,
    #                                            lemmas=True)
    df2, _, _ = dbutil.get_frequency_dataframe(dbc, query=q2,
                                               grams=True,
                                               lemmas=True)
    df3, _, _ = dbutil.get_frequency_dataframe(dbc, query=q3,
                                               grams=True,
                                               lemmas=True)
    df4, _, _ = dbutil.get_frequency_dataframe(dbc, query=q4,
                                               grams=True,
                                               lemmas=True)
    df5, _, _ = dbutil.get_frequency_dataframe(dbc, query=q5,
                                               grams=True,
                                               lemmas=True)
    df6, _, _ = dbutil.get_frequency_dataframe(dbc, query=q6,
                                               grams=True,
                                               lemmas=True)
    df7, _, _ = dbutil.get_frequency_dataframe(dbc, query=q7,
                                               grams=True,
                                               lemmas=True)

    # print(f"{q1}: all forms must start with 'auto'")
    # assert len(df1[~df1.form.str.contains('^auto')]) == 0
    print(f"{q2}: all forms must start with 'auto'")
    check.equal(len(df2[~df2.form.str.contains('^auto')]), 0)
    # assert len(df2[~df2.form.str.contains('^auto')]) == 0
    print(f"{q3}: all forms must end with 'ssa' or 'ssä'")
    check.equal(len(df3[(df3.form.str.contains('ssa$')) | (df3.form.str.contains('ssä$'))]), len(df3))
    # check.equal(len(df3[(df3.form.str.contains('ssa$')) | (df3.form.str.contains('ssä$'))]), 1)
    # assert len(df3[(df3.form.str.contains('ssa$')) | (df3.form.str.contains('ssä$'))]) == len(df3)
    print(f"{q4}: all forms must contain 'la' in the middle. They may also start or end with it")
    check.equal(len(df4[df4.form.str.contains(r'^.+la.+$')]), len(df4))
    print(f"{q5}: all forms must start with and contain 'la' in the middle. They may also end with it")
    check.equal(len(df5[df5.form.str.contains(r'^.+la.+$')]), len(df5))
    print(f"{q6}: all forms must start with and not contain 'la' in the middle. They may also end with it")
    check.equal(len(df6[~df6.form.str.contains(r'^.+la.+$')]), len(df6))
    print(f"{q7}: middle queries must add up to a full set")
    check.equal(len(df7), len(df5)+len(df6))


def test_error(dbc):
    """Test an error query."""
    q1 = "nouncase in Ill,Gen and pos in PROPN,NOUN and foo = 0 and len >  a and naat compound and len ~= 10 and len<10"
    try:
        print('Query must produce an exception')
        _df1, _, _ = dbutil.get_frequency_dataframe(dbc, query=q1,
                                                    grams=True,
                                                    lemmas=True)
        assert False
    except ValueError as ve:
        print(ve)
        for s in (["'foo' not ok", "'a' is not a number", "'naat compound'",
                   "'len' not ok: '~='", "'len<10'"]):
            check.is_true(s in str(ve))


def test_wordlist(dbc):
    """Text wordlist and filtered queries."""
    filename = 'samples/lemmalist.txt'
    wordinput = dbutil.get_wordinput(filename)
    lemmadf, _, _ = dbutil.get_frequency_dataframe(dbc, query=wordinput, grams=True, lemmas=True)
    check.greater(len(lemmadf), 0)
    ffiltered = dbutil.filter_dataframe(dbc, lemmadf, "form = voi and frequency > 10 and amblemma < 0.9")
    check.greater(len(ffiltered), 0)
    # The order column is in the dataframe.
    columns = ffiltered.columns
    check.is_true('order' in columns)
