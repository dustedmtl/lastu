# Scripts for building and managing a database

For all scripts, first activate the virtual environment.

## Building a database

`build_database.py`

- Activate virtual environment (see above)
- `python build_database.py -n -i <input> -d data/<dbfile>`
  - builds a new database file `<dbfile>`
  - `<input>` may a UD dependency parsed file or a directory containing such files
    - files may be gzipped or not
- Additional arguments
  - `-N`
    - do not build indexes afterwards
  - `-s <sentencecount>`
  - `-c <filecount>`

### Generating init/fintrigram and bigram frequencies
`generate_freqs.py`

 - `python generate_freqs.py -d data/<dbfile>`

### Generating helper tables

`generate_helper_tables.py`

 - `python generate_helper_tables.py -d data/<dbfile> [options]`
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

## Managing a database

`manage_database.py`

Note that when using the script, aggregate information must be regenerated afterwards with the `generate_freqs.py`and `generate_helper_tables` scripts.

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

 - `python manage_database.py -i <sourcefiles> -o <outfile> -c concat -e`

This is mostly useful when there is a large amount of source data. In this case it makes sense to build the database in parts. 

 - Options
   - `-e`
     - Normally the script produces an error if the output database `<outfile>` already exists.
     - This option suppresses the error and allows the operation.

When combining rows from two databases, the inserts are done with 
Two databases are combined with sqlite [UPSERT](https://www.sqlite.org/lang_UPSERT.html): when a row exists in both databases, the frequencies are summed.
This method might not be the most efficient one, but it is simple and straight-forward.

### Pruning a database

 - `python manage_database.py -i <infile> -o <outfile> -c prune -f <freq>`

Prune the database by mandating a minimum frequency `<freq>`.

 - Options
   - `-f <freq>`
     - minimum frequency
   - `-l <len>`
     - maximum word length 
   - `-p <pos1,pos2>`
     - word classes to remove

Remember to re-add the helper tables and gram frequencies after pruning.

## Database statistics

`db_stats.py`

To get statistics from a database:
 - `python db_stats.py <inputfile>`

## Exporting a database

TBD

