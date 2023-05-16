# WordMill 2 User Guide

## Background

WordMill 2 is a program for generating stimulus words for psycholinguistic research. It has mainly been developed for Finnish, but databases can be created for other languages as well.

## Download and installation instructions

The software has two necessary components:
 - the application itself (include the optional `wm2.ini` configuration file)
 - a database, which is a file in the form of SQLite3 database

The software and databases are located at OSF https://osf.io/j8v6b/.

You can download the application on OSF at https://osf.io/j8v6b/files/osfstorage:
 - Under `software`, download the appropriate package (`.zip` for Windows, `.dmg` for macOS).
 - Open the package and drag the application (`.exe` for Windows, `.app` for macOS) to your desired location.
   - If this is your first time using the software, also drag the `wm2.ini` file to the same location.
   - Otherwise you can keep using the old configuration file.

For databases, go to https://osf.io/7hrbv/files/osfstorage.

### Init file and database file

The main function of the init file is to tell the application what the database file is and where it should be found. For a more general description of the options, please see [init file configuration](#init-file-configuration).

The init file itself is looked for from two locations:
 - The same directory where the application is located in
 - The user's home directory
   - macOS: `/Users/<username>/wm2.ini`
   - Windows: `C:\Users\<username>\wm2.ini`

If the init file is not found, the database filename will default to `wm2database.db` and
the application will try to locate it from the `data` subdirectory. If this file isn't found either, the application will prompt the user to locate a file to open.


## User interface

The UI consists of one or more windows, with a query field, results table and various information fields. The application is used by entering a query into the query field and the pressing the `Query` button (or simply pressing the `Enter` on the keyboard). A variety of functions are also available from the menu, which include opening a different database, exporting and copying information to output file or clipboard and choosing which columns to show.

The results are disambiguated based on the lemma, surface form, pos (part-of-speech, i.e. word class) and the set of core features (which, among other things, include case, person, tense, clitics and derivations). This means that there usually are multiple rows for each lemma/form/pos triplet.

The table shows information in four difference categories: lemma information, surface form information, gram frequencies and features. The lemma and surface form fields include both string and numeric fields.

For performance reasons, the application fetches 10000 top results from the database (based on frequency) and shows top 1000 results (based on whatever sorting criteria the user has). These values can be changed in the [configuration file](#init-file-configuration), if necessary. The information field under the query field shows the number of rows fetched from the database. If the number is less than 10000, this is the amount of actual rows in the database; otherwise the total number of matching rows is unknown.

The results table is sortable by all available fields.

The application generates debug logs to the file `wm2log.txt` and logs executed searches to the file `wm2history.txt`. These files will by default be located in the same directory as the application itself. However, if the directory isn't writable (for whatever reason), the files are written to the user's home directory.

### Basic queries

The queries consist of one or more parts separated by the keyword `and`. The format of the parts depend on the type of property being queried. The three types of properties are: string, numeric and boolean.

Examples for string queries:
 - `form = autossa`
   - surface form
 - `case != ine`
   - (noun) case is not inessive
 - `lemma = voi and pos = noun`
   - results for the noun `voi`
 - `clitic not in kin,kaan`
   - the surface form does not contain the clitics `kin` or `kaan`
 - `start = aut`
   - surface form starts with `aut`
 - `end in ssa,ssä`
   - surface form ends with `ssa` or `ssä`

Examples of numeric queries:
 - `len > 10`
   - surface form is longer than 10 characters
 - `freq > 100`
   - the frequency of the item is higher than 100

For boolean properties, the only choice is `compound`:
 - `start = auto and compound`
   - compounds that start with `auto`
 - `pos = adj and not compound`
   - non-compound adjective

Different types of properties can also be combined:
 - `start = auto and compound and len > 10`

For a full list of properties to query and the format of query parts, please see [query keys](#query-keys) and [query formatting](#query-formatting).

### Basic menu functions

The functions below use the Windows platforms keys. For macOS, substitute `Cmd` for `Ctrl`.

A new window can be created with `Ctrl-N`, which copies the query and results from the currently active window, or `Shift-Ctrl-N`, which opens a new empty window. Queries from an wordlist file can be done with `Ctrl-I`. A different database can be opened with `Ctrl-D`.

There are three ways to export/copy information:
 1. `Ctrl-S` exports the result to file (csv/tsv/xlsx).
 2. `Ctrl-E` copies the results to the clipboard.
 3. `Ctrl-C` allows the user to individually select rows, columns or cells and copy them to clipboard.

With `Ctrl-C`, only cells that have been selected will be copied (i.e. hidden cells are excluded). With `Ctrl-E`, all results are copied, including rows and columns that are hidden from the result window.

For more information and other shortcuts, please see the [menu functions](#menu-functions).

### Modes: database versus wordlist

The two modes of operation are free search mode and wordlist mode. The free search mode is the default. In this mode, any queries are searched directly from the database whenever the they are executed (when the `Query` button or `Enter` key is pressed). In contrast, in the wordlist mode only the initial result list is fetched from the database. Any queries that are made afterward are made against this set of results.

The queries work the same for both modes. For wordlist mode, there is an additional key `top`. When this key is used in the query, only the top results (based on frequency) for each lemma/form/pos/feats quartet are shown.

To get back to the free search mode from the wordlist mode, the user must either open a new empty window with `Shift-Ctrl-N` or a different database with `Ctrl-D`.

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
 - `OPERATOR` is a mathematical or string comparison (e.g. `=`, `>`) or set operator `IN`
 - `VALUE` is the value being searched

Exceptions to these are boolean queries and negative (`NOT`) queries for certain string operators.

The allowed operators vary depending on whether the key queries a string, numeric or boolean property.
 - String operators are equality (`=`), inequality (`!=`) and set operators (`IN` and `NOT IN`).
 - Numeric operators are equality (`=`), inequality (`!=`), greater than (`>`), smaller than (`<`), greater than or equal (`>=`) and smaller than or equal (`<=`).
 - Boolean queries have a special format and there are no operators.

For strings, the set operator `IN`allows the user to query for accepted (or not accepted) values:
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
   - note the difference to the operator `middle`: this search does not exclude strings that start (or end) with `ta`

### Query keys

#### String properties

The basic string properties that can be queried are:
 - `lemma`
 - `form` (surface form)
 - `pos` (part-of-speech, i.e. word class)

The wildcard queries that operate on surface form:
 - `start`
   - form begins with string
 - `middle`
   - form contains string, but does not start or end with it
 - `end`
   - form ends with string

Noun morphological features:
 - `nouncase` (short: `case`)
 - `nnumber`
   - noun number

Verb morphological features:
 - `number`
 - `tense`
 - `person`
 - `verbform`

Other morphological features
 - `posspers`
   - possessive suffix person
 - `possnum`
   - possessive suffix person number
 - `derivation`
   - derivational suffixes
 - `clitic`
   - clitics

#### Numeric properties

For lemmas:
 - `lemmalen`
   - lemma length
 - `lemmafreq`
   - lemma frequency (for the specific part-of-speech, i.e. word class)
 - `amblemma`
   - measure of lemma ambiguity

For surface forms:
 - `len`
   - form length
 - `frequency` (short: freq)
   - form frequency
 - `hood`
   - orthographic neighbourhood
 - `ambform` 
   - measure of surface form ambiguity
 - `initgramfreq`
   - initial trigram frequency
 - `fingramfreq`
   - final trigram frequency
 - `bigramfreq`
   - bigram frequency

For all frequency fields there is a corresponding relative frequency field (prepended with `rel`, e.g. `rellemmafreq`). The value of this field is frequency per one million tokens, except for `relbigramfreq`, which is frequency per one thousand tokens.

#### Boolean properties:
 - `compound`
   - whether the word form is a compound

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
      - The file may be encoded as UTF-8 or ISO-Latin-1
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


