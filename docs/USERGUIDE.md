# User Guide

The application needs two files to with an optional init file:
 - The executable / application (`wm2.exe` / `wm2.app`)
 - The database (a file in the form of SQLite3)
 - The init file `wm2.ini` (optional)

## Init file and database file

The main function of the init file is to tell the application what the database file is and where it should be found. For a more general description of the options, please see [Init file configuration](#init-file-configuration).

The init file itself is looked for from two locations:
 - The same directory where the application is located in
 - The user's home directory
   - Mac: `/Users/<username>/wm2.ini`
   - Windows: `C:\Users\<username>\wm2.ini`

If the init file is not found, the database filename will default to `wm2database.db` and
the application will try to locate it from the `data` subdirectory.

## Logging

The application generates debug logs to the file `wm2log.txt` and logs executed searches to the file `wm2history.txt`. These files will by default be located in the same directory as the application itself. However, if the directory isn't writable (for whatever reason), the files are written to the user's home directory.

## User interface

There are various function available through keyboard shortcuts and the menu for inputting and outputting files and hiding/showing various fields.
Please see the [UI functions](#ui-functions) for those.

### Queries

A query consists of one or more parts separated by the keyword `and`:
 - `PART`
 - `PART` and `PART`
 - `PART` and `PART` and `PART` ...

The query parts  generally follow the form `KEY OPERATOR VALUE`.
 - `KEY` is a string to query (`form`)
 - `OPERATOR` is a mathematical or string comparison (e.g. `=`, `>`) or set operator ('IN', 'NOT IN')
 - `VALUE` is the value being searched

Exceptions to these include negative (`NOT`) queries and boolean queries.
All inputs are lowercase (although the underlying data might not be, please see the section concerning [Universal Dependencies data](#ud-data).

The allowed operators vary depending on whether the key queries a string, numeric or boolean property.

A set operator allows the user to query for accepted (or not accepted) values:
 - `KEY` IN `A,B`
   - The property `KEY` must contain value `A` or `B`
 - `KEY` NOT IN `A,B`
   - The complementary set

For a full list of keys to query, please see [the full list](#list-of-query-keys).

#### String queries

String properties include `lemma`, `form`, `pos`, `case`, `clitic` and `derivation`.

For these supported operators are equality (`=`), inequality (`!=`) and set operators (`IN` and `NOT IN`).

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

For advanced queries, please see the [advanced usage](#advanced-queries).

#### Numeric queries

The numeric properties allow operators for equality (`=`), inequality (`!=`), greater than (`>`), smaller than (`<`), greater than or equal (`>=`) and smaller than or equal (`<=`).

Examples:
 - `len > 10`

#### Boolean queries

The only supported boolean query is `compound`.

Examples:
 - `pos = noun and compound`
   - compound noun
 - `pos = adj and not compound`
   - non-compound adjective

## Advanced usage

###  UI functions

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
  - `Ctrl-E` - copy to clipboard
  - `Ctrl-D` - open new database

TODO: add samples here instead of link [samples directory](samples/)

#### Hiding and showing columns

The data menu lists the various column hide/show options:
 - `Ctrl-1` to `Ctrl-3`: showing frequency columns
 - `Ctrl-4`: showing columns (morphological features) that can be hidden
 - `Ctrl-5` to `Ctrl-8`: showing categories

### Init file configuration

The most important configuration options:
 - general
   - autoresize
     - set window width automatically to the width of the columns
   - opendbwithnewwindow
     - When opening new database, open new window
- input
   - datadir and database
 - output
   - outformat
     - xlsx, csv, tsv
 - query
   - fetchrows
     - the maximum number of rows to fetch from the database (10000)
   - showrows
     - the maximum number of rows to show in the UI (1000)
 - style
   - fontsize (11)
  
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

### UD data

The underlying data comes from [universal dependencies](https://universaldependencies.org/fi/) tagged data.

Note about the specific properties:
 - all word classes are uppercase
   - NOUN, VERB, ADJ, ADV, PRON, PROPN, ...
 - morphological features are in Titlecase (Ine)
   - noun cases: Abe, Abl, Acc, Ade, All, Com, Ela, Ess, Gen, Ill, Ine, Ins, Nom, Par, Tra
   - clitics: Han, Ka, Kaan, Kin, Ko, Pa, S
   - derivations: Inen, Ja, Lainen, Llinen, Minen, Sti, Tar, Ton, Ttain, U, Vs
 - word forms and lemmas are lowercase

Note that the list of derivations and clitics may be incomplete.

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


