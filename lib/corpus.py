"""File reader module."""

# pylint: disable=invalid-name, line-too-long
# too-many-locals, too-many-arguments

# from typing import List, Dict, Union, Tuple, Optional, Iterable, Callable
from typing import List, Tuple, Optional, Iterable, Callable
from os import walk
from os.path import isfile, join, basename, getsize
import re
import gzip
from collections import Counter
import pyconll
# from tqdm.notebook import tqdm
from tqdm.autonotebook import tqdm
from .mytypes import Freqs


# import nltk
# nltk.download('punkt')


def conllu_file_reader(cfile: str,
                       checker: Optional[Callable] = None,
                       sentencecount: Optional[int] = None) \
                       -> Iterable[Tuple[int, Optional[pyconll.unit.sentence.Sentence]]]:
    """Parse conllu file."""
    shortfn = basename(cfile)

    fastcheck = False

    if checker:
        # Inspect the checker closure for properties
        try:
            varrs = checker.__code__.co_freevars
            idx = varrs.index('fastcheck')
            if idx != -1:
                fastcheck = checker.__closure__[idx].cell_contents  # type: ignore
        except Exception:
            pass

        if fastcheck:
            has_file = checker(shortfn, 0)
            if has_file:
                # print("Fast check, don't read conllu file contents for %s" % cfile)
                yield 0, None

    if cfile.endswith('.vrt') or cfile.endswith('.vrt.gz'):
        # Convert suomi24 data to standard ConLL-U order
        outorder = {
            0: 'ref',
            1: 'lemma',
            2: 'word',
            3: 'pos',
            5: 'msd',
            6: 'dephead',
            7: 'deprel',
            9: 'lex',
        }
        inorder = None

        # FIXME: move to a different function
        with open(cfile, 'r') as f:
            idx = 0
            fileidx = 0
            insentence = False
            tabidx = [1, 0, 2, 4, 8, 5, 6, 7, 8, 10]
            sentencedata: List[str] = []

            for line in tqdm(f):
                idx += 1
                if 'positional-attributes' in line:
                    attrs = re.search(r':\s+(.*)\/', line)
                    if attrs:
                        _attrs = attrs.group(1).split()
                        inorder = {k: i for i, k in enumerate(_attrs)}
                        # print(inorder)
                if line.startswith('</sentence'):
                    insentence = False
                    fileidx += 1
                    in_string = ''.join(sentencedata)
                    # print(in_string)
                    sentencedata.append('\n')
                    # c = pyconll.unit.conll.Conll(sentencedata)
                    c = pyconll.unit.sentence.Sentence(in_string)
                    sentencedata = []
                    yield fileidx, c
                if insentence:
                    # reformat fields to standard (?) ConLL-U format
                    tabs = line.split('\t')
                    if inorder:
                        nutabs = []
                        for _i in range(0, 10):
                            if _i in outorder:
                                field = outorder.get(_i)
                                inidx = inorder[field]
                                value = tabs[inidx]
                                # print(field, inidx, value)
                                if field == 'msd' and value != '_':
                                    if '_' in value and '=' not in value:
                                        nuvals = []
                                        for _v in value.split('|'):
                                            try:
                                                if '_' in _v:
                                                    vals = _v.split('_')
                                                    k = vals[0]
                                                    if len(vals) > 2:
                                                        v = '_'.join(vals[1:])
                                                    else:
                                                        v = vals[1]
                                                    nuvals.append('='.join([k, v]))
                                                else:
                                                    nuvals.append(_v)
                                            except ValueError as e:
                                                print(_v)
                                                raise e
                                        value = '|'.join(nuvals)
                                nutabs.append(value)
                            else:
                                nutabs.append('_')
                    else:
                        nutabs = [tabs[i] for i in tabidx]
                    # print(line)
                    # print(nutabs)
                    sentencedata.append('\t'.join(nutabs))
                if line.startswith('<sentence'):
                    insentence = True

                if idx > 20:
                    pass

        yield 0, ''
    else:
        maxsize = 10**8
        filesize = getsize(cfile)

        if filesize < maxsize:
            with open(cfile, 'r', encoding="utf-8") as f:
                data = f.read()
                sentencecount = get_last_sentence(data)
                if checker:
                    has_file = checker(shortfn, sentencecount)
                    # print(cfile, shortfn, sentencecount, has_file)
                    if has_file:
                        yield 0, None

        idx = 0
        # for sentence in pyconll.load_from_file(cfile):
        # FIXME: read gzipped file
        # FIXME: use conllu module instead of pyconll
        for sentence in pyconll.load.iter_from_file(cfile):
            idx += 1
            if sentencecount and idx > sentencecount:
                break
            yield idx, sentence


def get_last_sentence(data: str) -> int:
    """Get id of last sentence in conllu file."""
    sentids = re.findall(r'# sent_id = (\d+)', data, flags=re.MULTILINE)
    sentencecount = max({int(s) for s in sentids})
    # print(last)
    return sentencecount


def conllu_freq_reader(path: str,
                       checker: Optional[Callable] = None,
                       origcase: Optional[bool] = False,
                       sentencecount: Optional[int] = None,
                       counts: Optional[Freqs] = None) -> Freqs:
    """Get frequencies from conllu files."""
    if counts:
        freqs = counts
    else:
        freqs = (Counter(), {}, Counter())

    wordcounter = freqs[0]
    wordfeats = freqs[1]
    featcounter = freqs[2]

    # FIXME: move map to another file? data class?
    featmap = {
        'Number': 'nnumber',
        'Case': 'nouncase',
        'Derivation': 'derivation',
        'Tense': 'tense',
        'Person': 'person',
        'VerbForm': 'verbform',
        'Clitic': 'clitic'
    }

    # print(freqs)
    # print(path)
    for _t in tqdm(conllu_file_reader(path, checker,
                                      sentencecount=sentencecount)):
        _idx, sentence = _t
        # if _idx > count:
        #    break
        pos = 0
        for token in sentence:  # type: ignore
            pos += 1
            # pyconll Token fields
            form = token.form
            lemma = token.lemma
            upos = token.upos
            feats = token.feats
            # print(form, lemma, upos, feats)
            # Convert feats back to string for indexing
            origfeats = token.conll().split('\t')[5]

            _corefeats = {}
            corefeats = None
            if feats:
                for feat in feats.keys():
                    if feat in featmap:
                        _corefeats[feat] = feats[feat]
                featlist = []
                for feat in sorted(_corefeats.keys()):
                    featlist.append('='.join([feat, ','.join(_corefeats[feat])]))
                corefeats = '|'.join(featlist)
                # print(origfeats, '=>', corefeats)

            if ',' in origfeats:
                # print(form, lemma, upos, feats)
                pass

            if lemma and form and upos:
                if not feats:
                    origfeats = "_"
                    corefeats = "_"

                uselemma = lemma if origcase else lemma.lower()
                useform = form if origcase else form.lower()
                useasidx = (uselemma, useform, upos, corefeats)
                wordcounter[useasidx] += 1

                wordfeats[useasidx] = feats

                useasidx2 = (uselemma, useform, upos, origfeats)
                featcounter[useasidx2] += 1

    return freqs


def conllu_reader(path: str,
                  verbose: bool = False,
                  checker: Optional[Callable] = None,
                  origcase: Optional[bool] = False,
                  sentencecount: Optional[int] = None,
                  filecount: Optional[int] = None) -> Optional[Freqs]:
    """Read conllu files recursively."""
    print(f"Reading input files: {path}")

    if isfile(path):
        if sentencecount:
            print(f"Reading {sentencecount} sentences")

        freqs = conllu_freq_reader(path,
                                   origcase=origcase,
                                   sentencecount=sentencecount,
                                   checker=checker)
    else:
        idx = 0
        # FIXME: move initialization to another file or data class?
        # columns = ['lemma', 'form', 'pos', 'case', 'feats', 'count']
        freqs = (Counter(), {}, Counter())

        files = []
        for res in list(walk(path)):
            dirpath, _dirnames, filenames = res
            for fn in filenames:
                files.append((join(dirpath, fn), fn))

        total = filecount if filecount else len(files)

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
                                           origcase=origcase,
                                           sentencecount=sentencecount,
                                           counts=freqs,
                                           checker=checker)
                if filecount and idx > filecount:
                    break
            except Exception:
                pass
    return freqs
