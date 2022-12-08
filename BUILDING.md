# Building a database

## Setup
- Clone the repository
  - `git clone`
- Create a virtual environment for packaging (venv)
  - `python3 -m venv venv`
  - See also: https://docs.python.org/3/library/venv.html
- Activate virtual environment
  - Mac:
    - `source venv/bin/activate`
  - Windows:
    - `venv\Scripts\activate.bat`
 - Install requirements to packenv
   - `pip3 install -r requirements.txt`

## Building a database
- Activate virtual environment (see above)
- `python3 build_database.py -n -i <input> -d data/<dbfile>`
  - builds a new database file `<dbfile>`
  - `<input>` may a UD dependency parsed file or a directory containing such files
    - files may be gzipped or not
- Additional arguments
  - `-N`
    - do not build indexes afterwards
  - `-s <sentencecount>`
  - `-c <filecount>`

## Additional scripts

It is necessary to run all of the below scripts to get a functional database.

### Add indexes
 - `sqlite3 data/<dbfile> < sql/wordfreqs_indexes.sql`

### Generate init/fin trigram and bigram frequencies
 - `python3 generate_freqs.py -d data/<dbfile>`

### Generate helper tables
 - `python3 generate_helper_tables.py -d data/<dbfile> -a`
 - Arguments
   - `-a`
     - All of the below
   - `-p`
     - Generate frequency information for pos/posx
   - `-F`
     - Generate feature tables
   - `-f`
     - Generate aggregate information for forms
   - `-l`
     - Generate aggregate information for lemmas
   - `-H`
     - Generate neighbourhood information for forms
   - `-c`
     - Generate generated aggregate information to the wordfreqs tables

## Managing a database

### Combining one or more database files

### Rebuilding indexes

### Pruning a database

