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

TBD

### Input and output

Input and output commands:
  - <code>C-I</code> - query from wordlist
  - <code>C-S</code> - export to file (csv/tsv/xlsx)
  - <code>C-E</code> - copy to clipboard

