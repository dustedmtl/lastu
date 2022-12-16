# Building a database

## Setup
- Clone the repository
  - `git clone <giturl>`
- Create a virtual environment for building (venv)
  - `python3 -m venv venv`
  - See also: https://docs.python.org/3/library/venv.html
- Activate virtual environment
  - Mac:
    - `source venv/bin/activate`
  - Windows:
    - `venv\Scripts\activate.bat`
 - Install requirements to venv
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
 - Options
   - `-a`
     - All of the below (except -c)
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
     - Copy hood and ambform information to the wordfreqs table

In practice, you should first run the script with the argument `-a` and then with argument `-c`.

## Managing a database

Note that when using the `manage_database.py` script, aggregate information must be regenerated with the `generate_freqs.py`and `generate_helper_tables` scripts.

 - General options
   - `-c <cmd>`
     - Run operations `<cmd>`
   - `-i <file1> [file2, ...]`
     - Source file (or files)
   - `-o <outfile`
     - Output file. The source database will be modified in-place unless this option is present.
   - `-y`
     - Do not ask for confirmation when executing a pruning operation.
     - This option is necessary if the script needs to be run in a batch script.

### Combining one or more database files

 - `python3 manage_database.py -i <sourcefiles> -o <outfile> -c concat -e`

This is mostly useful when there is a large amount of source data. In this case it makes sense to build the database in parts. 

 - Options
   - `-e`
     - Normally the script produces an error if the output database `<outfile>` already exists.
     - This option suppresses the error and allows the operation.

### Pruning a database

 - `python3 manage_database.py -i <infile> -o <outfile> -c prune -f <freq>`

Prune the database by mandating a minimum frequency `<freq>`.

 - Options
   - `-f <freq>`
     - minium frequency

  
