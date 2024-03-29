import math
import copy
from collections import Counter

import nltk
import re

def read_cacm(path):
    """Reads CACM File and extracts the ID (I), Title (T), Authors (A) and Summary (W) (if present) of all the
    documents in a dictionary"""
    with open(path, 'r') as f:
        data = f.read()
    l = re.findall(r'(\.I(.|\n)+?(?=(\n\.I|$)))', data)
    l = [x[0] for x in l]
    r1 = r'\.(I) (\d+)'
    r2 = r'\.(T)\n((.|\n)+?)(?=(\n\.|$))'
    r3 = r'\.(A)\n((.|\n)+?)(?=(\n\.|$))'
    r4 = r'\.(W)\n((.|\n)+?)(?=(\n\.|$))'
    r = r'{}|{}|{}|{}'.format(r1,r2,r3,r4)

    dictionary = {}
    for doc in l:
        x = re.findall(r, doc)
        i = 0
        id = None
        while i < len(x):
            x[i] = tuple(filter(len, x[i]))[:2]
            if x[i][0] == 'I':
                id = int(x[i][1])
                x.pop(i)
                i -= 1
            i += 1
        dictionary[id] = dict(x)
    return dictionary

def read_cacm_query(query_path, qrels_path):
    # query
    with open(query_path, 'r') as f:
        data = f.read()
    l = re.findall(r'(\.I(.|\n)+?(?=(\n\.I|$)))', data)
    l = [x[0] for x in l]
    r1 = r'\.(I) (\d+)'
    r3 = r'\.(A)\n((.|\n)+?)(?=(\n\.|$))'
    r4 = r'\.(W)\n((.|\n)+?)(?=(\n\.|$))'
    r = r'{}|{}|{}'.format(r1, r3, r4)
    query_dict = {}
    for doc in l:
        x = re.findall(r, doc)
        i = 0
        id = None
        while i < len(x):
            x[i] = tuple(filter(len, x[i]))[:2]
            if x[i][0] == 'I':
                id = int(x[i][1])
                x.pop(i)
                i -= 1
            i += 1
        query_dict[id] = dict(x)
    query_dict = {k: ' '.join(v.values()) for k,v in query_dict.items()}

    # qrels
    with open(qrels_path, 'r') as f:
        data = f.readlines()
    data = [x.split(' ')[:2] for x in data if len(x)]
    data = [(int(x), int(y)) for x, y in data]
    qrels_dict = {}
    for x, y in data:
        if x not in qrels_dict:
            qrels_dict[x] = []
        qrels_dict[x].append(y)
    query_dict = {k:v for k,v in query_dict.items() if k in qrels_dict}
    return query_dict, qrels_dict

def preprocess_cacm(dictionary : dict):
    """Preprocess CACM dictionary inplace : lower + remove stopwords + Count frequencies"""
    stop_words = set(nltk.corpus.stopwords.words('english'))
    for k in dictionary:
        s = ' '.join(dictionary[k].values()).lower()
        s = re.findall(r'\w+', s)
        s = [x for x in s if x not in stop_words]
        s = dict(Counter(s))
        dictionary[k] = s
    return dictionary

def inverse_dict(dictionary):
    r = {}
    for k in dictionary:
        for term, value in dictionary[k].items():
            if term not in r:
                r[term] = {}
            r[term][k] = value
    return r

class TermDocumentDict:
    def __init__(self, dictionary: dict = None):
        self._max_freq_docs = {k : max(v.values()) for k, v in dictionary.items()}
        self.all_documents = list(dictionary.keys())
        self.dict = inverse_dict(dictionary)
        self.N = len(dictionary)

    def documents(self, term):
        """Get all the docuemnts that contains the term with their value"""
        if term not in self.dict:
            return {}
        return self.dict[term]

    def terms(self, document):
        """Get all the terms that are in the document with their value"""
        terms = {}
        for term, d in self.dict.items():
            if document in d:
                terms[term] = d[document]
        return terms

    def add(self, term, document, value):
        if term not in self.dict:
            self.dict[term] = {}
        self.dict[term][document] = value

    def __getitem__(self, key):
        term, document = key
        if term not in self.dict:
            return 0
        d = self.dict[term]
        if document not in d:
            return 0
        return d[document]

    def weight_inplace(self):
        for k in self.dict:
            term = self.dict[k]
            ni = len(term)
            for document in term:
                term[document] = term[document] / self._max_freq_docs[document] * math.log10(self.N / ni + 1)

    def weight(self):
        """Weight inplace the dictionary using TF-IDF formula"""
        c = copy.deepcopy(self)
        c.weight_inplace()
        return c

    def __str__(self):
        return str(self.dict)

    def __repr__(self):
        return str(self)

