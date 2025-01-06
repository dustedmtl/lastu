"""UD file reader module."""

# pylint: disable=invalid-name, line-too-long
# too-many-locals, too-many-arguments

from typing import List, Dict, Tuple, Optional, Iterable, Callable, TextIO, Iterator
from os import walk
from os.path import isfile, join, basename, getsize
import re
import gzip
from contextlib import contextmanager
from collections import Counter
# import pyconll
# from conllu import parse_incr, TokenList
from conllu import TokenList
from conllu.exceptions import ParseException
from conllu.parser import (
    parse_sentences, parse_token_and_metadata
)
# from tqdm.notebook import tqdm
from tqdm.autonotebook import tqdm
from .mytypes import Freqs

initchars = '^'
alpha = 'abcdefghijklmnopqrstuvwxyzåäöüáàãâéèêíìïóòôõúñç'
# alphanum = r'[abcdefghijklmnopqrstuvwxyzåäöéü0-9]'
alphanum = r'[' + alpha + '0-9]+'
# alphanumplus = r'[abcdefghijklmnopqrstuvwxyzåäöéü0-9\-\.\']'
alphanumplus = '[' + alpha + r'0-9' + r'\-\.\']'
# midchars = r'[\'\.\:\-\_\#abcdefghijklmnopqrstuvwxyzåäöéü0-9]*'
midchars = r'[\'\.\:\-\_\#' + alpha + '0-9' + ']*'
endchars = '$'
hasalpha = re.compile(''.join(['.*?[', alpha, '].*?']))
validregex = re.compile(''.join([initchars, alphanum, midchars, alphanumplus, endchars]))
# alphanumregex = re.compile(''.join([initchars, alphanumplus, '+', endchars]))


# def semi_word(word: str) -> bool:
#     """Check if word is semi-valid."""
#     if not valid_word(word):
#         return False
#     if re.match(alphanumregex, word):
#        return False
#     return True


def valid_word(word: str) -> bool:
    """Check if word is valid."""
    if len(word) < 2:
        return False
    if re.match(validregex, word):
        if re.match(hasalpha, word):
            return True
    return False


def conllu_file_reader(cfile: str,
                       checker: Optional[Callable] = None,
                       sentencecount: Optional[int] = None) \
                       -> Iterable[Tuple[int, Optional[TokenList]]]:
    """Parse conllu file."""
    shortfn = basename(cfile)

    if cfile.endswith('.vrt') or cfile.endswith('.vrt.gz'):
        for idx, tokenlist in conllu_vrt_file_reader(cfile):
            yield idx, tokenlist
    else:
        if checker:
            maxsize = 10**8
            filesize = getsize(cfile)

            if filesize < maxsize:
                with open(cfile, 'r', encoding="utf-8") as fileh:
                    data = fileh.read()
                    maxcount = get_last_sentence(data)
                    if checker(shortfn, maxcount):
                        yield 0, None

        idx = 0
        with get_filehandle(cfile) as fileh:
            # fields = parse_conllu_plus_fields(fileh, metadata_parsers=None)
            try:
                for sentence in parse_sentences(fileh):
                    # The used parser module considers two spaces to be a separator, fix that.
                    # Multiple consecutive space characters are converted to a single space.
                    # The files are all separated by tabs actually
                    # sentence = sentence.replace('  ', ' ')
                    sentence = re.sub(r' +', ' ', sentence)
                    tokenlist = parse_token_and_metadata(
                        sentence,
                        # fields=fields,
                        field_parsers=None,
                        metadata_parsers=None
                    )
                    # for tokenlist in parse_incr(fileh):
                    idx += 1
                    if sentencecount and idx > sentencecount:
                        break
                    yield idx, tokenlist
            except ParseException as pe:
                print(idx, pe)
                raise pe

#        for sentence in pyconll.load.iter_from_file(cfile):
#            idx += 1
#            if sentencecount and idx > sentencecount:
#                break
#            yield idx, sentence


def conllu_vrt_file_reader(filename: str):
    """Read sentences from vrt file."""
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

    with open(filename, 'r', encoding='utf-8') as f:
        idx = 0
        fileidx = 0
        insentence = False
        tabidx = [1, 0, 2, 4, 8, 5, 6, 7, 8, 10]
        sentencedata: List[str] = []

        # FIXME: use conllu module instead of pyconll
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
                # in_string = ''.join(sentencedata)
                # print(in_string)
                sentencedata.append('\n')
                # c = pyconll.unit.conll.Conll(sentencedata)
                # c = pyconll.unit.sentence.Sentence(in_string)
                c = []  # type: ignore
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


@contextmanager
def get_filehandle(filename: str):
    """Get filehandle from file, possibly gzipped."""
    if filename.endswith('.gz'):
        with gzip.open(filename, mode='rt') as fh:
            yield fh
    else:
        with open(filename, 'r', encoding='utf-8') as fh:
            yield fh


@contextmanager
def get_trashfh(filename: Optional[str]) -> Iterator[Optional[TextIO]]:
    """Get trash filehandle from file."""
    if filename and not isfile(filename):
        with open(filename, 'w', encoding='utf-8') as fh:
            yield fh
    yield None


def get_last_sentence(data: str) -> int:
    """Get id of last sentence in conllu file."""
    sentids = re.findall(r'# sent_id = (\d+)', data, flags=re.MULTILINE)
    sentencecount = max({int(s) for s in sentids})
    # print(last)
    return sentencecount


def serialize_feats(feats: Dict) -> str:
    """Serialize feats to string."""
    fields = []
    if not feats:
        return '_'
    for k in sorted(feats.keys()):
        v = feats[k]
        fields.append(f'{k}={v}')
    return '|'.join(fields)


def conllu_freq_reader(path: str,
                       featmap: Dict,
                       origcase: Optional[bool] = False,
                       sentencecount: Optional[int] = None,
                       trashfile: Optional[TextIO] = None,
                       singlefile: Optional[bool] = False,
                       counts: Optional[Freqs] = None) -> Freqs:
    """Get frequencies from conllu files."""
    if counts:
        freqs = counts
    else:
        freqs = (Counter(), {}, Counter())

    wordcounter = freqs[0]
    wordfeats = freqs[1]
    # featcounter = freqs[2]

    for _idx, sentence in tqdm(conllu_file_reader(path,
                                                  sentencecount=sentencecount),
                               disable=not singlefile):
        # if _idx > count:
        #    break
        pos = 0
        for token in sentence:  # type: ignore
            pos += 1
            form = token['form']
            lemma = token['lemma']
            upos = token['upos']
            feats = token['feats']
            # Convert feats back to string for indexing
            origfeats = serialize_feats(feats)
            # print(form, lemma, upos, feats, origfeats)
            # origfeats = token.conll().split('\t')[5]

            if not valid_word(form.lower()) or not valid_word(lemma.lower()):
                if len(form) > 1 and len(lemma) > 1:
                    # print(form, lemma)
                    if trashfile:
                        trashfile.write('\t'.join([path, str(_idx), form, lemma]) + '\n')
                continue

            # if not re.match(hasalpha, form.lower()) or not re.match(hasalpha, lemma.lower()):
            #    print(f'not invalid: {lemma} / {form}')
            _corefeats = {}
            corefeats = None
            if feats:
                for feat in feats.keys():
                    if feat in featmap:
                        _corefeats[feat] = feats[feat]
                corefeats = serialize_feats(_corefeats)
                # featlist = []
                # for feat in sorted(_corefeats.keys()):
                #     featlist.append('='.join([feat, ','.join(_corefeats[feat])]))
                # corefeats = '|'.join(featlist)
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

                # useasidx2 = (uselemma, useform, upos, origfeats)
                # featcounter[useasidx2] += 1

    return freqs


def conllu_reader(path: str,
                  featmap: Dict,
                  verbose: bool = False,
                  origcase: Optional[bool] = False,
                  sentencecount: Optional[int] = None,
                  trashfile: Optional[TextIO] = None,
                  filecount: Optional[int] = None) -> Optional[Freqs]:
    """Read conllu files recursively."""
    print(f"Reading input files: {path}")

    if isfile(path):
        if sentencecount:
            print(f"Reading {sentencecount} sentences")

        freqs = conllu_freq_reader(path,
                                   featmap,
                                   origcase=origcase,
                                   sentencecount=sentencecount,
                                   trashfile=trashfile,
                                   singlefile=True)
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
                                           featmap,
                                           origcase=origcase,
                                           sentencecount=sentencecount,
                                           trashfile=trashfile,
                                           counts=freqs)
                if filecount and idx > filecount:
                    break
            except Exception as e:
                print(f'Error with file {fn}: {e}')

    return freqs
