# Changelog

Notable changes in the program will be documented here.

The format of this file is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.0.7] - 2023-05-XX

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
