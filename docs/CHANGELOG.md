# Changelog

Notable changes in the program will be documented here.

The format of this file is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.0.10] - 2023-06-21

### Added

- command line option -e to just load the program and exit (for testing)

### Changed

- Application name changed to LASTU

### Fixed

- querying and filtering method for middle != na and middle = na queries
- reading database file path from wm2.ini
- macOS building by downgrading PyQt version
- Aggregation query fix: f -> ft

## [0.0.9] - 2023-06-13

### Added

- default query to init file
- wordlist input: enable result ordering by order in input file
- prototype feature: aggregation queries
- packaging: macos version number
- packaging: copy documentation to distributable package
- testing: testing framework to packaging
- building a database: remove extra word classes such as X,PUNCT,SYM; max length filter
- pruning a database: add noindex option

### Changed

- UI: database and input file names are shortened

### Fixed

- reading database file path from wm2.ini
- when opening a new window: if query has no results, show empty result window

## [0.0.8] - 2023-05-15

### Added

- database metadata table
- basic test framework
- initial support for Spanish, Portuguese and Swedish
- github workflow for building application for macOS and Windows

### Changed

- no hard-coded morphological features, other than those defined in SQL schema
- scaling factor for bigram frequencies from one thousand to one million

### Fixed

- generate_helper_tables: do not crash if feature (e.g. derivation) is not available for the language
- word cleanup regex fixes
- styling fixes for flake8 and mypy

## [0.0.7] - 2023-05-02

### Added

- wordlist mode filtering: add handling for start, middle and end query keys

### Fixed

- wordlist mode: support input files of arbitrary size
- wordlist mode filtering: fix handling for case, number query keys
- wordlist mode filtering: fix handling for lemma = X for compounds
- multiple sort signals when opening new files

## [0.0.6] - 2023-04-24

### Added

- wordlist mode filtering: top = X
- copy-paste directly from the results window with C-c

### Fixed

- issues with opening new database, wordlist mode and data filtering

## [0.0.5] - 2023-04-06

### Added

- wordlist mode filtering

## [0.0.4] - 2022-12-29

### Added

- database building: amblemma
- properly scripted database builders

### Changed

- input file type for invalid words changed from unword to nonword

## [0.0.3] - 2022-12-09

### Added

- logging queries to history file
- query updates: middle key, relative frequencies
- UI function for opening a new database

## [0.0.2] - 2022-12-08

### Added

- database building: lemma length, lemma without separator
- sample wordlist files: lemmas, unword

### Fixed

- searching for compound lemmas

## [0.0.1] - 2022-12-02

### Added

- first version with a version number
- multithreaded application windows
- keyboard shortcuts
- hide/show columns for various categories, hiding empty columns (for features)
- query shortcuts for case, number, frequency
- start, end queries
- relative frequencies
- input from wordlist
