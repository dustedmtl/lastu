"""List of supported features."""

# pylint: disable=invalid-name, line-too-long

allfeatures = {
    'Number': 'nnumber',  # 'number' is a reserved word in SQL, so 'nnumber'.
    'Case': 'nouncase',  # 'case' is a reserved word in SQL.
    'Gender': 'gender',
    'Definite': 'definite',
    'Mood': 'mood',
    'Tense': 'tense',
    'Aspect': 'aspect',
    'Voice': 'voice',
    'Person': 'person',
    'VerbForm': 'verbform',
    'PartForm': 'partform',
    'Degree': 'degree',
    'Person[psor]': 'posspers',
    'Number[psor]': 'possnum',
    'Clitic': 'clitic',
    'Derivation': 'derivation',
    'Style': 'style',
    'Typo': 'typo',
}
