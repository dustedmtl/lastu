# Usage

The application needs two files to with an optional init file:
 - The executable / application (<code>wm2.exe</code> / <code>wm2.app</code>)
 - The database file (SQLite3)
 - The init file <code>wm2.ini</code> (optional)

## Init file and database file

At this point the main function of the init file is to tell the application what the database file is and where it should be found.

The init file itself is looked for from two locations:
 - The same directory where the application is located in
 - The user's home directory
   - Mac: <code>/Users/\<username\>/wm2.ini</code>
   - Windows: <code>C:\Users\<username\>\wm2.ini</code>

If the init file is not found, the database filename will default to <code>wm2database.db</code> and
the application will try to locate it from the <code>data</code> subdirectory.

## User interface

### Window management

The user interface consists of one or more windows. Shortcuts for window management:
  - <code>C-N</code> - new window
  - <code>C-W</code> - close currently active window
  - <code>C-Q</code> - quit application

### Queries

A query consists of one or more parts separated by the keyword 'and':
 - <code>form = 'auto'</code>
 - <code>lemma = 'voi' and nouncase = 'Ine'</code>

The quotes around <code>\<value></code> are optional.

A query part may relate to a string, numeric or boolean value.
 - string: <code>\<key></code> <code>\<operator></code> <code>\<value></code>
 - numeric: <code>\<key></code> <code>\<operator></code> <code>\<value></code>
 - boolean: <code>\<key></code> OR <code>NOT \<key></code>

Allowed keys:
 - string: lemma, form, pos, start, middle, end, nouncase, number, clitic, derivation, ...
 - numeric: len, frequency, initgramfreq, fingramfreq, bigramfreq, ...
 - boolean: compound

Allowed operators:
 - string: = != in like
   - for in and like, 
 - numeric: = != < > <= >=

Keys, operators and values are case-sensitive. This will change in the future.
 - all keys and operators are lowercase.
 - values are also lowercase, except..
   - Word classes (PoS) are uppercase (NOUN)
   - UD morphogical features such as case and clitic are titlecase (Ine, Ko)

TBD: List of UD tags etc

### Input and output

Input and output commands:
  - <code>C-I</code> - query from wordlist
  - <code>C-S</code> - export to file (csv/tsv/xlsx)
  - <code>C-E</code> - copy to clipboard

