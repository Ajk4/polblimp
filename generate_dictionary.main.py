from tqdm import tqdm
import csv, gzip
from collections import defaultdict

TAG_F = "praet:sg:f:perf"
TAG_M = "praet:sg:m1.m2.m3:perf"

acc = defaultdict(lambda: {})

path = "PoliMorf-0.6.7.tab.gz"

with tqdm(gzip.open(path, "rt", encoding="utf-8", errors="replace")) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        form, lemma, tag = cols[0], cols[1], cols[2]
        if tag in {TAG_F, TAG_M}:
            # Use only one option, ignore multi-option
            acc[lemma][tag] = form

with open("dictionary.csv", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow([TAG_M, TAG_F])
    for lemma, d in acc.items():
        if TAG_M in d and TAG_F in d:
            w.writerow([d[TAG_M], d[TAG_F]])
