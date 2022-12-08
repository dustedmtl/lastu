# wm2

Wordmill2 is a program for generating stimulus words for psycholinguistic research.

The database for the program is generated from one data files containing [Universal Dependencies](https://universaldependencies.org/fi/) parsed data.

## Features

The wordmill2 database contains various properties for lemmas and forms:
 - surface frequencies (absolute and relative)
 - initial trigram, final trigram and average bigram frequencies (absolute relative)
 - length
 - part of speech
 - orthographic neighbourhood (with Hamming distance 1)
 - ambiguity percentages for lemmas and forms
 - most important morphological features (see below)

Add properties can be queried and filtered with. Additionally, string properties can be filtered with various wildcard searches.

### Morphological features

The morphological feature set is tailored for the most important features for Finnish:
 - case
 - person, number and plural/single
 - derivatives and clitics
 - possessive suffix
 - verb tense and finiteness

## Input and output

Properties can be queried for lemmas, form or 'unwords' (i.e. words that are not proper Finnish).

Supported output formats are CSV, TSV and Excel (xlsx). The data can also be copied to clipboard.

## Documentation

 - Quick guide for using the application: [USAGE](USAGE.md)
 - Building databases for the application: [BUILDING](BUILDING.md)
 - Packaging the application into an executable: [PACKAGING](PACKAGING.md)

## Limitations

TBD. Highly tuned for Finnish.

# License

Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
