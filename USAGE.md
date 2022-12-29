# Quick Guide

The application needs two files to with an optional init file:
 - The executable / application (`wm2.exe` / `wm2.app`)
   - Alternatively, use the source version with: `python3 ui-qt6.py`
     - See the [building instructions](BUILDING.md) for generating virtualenv for python
 - The database file (SQLite3)
 - The init file `wm2.ini` (optional)

## Init file and database file

At this point the main function of the init file is to tell the application what the database file is and where it should be found. For a more general description of the options, please see [Init file configuration](#init-file-configuration).

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

The query parts  generally follow the form `KEY OPERATOR VALUE`. Exceptions to these include negative (`NOT`) queries and boolean queries.
All inputs are lowercase (although the underlying data might not be, please see the section concerning [Universal Dependencies data](#ud-data).

Examples:
 - `form = auto`
 - `lemma = voi and nouncase = Ine`
 - `case != Gen`
 - `lemmafreq > 10000 and lemmalen < 5`

The allowed operators vary depending on whether the key queries a string, numeric or boolean property.

#### String queries

String properties include `lemma`, `form`, `pos`, `case` `clitic` and `derivation`.

For these supported operators are equality (`=`), inequality (`!=`), `IN` (and `NOT IN`) and `LIKE`.

Examples:
 - `form = auto'`
 - `case != Ine`
 - `lemma in voi,voida`
 - `clitic not in Kin,Kaan`

The `start`, `middle` and `end` keys allow queries based on the properties of `form`:
 - `start = aut`
   - word starts with `aut`
 - `end in ssa,ssä`
   - word ends with `ssa` or `ssä`
 - `end not in ssa,ssä`
   - the converse
 - `middle = ta`
   - the word contains the substring `ta` but does not start or end with it

Finally, the `LIKE` can be used if the above functions do not suffice.
This operators allows the querying of any string property using a wildcard syntax, where the wildcard is `%`.

Examples:
 - `lemma like voi%`
   - lemma starts with string `voi`
 - `form like %ta%`
   - form contains the substring `ta`
   - note the difference to the operator `middle`!

For advanced queries, please see the [advanced usage](#advanced-queries).

#### Numeric queries

The numeric properties allow operators for equality (`=`), inequality (`!=`), greater than (`>`), smaller than (`<`), greater or equal (`>=`) and smaller or equal (`<=`).

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
  - `Ctrl-W` - close currently active window
  - `Ctrl-Q` - quit application

#### Input and output

Input and output commands:
  - `Ctrl-I` - query from wordlist
    - The input file may contain empty lines, comment lines (starting with `#`) and content lines
      - Before the first content line, there must be a type identified line
        - form: "# type=`querytype`"
        - querytype` can be `lemma`, `form` or `nonword`
        - The specific category is searched for the strings in the content lines
      - The file may be encoded as UTF-8 or ISO-Latin-1
    - See sample input files in the [samples directory](samples/)
  - `Ctrl-S` - export to file (csv/tsv/xlsx)
  - `Ctrl-E` - copy to clipboard
  - `Ctrl-D` - open new database

#### Hiding and showing columns

The data menu lists the various column hide/show options:
 - `Ctrl-1` to `Ctrl-3`: showing frequency columns
 - `Ctrl-4`: showing columns (morphological features) that can be hiddin
 - `Ctrl-5` to `Ctrl-8`: showing categories

### Init file configuration

The most important configuration options:
 - general
   - autoresize
 - input
   - datadir and database
 - output
   - outformat
 - query
   - fetchrows
     - the maximum number of rows to fetch from the database
   - showrows
     - the maximum number of rows to show in the UI
 - style
   - fontsize

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
   - the use of the LIKE operator is generally not recommended
   - for IN, the value may contain comma-separated values
 - numeric: `=` `!=` `<` `>` `<=` `>=`


