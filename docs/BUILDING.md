# Building a database

The database building involves four phases
 - Adding the initial schema (_wordfreqs_ and _features_ tables)
 - Importing the data
 - Generating aggregate information (gram frequencies, ambiguity information, orthographic neighbourhood)
 - Adding indexes to the schema

The indexes complicate the building process. On one hand, they are necessary for generating aggregate information.
On the other hand, having an index on a table may reduce performance when adding rows to the table or deleting rows from it.
During the building process, indexes are therefore automatically added or deleted as necesssary.

## Setup
- Clone the repository
  - `git clone <giturl>`
- Create a virtual environment for building (venv)
  - `python -m venv venv`
  - See also: https://docs.python.org/3/library/venv.html
- Activate virtual environment
  - macOS:
    - `source venv/bin/activate`
  - Windows:
    - `venv\Scripts\activate.bat`
 - Install requirements to venv
   - `pip install -r requirements.txt`

Full documentation for scripts: [SCRIPTS](SCRIPTS.md)

## Building a database

- Activate virtual environment (see above)
- `python build_database.py -n -i <input> -d data/<dbfile>`
  - builds a new database file `<dbfile>`
  - `<input>` may a UD dependency parsed file or a directory containing such files
    - files may be gzipped or not
- Additional arguments
  - `-N`
    - do not build indexes afterwards

## Additional scripts

It is necessary to run all of the below scripts to get a functional database.

### Add indexes
 - `sqlite3 data/<dbfile> < sql/wordfreqs_indexes.sql`

### Generate init/fin trigram and bigram frequencies
 - `python generate_freqs.py -d data/<dbfile>`

### Generate helper tables
 - `python generate_helper_tables.py -d data/<dbfile> -a`
 - `python generate_helper_tables.py -d data/<dbfile> -c`

The recommended file name schema is `<lang>_<source>_<size>_<minfreq>.db`, where
 - `<lang>` for the language (e.g., `fi`, `es`)
 - `<source>` for the data source (e.g., `parsebank`, `tdt`)
 - `<size>` for the gross token size (e.g., `50M`, `2B`)
 - `<minfreq>` for the minimum frequency, or `full` if not applicable (e.g., `10`)
   - See [SCRIPTS](SCRIPTS.md) for pruning a database

## Building a database from parts

The process generally takes the form of building databases for a subset of the input files without indexes and then combining them with the `manage_database.py`script:
 - For each source file/directory, run:
   - `python3 build_database.py -n -i [source] -d [intermediate_database] -N`
 - Combine the intermediate databases
   - `python3 manage_database.py -i [intermediate_databases] -o [finalfile] -c concat -e`

After having the final database file, add indexes, gram frequencies and helper tables as above.

## Building for languages other than Finnish.

The building can take any UD-formatted file as input.

The feature set for the language is defined in SQL schema, specifically the _features_ table. To support non-default morphological features, there are two options:
1. modify the schema file _sql/features.sql_
2. add or modify the schema file for the language in the _sql/languages/_ (recommended)

For the second option, the command line option `--language` or (`-l`) must be used for the initial database builder script.

The most common typological features are listed _lib/features.py_.
