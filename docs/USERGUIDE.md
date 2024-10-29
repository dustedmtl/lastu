# LASTU User Guide

## Background

LASTU: Lexical Application for STimulus Unearthing is a program for searching for stimulus words for psycholinguistic research. It has mainly been developed for Finnish, but databases can be created for other languages as well.

### Citations

Citation when using our software:

Sami Itkonen, Tuomo Häikiö, Seppo Vainio, and Minna Lehtonen. 2024. LASTU: A psycholinguistic search tool for Finnish lexical stimuli. Behavior Research Methods. https://doi.org/10.3758/s13428-024-02347-x

If you also use our Finnish database(s) derived from the Finnish Internet Parsebank, your should also cite its creators:

Juhani Luotolahti, Jenna Kanerva, Veronika Laippala, Sampo Pyysalo, and Filip Ginter. 2015. Towards Universal Web Parsebanks. In Proceedings of the Third International Conference on Dependency Linguistics (Depling 2015), pages 211-220, Uppsala, Sweden. Uppsala University, Uppsala, Sweden.
https://aclanthology.org/W15-2124/

## Download and installation instructions

The software has two required components:
 - the application itself (including the optional `lastu.ini` configuration file)
 - a database, which is a file in the form of SQLite3 database

The software and databases are located at OSF: https://osf.io/j8v6b/.

The application can be downloaded at https://osf.io/j8v6b/files/osfstorage:
 - Under `software`, download the appropriate package (`.zip` for Windows, `.dmg` for macOS).
 - Open (extract) the package and drag the application (`.exe` for Windows, `.app` for macOS) to your desired location.
   - If this is your first time using the software, also drag the `lastu.ini` file to the same location.
   - Otherwise you can keep using the old configuration file.

For databases, go to https://osf.io/7hrbv/files/osfstorage. A database archive contains the database as well as tables exported from the database in CSV format.
 - Download the package (in `.zip` format), and extract it to a suitable location.

Your operating system may issue a warning when opening the application for the first time. How to get around this:
 - macOS: https://support.apple.com/en-gb/guide/mac-help/mchleab3a043/mac
 - Windows: TBD

### Init file and database file

The main function of the init file is to tell the application where the database file should be found. For a more general description of the options, please see [init file configuration](#init-file-configuration).

The init file itself is looked for in two locations:
 - The same directory where the application is located in
 - The user's home directory
   - macOS: `/Users/<username>/lastu.ini`
   - Windows: `C:\Users\<username>\lastu.ini`

If the init file is not found in either location, the database filename will default to `lastudatabase.db` and
the application will try to locate it from the `data` subdirectory. If this file isn't found either, the application will prompt the user to locate a database file to open.


## User interface

The user interface consists of one or more windows, containing a query field, results table and various information fields. The application is used by typing a query into the query field and the clicking the `Query` button (or simply pressing the `Enter` on the keyboard). A variety of functions are also available from the menu, which include opening a different database, exporting and copying information to output file or clipboard and choosing which columns to show.

The results are disambiguated based on the lemma, surface form, part-of-speech (i.e. word class) and the set of core features (which, among other things, include case, person, mood, tense, clitics and derivations). This means that there usually are multiple rows for each lemma/form/pos triplet.

The table shows information in four difference categories: lemma information, surface form information, gram frequencies and features. The lemma and surface form fields include both string and numeric fields.

For performance reasons, by default the application fetches 10000 top results from the database (ordered by frequency) and shows the top 1000 results (based on whatever sorting criteria the user has, the default is frequency). These values can be changed in the [configuration file](#init-file-configuration), if necessary (e.g. if the user finds the application too slow; see also the [chapter on limitations](#limitations). The information field under the query field shows the number of rows fetched from the database. If the number is less than 10000, this is the amount of actual rows in the database; otherwise the total number of matching rows is unknown.

The results table is sortable by all available fields.

The application generates debug logs to the file `lastu_log.txt` and records executed searches to the file `lastu_history.txt`. These files will by default be located in the same directory as the application itself. However, if the directory isn't writable (for whatever reason), the files are written to the user's home directory.

### Basic queries

The queries consist of one or more parts separated by the keyword `and`. The format of the parts depend on the type of property being queried. The three types of properties are: string, numeric and boolean.

Examples for string queries:

| Query | Explanation |
| --- | --- |
| `form = autossa` | surface form |
|`case != ine` | (noun) case is not inessive |
| `lemma = voi and pos = noun` | results for the noun `voi` |
| `clitic not in kin,kaan` | the surface form does not contain the clitics `kin` or `kaan` |
| `start = aut` | surface form starts with `aut` |
| `end in ssa,ssä`| surface form ends with `ssa` or `ssä` |

Examples for numeric queries:

| Query | Explanation |
| --- | --- |
| `len > 10` | surface form is longer than 10 characters |
| `freq > 100` | the frequency of the surface form is higher than 100 |

For boolean properties, the only choice is `compound`:

| Query | Explanation |
| --- | --- |
| `start = auto and compound` | compounds that start with `auto` |
| `pos = adj and not compound` | non-compound adjective 

Different types of properties can also be combined:

| Query |
| --- |
| `start = auto and compound and len > 10` |

For a full list of properties to query, the format of query parts and extended examples, please see [query keys](#query-keys), [query formatting](#query-formatting) and [extended examples](#extended-examples).

### Basic menu functions

The keyboard shortcuts described here are applicable for the Windows platforms. For macOS, substitute `Cmd` for `Ctrl`.

A new window can be created with `Ctrl-N`, which copies the query and results from the currently active window, or `Shift-Ctrl-N`, which opens a new empty window. Queries from an wordlist file can be done with `Ctrl-I`. A different database can be opened with `Ctrl-D`.

There are three ways to export/copy information:
 1. `Ctrl-S` exports the results to file (csv/tsv/xlsx); default output format is specified in the configuration file.
 2. `Ctrl-E` copies the results to the clipboard.
 3. `Ctrl-C` copies the individually selected rows, columns or cells to the clipboard.

With `Ctrl-C`, only cells that have been selected will be copied (i.e. hidden cells are excluded). With `Ctrl-E`, all results are copied, including rows and columns that are hidden from the result window.

For more information and other shortcuts, please see the [menu functions](#menu-functions).

### Modes: database versus wordlist

The two modes of operation are free search mode and wordlist mode. The free search mode is the default. In this mode, any queries are searched directly from the database whenever the they are executed (when the `Query` button or `Enter` key is pressed).

In the wordlist mode, the user can upload a ready list of words or nonwords from a .txt file to get their properties. In this mode only the initial result list is fetched from the database. Any queries that are made afterward are made against this set of results.

The queries work identically in both modes. The only exception is that for the wordlist mode, where there is an additional key `top`. When this key is used in the query, only the top results (based on frequency) for each lemma/form/pos/feats quartet are shown (e.g. `top = 2` shows top 2 results).

To get back to the free search mode from the wordlist mode, the user must either open a new empty window with `Shift-Ctrl-N` or a different database with `Ctrl-D`.

In the wordlist mode, there is an additional column `order`, which shows the order (row) of the input words in the wordlist input file.

## Limitations

The main limitations of the program relate to performance. Some queries may be slow to execute in the database. The user interface may also be slow to update when fetching data from the database or sorting it, depending on the resources of the computer. To alleviate these issues, the user may consider the following remedies:
 - Consider using a smaller database.
 - Choose smaller values for the `fetchrows` and `showrows` configuration variables (see [init file configuration](#init-file-configuration)).


## Advanced information

### Query formatting

A query consists of one or more parts separated by the keyword `and`:
 - `PART`
 - `PART` and `PART`
 - `PART` and `PART` and `PART` ...

The query parts generally follow the form `KEY OPERATOR VALUE`.
 - `KEY` is a string to query (`form`)
 - `OPERATOR` is a mathematical or string comparison (e.g. `=`, `>`) operator or set operator `IN`
 - `VALUE` is the value being searched

Exceptions to these are boolean queries and negative (`NOT`) queries for certain string operators and the set operator.

The allowed operators vary depending on whether the key queries a string, numeric or boolean property.
 - String operators are equality (`=`), inequality (`!=`) and set operators (`IN` and `NOT IN`).
 - Numeric operators are equality (`=`), inequality (`!=`), greater than (`>`), smaller than (`<`), greater than or equal (`>=`) and smaller than or equal (`<=`).
 - Boolean queries have a special format and there are no operators.

For strings, the set operator `IN` allows the user to query for accepted (or not accepted) values:
 - `KEY` IN `A,B`
   - The property `KEY` must contain value `A` or `B`
 - `KEY` NOT IN `A,B`
   - The complementary set

The only supported boolean property is `compound`:
 - `compound`
   - search for compound lemmas
 - `not compound`
   - searching for lemmas that are not compounds

All inputs (keys, operators, values) are lowercase regardless of the format of the underlying data.

The `LIKE` operator can be used for wildcard searches if the operators `start`, `middle` and `end` do not suffice.
This operator allows the querying of any string property using a wildcard syntax, where the wildcard is `%`.
The use of this operator is generally not recommended as it is slower than the alternatives.

Examples:
 - `lemma like voi%`
   - lemma starts with string `voi`
 - `form like %ta%`
   - form contains the substring `ta`

### Query keys

#### String properties

The below tables show the query keys and operators for strings.

| Key | Explanation |
| --- | --- |
| `lemma` | Lemma |
| `form` | Surface form |
| `pos` | Word class (i.e., part-of-speech) |
| `number` | Number |
| `person` | Person |
| `posspers` | Possessive suffix person |
| `possnum` | Possessive suffix number |
| `mood` | Verb mood |
| `tense` | Verb tense |
| `verbform` | Verb form |
| `nouncase` | Case |
| `derivation` | Derivation |
| `clitic` | Clitic |

| Operator | Explanation | Example |
| --- | --- | --- |
| `=` | Equal | `form = kuusi` |
| `!=` | Unequal | `pos != noun` |
| `in` | In a set | `case in nom,gen` |
| `not in` | Not in a set | `case not in nom,gen` |
| `like` | SQL `LIKE` operator | `form like auto%` |

Additional query keys for the surface form are shown below.

| Key | Explanation | Example |
| --- | --- | --- |
| `start` | Form begins with string | `start = au` |
| `middle` | Form contains string in the middle | `middle in ta,sa` |
| `end` | Form ends with string | `end not in ssa,ssä`|

#### Numeric properties

For numbers, the keys and operators are shown below.

| Key | Explanation |
| --- | --- |
| `lemmafrequency` | Lemma frequency |
| `frequency` | Surface form frequency |
| `lemmalen` | Lemma length |
| `len` | Surface form length |
| `hood` | Orthographic neighbourhood |
| `amblemma` | Lemma ambiguity percentage |
| `ambform` | Surface form ambiguity percentage |
| `initgramfreq` | Initial trigram frequency |
| `fingramfreq` | Final trigram frequency |
| `bigramfreq` | Bigram frequency |

| Operator | Explanation | Example |
| --- | --- | --- |
| `=` | Equal | `len = 8` |
| `!=` | Unequal | `person != 3` |
| `>` | Greater than | `freq > 10000` |
| `>=` | Greater than ow equal | `freq >= 10000` |
| `<` | Lower than | `ambform < 0.99` |
| `<=` | Lower than or equal | `len <= 10` |

For all frequency fields there is a corresponding relative frequency field (prepended with `rel`, e.g. `rellemmafreq`). The value of this field is frequency per one million tokens.

#### Boolean properties

There is one boolean key for compound words.

| Key | Explanation |
| --- | --- |
| `compound` | Compound word |
| `not compound` | Not compound word |

### Extended examples

Search for all nouns and adjectives in inessive, elative or illative with frequency between 100 and 200, length between 5 to 12 characters (inclusive), omitting compounds:
 - `pos in noun,adj and case in ine,ela,ill and freq > 100 and freq < 200 and len >= 5 and len <= 20 and not compound`

Search for all verbs in base form ending with `da` or `dä` with frequency above `x` and below `y`:
 - `verbform = Inf and end in da,dä and freq > x and freq < y`

Search for nouns with `kse` in the body in inessive case:
 - `pos = noun and middle = kse and case = ine`

### Menu functions

#### Opening and closing windows

The user interface consists of one or more windows. Shortcuts for window management:
  - `Ctrl-N` - new window
    - Copies the query and results from the currently active window
  - `Shift-Ctrl-N` - new empty window
  - `Ctrl-W` - close currently active window
  - `Ctrl-Q` - quit application

#### Input and output

Input and output commands:
  - `Ctrl-I` - query from wordlist
    - The wordlist file may contain empty lines, comment lines (starting with `#`) and content lines
      - Before the first content line, there must be a type identified line
        - form: "# type=`querytype`"
        - `querytype` can be `lemma`, `form` or `nonword`
        - The specific category is searched for the strings in the content lines
      - The file may be encoded as UTF-8 or ISO-Latin-1 / ISO-Latin-15
  - `Ctrl-S` - export to file (csv/tsv/xlsx)
  - `Ctrl-E` - copy to clipboard (all results)
  - `Ctrl-C` - copy to clipboard (selected cells/rows/columns)
  - `Ctrl-D` - open new database

#### Hiding and showing columns

The data menu lists the various column hide/show options:
 - `Ctrl-1` to `Ctrl-3`: showing frequency columns
 - `Ctrl-4`: showing columns (morphological features) that can be hidden
 - `Ctrl-5` to `Ctrl-8`: showing categories

### Init file configuration

The most important configuration options:
 - general
   - autoresize
     - set window width automatically to the width of the columns (True/False)
   - opendbwithnewwindow
     - When opening new database, open new window (True/False)
- input
   - datadir and database (paths to files/directories)
 - output
   - outformat
     - xlsx, csv, tsv
 - query
   - fetchrows
     - the maximum number of rows to fetch from the database (integer, default 10000)
   - showrows
     - the maximum number of rows to show in the UI (integer, default 1000)
 - style
   - fontsize (integer, default 11)


