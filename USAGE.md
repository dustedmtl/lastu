# Usage

The application needs two files to with an optional init file:
 - The executable / application (`wm2.exe` / `wm2.app`)
   - Alternatively, use the source version with `python3 ui-qt6.py`
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

### Window management

The user interface consists of one or more windows. Shortcuts for window management:
  - `C-N` - new window
  - `C-W` - close currently active window
  - `C-Q` - quit application

### Queries

A query consists of one or more parts separated by the keyword 'and':
 - `form = 'auto'`
 - `lemma = 'voi' and nouncase = 'Ine'`

The quotes around `<value>` are optional.

A query part may relate to a string, numeric or boolean value.
 - string: `<key>` `<operator>` `<value>`
 - numeric: `<key>` `<operator>` `<value>`
 - boolean: `<key>` OR `NOT <key>`

Allowed keys:
 - string: `lemma`, `form`, `pos`, `start`, `middle`, `end`, `nouncase`, `number`, `clitic`, `derivation`, ...
 - numeric: `len`, `frequency`, `initgramfreq`, `fingramfreq`, `bigramfreq`, ...
 - boolean: `compound`

Allowed operators:
 - string: `=` `!=` `in` `like`
   - word `NOT` can be prepended to `in` and `like` 
 - numeric: `=` `!=` `<` `>` `<=` `>=`

Keys, operators and values are case-sensitive (this will change in the future):
 - all keys and operators are lowercase.
 - values are also lowercase, except..
   - Word classes (PoS) are uppercase (`NOUN`)
   - UD morphogical features such as case and clitic are titlecase (`Ine`, `Ko`)

TBD:
 - handle cases of input automatically
 - List of UD tags etc

### Input and output

Input and output commands:
  - `C-I` - query from wordlist
  - `C-S` - export to file (csv/tsv/xlsx)
  - `C-E` - copy to clipboard

