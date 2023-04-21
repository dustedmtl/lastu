## Technical information

### Word classes

#### POS vs AUX

For most cases, the application considers the word classes `VERB` and `AUX` equivalent. For this reason, each row records both the original frequency and the combined frequency in the case where the row is not unique according to the equivalent. Duplicate indexes are also required (whenever frequency is used in an index, we also need another one for the combined frequency).

#### Lemma queries

When querying for lemma match (e.g. `lemma = autotalli`), the program also finds compound lemmas (i.e. `auto#talli`). To do this, the lemma without the compound separator is stored in a separate column.

### Calculated properties

#### Hood

The orthographic neighbourhood is considered as the set of words in the database where the Hamming distance is 1 (substitution of one letter). For calculating the neighbourhood (when building the database), the system uses a spelling dictionary with the [symspell](https://github.com/mammothb/symspellpy) python module and the [uralicNLP](https://github.com/mikahama/uralicNLP) morphological analyzer.

#### Ambform

Form ambiguity (ambform) is the probability that the lemma and word class for a form are likely to be something else than the specified lemma and word class. For example, the form `voi` is the base form for the noun `voi`; it can also be an interjection. However, the form will far more likely refer to the verb `voida`, leading to a hight ambform probability for the noun `voi`.

#### Amblemma

Lemma ambiguity is the weighted probability that some form of the lemma/word class combination is ambiguous.

### Universal Dependencies data

The underlying data comes from [universal dependencies](https://universaldependencies.org/fi/) tagged data.

Note about the specific properties:
 - all word classes are uppercase
   - NOUN, VERB, ADJ, ADV, PRON, PROPN, ...
 - morphological features are in Titlecase (Ine)
   - noun cases: Abe, Abl, Acc, Ade, All, Com, Ela, Ess, Gen, Ill, Ine, Ins, Nom, Par, Tra
   - clitics: Han, Ka, Kaan, Kin, Ko, Pa, S
   - derivations: Inen, Ja, Lainen, Llinen, Minen, Sti, Tar, Ton, Ttain, U, Vs
 - word forms and lemmas are lowercase

Note that the list of derivations and clitics may be incomplete.

