# Usage

The application needs two files to with an optional init file:
 - The executable / application (`wm2.exe` / `wm2.app`)
   - Alternatively, use the source version with: `python3 ui-qt6.py`
   - See the [building instructions](BUILDING.md) for generating virtualenv for python
 - The database file (SQLite3)
 - The init file `wm2.ini` (optional)

## Init file and database file

At this point the main function of the init file is to tell the application what the database file is and where it should be found.

The init file itself is looked for from two locations:
 - The same directory where the application is located in
 - The user's home directory
   - Mac: `/Users/<username>/wm2.ini`
   - Windows: `C:\Users\<username>\wm2.ini`

If the init file is not found, the database filename will default to `wm2database.db` and
the application will try to locate it from the `data` subdirectory.

## User interface

There are various function available through keyboard shortcuts and the menu for inputting and outputting files and hiding/showing various fields.
Please see the [advanced usage](#advanced-usage) for those.

## Basic usage

### Queries

A query consists of one or more parts separated by the keyword `and`:
 - `PART`
 - `PART` and `PART`


The query parts themselves generally follow the form `KEY` `OPERATOR` `VALUE`.
All inputs are lowercase (although the underlying data might not be, please see the section concerning [Universal Dependecnies data](#ud-data).

Examples
 - `form = 'auto'`
 - `lemma = 'voi' and nouncase = 'Ine'`
 - 

### Logging

The application logs to the file `wm2log.txt`in the user's home directory.

### TBD

A query part may relate to a string, numeric or boolean value.
 - string: `<key>` `<operator>` `<value>`
 - numeric: `<key>` `<operator>` `<value>`
 - boolean: `<key>` OR `NOT <key>`

The quotes around `<value>` are optional.

Allowed keys:
 - string: `lemma`, `form`, `pos`, `start`, `middle`, `end`, `nouncase`, `number`, `clitic`, `derivation`, ...
 - numeric: `len`, `frequency`, `initgramfreq`, `fingramfreq`, `bigramfreq`, ...
 - boolean: `compound`

Allowed operators:
 - string: `=` `!=` `in` `like`
   - word `NOT` can be prepended to `in` and `like`
   - the use of the LIKE operator is generally not recommended
   - for IN, the value may contain comma-separated values
 - numeric: `=` `!=` `<` `>` `<=` `>=`

Shortcuts
 - the following keys have shortcuts:
   - `freq` for `frequency`
   - `case` for `nouncase`

Keys, operators and values are case-insensitive. The cases for the data based on the underlying UD data:
 - all keys and operators are lowercase.
 - values are also lowercase, except..
   - Word classes (PoS) are uppercase (`NOUN`)
   - UD morphogical features such as case and clitic are titlecase (`Ine`, `Ko`)

The query parser will convert all the user-supplied values to the appropriate case.

TBD:
 - Explain AUX/VERB handling
 - Examples
 - Interpreting calculated variables (relative frequencies, hood, ambform, amblemma9

### Advanced usage

## UI functrions

### Opening and closing windows

The user interface consists of one or more windows. Shortcuts for window management:
  - `C-N` - new window
  - `C-W` - close currently active window
  - `C-Q` - quit application

### Input and output

Input and output commands:
  - `C-I` - query from wordlist
    - See sample input files in the [samples directory](samples/)
  - `C-S` - export to file (csv/tsv/xlsx)
  - `C-E` - copy to clipboard

### Hiding and showing columns

The data menu lists the various column hide/show options:
 - `C-1` to `C-3`: showing frequency columns
 - `C-4`: showing columns (morphological features) that can be hiddin
 - `C-5` to `C-8`: showing categories

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

Some notes about the data:
 - all word classes are uppercase
   - NOUN, VERB, ADJ, ADV, PRON, PROPN, etc
 - morphological features are in Titlecase (Ine)
   - noun cases: Abe, Abl, Acc, Ade, All, Com, Ela, Ess, Gen, Ill, Ine, Ins, Nom, Par, Tra
   - clitics: Han, Ka, Kaan, Kin, Ko, Pa, S
   - derivations: Inen, Ja, Lainen, Llinen, Minen, Sti, Tar, Ton, Ttain, U, Vs
 - word forms and lemmas and lowercase

Note that the list of derivations and clitics may be incomplete.

## Jupyter notebooks

TBD

