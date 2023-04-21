# User Guide

## Background

Background: TBD.

## Download instructions

There are two components necessary for the software:
 - the application itself (include the optional `wm2.ini` configuration file)
 - a database, which is a file in the form of SQLite3 database

You can download the application and database(s) here: TBD.

## Init file and database file

The main function of the init file is to tell the application what the database file is and where it should be found. For a more general description of the options, please see [Init file configuration](#init-file-configuration).

The init file itself is looked for from two locations:
 - The same directory where the application is located in
 - The user's home directory
   - Mac: `/Users/<username>/wm2.ini`
   - Windows: `C:\Users\<username>\wm2.ini`

If the init file is not found, the database filename will default to `wm2database.db` and
the application will try to locate it from the `data` subdirectory.

## User interface

The UI consists of one or more windows, with a query field, results table and various information fields. The application is used by entering a query into the query field and the pressing the `Query` button (or simply pressing the `Enter` on the keyboard). A variety of functions are also available from the menu, which include opening a different database, exporting and copying information to output file or clipboard and choosing which columns to show.

The results table is sortable by all available fields.

The application generates debug logs to the file `wm2log.txt` and logs executed searches to the file `wm2history.txt`. These files will by default be located in the same directory as the application itself. However, if the directory isn't writable (for whatever reason), the files are written to the user's home directory.

TBD: show picture?

TBD: only 1000 of 10000 top results (based on frequency) are shown.

TBD: results are disambiguated based on lemma, form, pos and core features (which are...)

### Fields / properties

TBD. Explain fields are properties in the UI (?)

### Basic queries

The queries consist of one or more parts separated by the keyword `and`. The format of the parts depend on the type of property being queried. The three types of properties are: string, numeric and boolean.

Examples for string queries:
 - `form = autossa`
   - surface form
 - `case != ine`
   - (noun) case is not inessive
 - `lemma = voi and pos = noun`
   - surface forms of the noun `voi`
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

For a full list of properties to query and the format of query parts, please see the chapters [query keys](#query-keys) and [query formatting](#query-formatting).

### Basic menu functions

The functions below use the Windows platforms keys. For macos, substitute `Cmd` for `Ctrl`.

A new window can be created with `Ctrl-N`, which copies the query and results from the currently active window, or `Shift-Ctrl-N`, which opens a new empty window. Queries from an input file list can be done with `Ctrl-I`.

There are three ways to export/copy information:
 1. `Ctrl-S` exports the result to file (csv/tsv/xlsx).
 2. `Ctrl-E` copies the results to the clipboard.
 3. `Ctrl-C` allows the user to individually select rows, columns or cells and copy them to clipboard.

For more information and more shortcuts, please see the chapter [menu functions](#menu-functions).

### Modes: database search versus input file mode

TBD. Differences. How it shows.

## Limitations

TBD: Does this belong here or more below?

## Advanced stuff

### Query formatting

A query consists of one or more parts separated by the keyword `and`:
 - `PART`
 - `PART` and `PART`
 - `PART` and `PART` and `PART` ...

The query parts generally follow the form `KEY OPERATOR VALUE`.
 - `KEY` is a string to query (`form`)
 - `OPERATOR` is a mathematical or string comparison (e.g. `=`, `>`) or set operator (`IN`, `NOT IN`)
 - `VALUE` is the value being searched

Exceptions to these include boolean queries and negative (`NOT`) queries for certain string operators. All inputs are lowercase (although the underlying data might not be).

The allowed operators vary depending on whether the key queries a string, numeric or boolean property.
 - String operators are equality (`=`), inequality (`!=`) and set operators (`IN` and `NOT IN`).
 - Numeric operators are equality (`=`), inequality (`!=`), greater than (`>`), smaller than (`<`), greater than or equal (`>=`) and smaller than or equal (`<=`).
 - Boolean queries have a special format and there are no operators: either `compound` or `not compound`

For string, a set operator allows the user to query for accepted (or not accepted) values:
 - `KEY` IN `A,B`
   - The property `KEY` must contain value `A` or `B`
 - `KEY` NOT IN `A,B`
   - The complementary set

### Query keys

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
    - The input file may contain empty lines, comment lines (starting with `#`) and content lines
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

### Init file

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
  
### External links

Not in this file:
 - Samples
 - Technical information
 - License

### 

# Old stuff

### Queries

#### String queries

String properties include `lemma`, `form`, `pos`, `case`, `clitic` and `derivation`.

For these supported operators 

Examples:
 - `form = autossa`
 - `case != ine`
 - `lemma = voi and nouncase = ine`
 - `lemma in voi,voida`
 - `lemmafreq > 10000 and lemmalen < 5`
 - `clitic not in kin,kaan`

The `start`, `middle` and `end` keys allow queries based on the properties of `form`:
 - `start = aut`
   - word starts with `aut`
 - `end in ssa,ssä`
   - word ends with `ssa` or `ssä`
 - `end not in ssa,ssä`
   - the converse
 - `middle = ta`
   - the word contains the substring `ta` but does not start or end with it

## Advanced usage

### List of query keys

String properties:
 - basic features
   - form
   - lemma
   - pos
   - word class
 - wildcard queries for form
   - start
     - form begins with string
   - middle
     - form contains string, but does not start or end with it
   - end
     - form ends with string
 - noun features
   - nouncase
   - nnumber
 - verb features
   - number
   - tense
   - person
   - verbform
 - other morphological features
   - posspers
   - possnum
   - derivation
   - clitic

Numeric properties:
 - len
   - form length
 - lemmalen
   - lemma length
 - freq
   - form surface frequency
 - lemmafreq
   - lemma frequency (for the specific part-of-speech, i.e. word class)
 - hood
   - orthographic neighbourhood
 - ambform
   - measure of surface form ambiguity
 - amblemma
   - measure of lemma ambiguity
 - initgramfreq
 - fingramfreq
 - bigramfreq

Boolean properties:
 - compound
   - whether the word form is a compound

### Advanced queries

A query part may relate to a string, numeric or boolean value.
 - string: `KEY` `OPERATOR` `VALUE`
 - numeric: `KEY` `OPERATOR` `VALUE`
 - boolean: `KEY` OR `NOT KEY`

Allowed keys:
 - string: `lemma`, `form`, `pos`, `start`, `middle`, `end`, `case`, `number`, `clitic`, `derivation`, ...
 - numeric: `len`, `lemmafreq`, `freq`, `initgramfreq`, `fingramfreq`, `bigramfreq`, ...
 - boolean: `compound`

Allowed operators:
 - string: `=` `!=` `in` `like`
   - word `NOT` can be prepended to `in` and `like`
   - for IN, the `VALUE` may contain comma-separated strings
 - numeric: `=` `!=` `<` `>` `<=` `>=`

The `LIKE` operator can be used if the above functions do not suffice. 
This operators allows the querying of any string property using a wildcard syntax, where the wildcard is `%`.
The operator is not generally recommended as it is slower than the alternatives.

Examples:
 - `lemma like voi%`
   - lemma starts with string `voi`
 - `form like %ta%`
   - form contains the substring `ta`
   - note the difference to the operator `middle`
     - this search does not exclude strings that start with `ta`


