# LASTU

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Platform](https://img.shields.io/badge/platform-windows%20|%20MacOS-orange.svg)

LASTU (Lexical Application for STimulus Unearthing) is a program for generating stimulus words for psycholinguistic research.
It has been primarily developed for Finnish.

The database for the program has been generated from one data files containing [Universal Dependencies](https://universaldependencies.org/fi/) parsed data.

## Features

A LASTU database contains various properties for lemmas and forms:
 - surface frequencies (absolute and relative)
 - initial trigram, final trigram and average bigram frequencies (absolute and relative)
 - length
 - part of speech
 - orthographic neighbourhood (with [Hamming distance](https://en.wikipedia.org/wiki/Hamming_distance) 1)
 - ambiguity percentages for lemmas and forms
 - most important morphological features (see below)

Add properties can be queried and filtered with. Additionally, string properties can be filtered with various wildcard searches.

Each row in a database in unique according to four properties:
 - lemma
 - form
 - word class (part of speech)
 - morphological feature string
   - for the "core" Finnish features (see below)

### Morphological features

The morphological feature set is tailored for the most important features for Finnish:
 - case
 - person, number and plural/single
 - derivatives and clitics
 - possessive suffix
 - verb mood, tense and finiteness

## Input and output

Properties can be queried for lemmas, form or 'non-words' (i.e. words that are not proper Finnish).

Supported output formats are CSV, TSV and Excel (xlsx). The data can also be copied to the clipboard.

## Running the program

Running the source version:
 - `python3 ui-qt6.py`

Please see the user guide for downloading a database or an executable package.

## Documentation

 - User guide for using the application: [USERGUIDE](docs/USERGUIDE.md)
 - Technical data
   - Building databases for the application: [BUILDING](docs/BUILDING.md)
   - Documentation for the scripts: [SCRIPTS](docs/SCRIPTS.md)
   - Packaging the application into an executable: [PACKAGING](docs/PACKAGING.md)
   - Technical information: [TECHINFO](docs/TECHINFO.md)
   - Known issues: [ISSUES](docs/ISSUES.md)
 - Input file samples: [SAMPLES](docs/SAMPLES.md)

## Limitations

The database and software are tailored for Finnish.
 - The data in the database is disambiguated based on the so-called "core" morphological features for Finnish.
   - For other languages, most UD features are directly supported.
 - The software has no support for features that are not relevant for Finnish, such as information regarding pronunciation.

## Citing

When using the software in your research, please use the following citation:

Sami Itkonen, Tuomo Häikiö, Seppo Vainio, and Minna Lehtonen. 2024. LASTU: A psycholinguistic search tool for Finnish lexical stimuli. Behavior Research Methods. https://doi.org/10.3758/s13428-024-02347-x

If you also use our Finnish database(s) derived from the Finnish Internet Parsebank, your should also cite its creators:

Juhani Luotolahti, Jenna Kanerva, Veronika Laippala, Sampo Pyysalo, and Filip Ginter. 2015. Towards Universal Web Parsebanks. In Proceedings of the Third International Conference on Dependency Linguistics (Depling 2015), pages 211-220, Uppsala, Sweden. Uppsala University, Uppsala, Sweden. https://aclanthology.org/W15-2124/


# License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Copyright &copy; 2022-2023 University of Turku.


## Documentation license
Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

Documentation is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg
