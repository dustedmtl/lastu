"""File reader module."""

# pylint: disable=invalid-name, line-too-long, consider-using-f-string

# from typing import List, Dict, Union, Tuple, Optional, Iterable, Callable
from typing import Tuple, Optional, Iterable, Callable
from os import walk
from os.path import isfile, join, basename
import re
from collections import Counter
import pyconll
# from tqdm.notebook import tqdm
from tqdm.autonotebook import tqdm

Freqs = Tuple[Counter, Counter, Counter]

# import nltk
# nltk.download('punkt')


def conllu_file_reader(cfile: str,
                       checker: Optional[Callable] = None) -> Iterable[Tuple[int,
                                                                             Optional[pyconll.unit.sentence.Sentence]]]:
    """Parse conllu file."""
    shortfn = basename(cfile)

    fastcheck = False

    if checker:
        # Inspect the checker closure for properties
        try:
            vars = checker.__code__.co_freevars
            idx = vars.index('fastcheck')
            if idx != -1:
                fastcheck = checker.__closure__[idx].cell_contents  # type: ignore
        except Exception:
            pass

        if fastcheck:
            has_file = checker(shortfn, 0)
            if has_file:
                # print("Fast check, don't read conllu file contents for %s" % cfile)
                yield 0, None

    with open(cfile, 'r') as f:
        data = f.read()

    # Get the last sentence id for the file
    sentids = re.findall(r'# sent_id = (\d+)', data, flags=re.MULTILINE)
    # print(sentids)
    sentencecount = max(set([int(s) for s in sentids]))
    # print(last)

    if checker:
        has_file = checker(shortfn, sentencecount)
        # print(cfile, shortfn, sentencecount, has_file)
        if has_file:
            yield 0, None

    # FIXME: field order (?)
    idx = 0
    for sentence in pyconll.load_from_file(cfile):
        idx += 1
        yield idx, sentence


def conllu_freq_reader(path: str,
                       checker: Optional[Callable] = None,
                       counts: Optional[Freqs] = None) -> Freqs:
    """Get frequencies from conllu files."""
    # FIXME: generate bigram frequencies
    if counts:
        freqs = counts
    else:
        # FIXME: initialize based on type?
        freqs = (Counter(), Counter(), Counter())

    wordcounter = freqs[0]
    # print(freqs)
    # print(path)
    for _t in conllu_file_reader(path, checker):
        _idx, sentence = _t
        # if _idx > count:
        #    break
        # print(_idx, sentence)
        pos = 0
        for token in sentence:  # type: ignore
            pos += 1
            # pyconll Token fields
            form = token.form
            lemma = token.lemma
            upos = token.upos
            # print(form, lemma, upos, token.feats)
            if form and upos:
                # useasidx = ' '.join([lemma.lower(), form.lower(), upos])
                useasidx = (lemma.lower(), form.lower(), upos)
                wordcounter[useasidx] += 1

    return freqs


def conllu_reader(path: str,
                  verbose: bool = False,
                  checker: Optional[Callable] = None,
                  count: Optional[int] = None) -> Optional[Freqs]:
    """Read conllu files recursively."""
    print("Reading input files: %s" % path)
    if isfile(path):
        freqs = conllu_freq_reader(path, checker=checker)
    else:
        idx = 0
        freqs = (Counter(), Counter(), Counter())
        # freqs = None

        files = []
        for res in list(walk(path)):
            dirpath, _dirnames, filenames = res
            for fn in filenames:
                files.append((join(dirpath, fn), fn))

        total = count if count else len(files)

        for fnpath, fn in (pbar := tqdm(files[:total], total=total)):
            try:
                if not fn.endswith('conllu'):
                    continue
                if verbose:
                    pbar.set_description(f'{fn}')
                    # tqdm.write(f'Reading file: {fn}')
                    # tqdm.write(f'Reading file: {fn}', end='\r')
                    # print("Reading file: %s" % fn, end='\r')
                idx += 1
                freqs = conllu_freq_reader(fnpath,
                                           counts=freqs, checker=checker)
                if count and idx > count:
                    break
            except Exception:
                pass
    return freqs
