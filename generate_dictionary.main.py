from tqdm import tqdm
import csv, gzip
from collections import defaultdict

# pri - first person
# sec - second person
# ter - third person

# sg - singular
# pl - plural

fin_tags = []

for t1 in ["sg", "pl"]:
    for t2 in ["pri", "sec", "ter"]:
        for t3 in ["perf", "imperf"]:
            fin_tags.append(f"fin:{t1}:{t2}:{t3}")

TAGS = [
    *fin_tags,
    'praet:sg:n1.n2:perf'
    'praet:sg:n1.n2:imperf'
    'praet:sg:n1.n2:imperf.perf'
    'praet:sg:f:perf',
    'praet:sg:f:imperf',
    "praet:sg:m1.m2.m3:perf",
    'praet:sg:m1.m2.m3:imperf',
    'praet:sg:m1.m2.m3:imperf.perf',
    'praet:pl:m1.p1:perf',
    'praet:pl:m1.p1:imperf',
    'praet:pl:m1.p1:imperf.perf',
    'praet:pl:m2.m3.f.n1.n2.p2.p3:perf',
    'praet:pl:m2.m3.f.n1.n2.p2.p3:imperf',
    'praet:pl:m2.m3.f.n1.n2.p2.p3:imperf.perf',
    'ppron3:sg:nom:m1.m2.m3:ter:_:_',
]

assert len(TAGS) == len(set(TAGS)), "No duplicate tags"

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

        # HACK FIXME
        if tag.endswith(":nagl"):
            tag = tag[:-len(":nagl")]

        if tag in TAGS:
            # Use only one option, ignore multi-option
            acc[lemma][tag] = form

        all_tags.add(tag)

print("All tags", all_tags)

with open("conllu_analysis/dictionary.v3.csv", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow(["lemma", *TAGS])
    for lemma, d in acc.items():
        row = [d.get(tag, "") for tag in TAGS]
        has_at_least_on_tag = any([len(e) > 0 for e in row])
        if has_at_least_on_tag:
            w.writerow([lemma, *row])


for tag in TAGS:
    if tag not in all_tags:
        print(f"unexpected tag {tag}")
