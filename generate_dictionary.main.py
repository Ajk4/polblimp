from tqdm import tqdm
import csv, gzip
from collections import defaultdict

# pri - pierwsza osoba
# sec - druga osoba
# ter - trzecia osoba

TAGS = [
    "fin:sg:pri:perf",
    "fin:sg:sec:perf",
    "fin:sg:ter:perf",
    "praet:sg:f:perf",
    "praet:sg:m1.m2.m3:perf"
]

acc = defaultdict(lambda: {})

# TODO komentarz url
# TODO argparse
path = "PoliMorf-0.6.7.tab.gz"

all_tags = set()

with tqdm(gzip.open(path, "rt", encoding="utf-8", errors="replace")) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        form, lemma, tag = cols[0], cols[1], cols[2]
        if tag in TAGS:
            # Use only one option, ignore multi-option
            acc[lemma][tag] = form

        all_tags.add(tag)

print("All tags", all_tags)

with open("dictionary.v2.csv", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow(["lemma", *TAGS])
    for lemma, d in acc.items():
        row = [d.get(tag, "") for tag in TAGS]
        has_at_least_on_tag = any([len(e) > 0 for e in row])
        if has_at_least_on_tag:
            w.writerow([lemma, *row])
