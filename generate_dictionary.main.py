from tqdm import tqdm
import csv, gzip
from collections import defaultdict

# TODO komentarz url
# TODO argparse
path = "PoliMorf-0.6.7.tab.gz"

acc = defaultdict(lambda: {})
all_tags = set()

with tqdm(gzip.open(path, "rt", encoding="utf-8", errors="replace")) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            raise Exception("Empty line")
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        form, lemma, tag = cols[0], cols[1], cols[2]

        unwanted_prefixes = {"adj", "adv:", 'aglt:', "depr:", "subst", 'ppron12', 'ppron3', 'prep:', 'ppas', 'pact:', 'ger:', 'imps:'}

        # reduce dict by removing unneeded entries
        if tag in {'interj', 'burk', 'comp', 'conj', 'qub'} or any(tag.startswith(p) for p in unwanted_prefixes):
            continue

        acc[lemma][tag] = form
        all_tags.add(tag)

print("All tags", all_tags)
all_tags = list(sorted(all_tags))

with open("conllu_analysis/dictionary.v4.csv", "w", encoding="utf-8", newline="") as out:
    w = csv.writer(out)
    w.writerow(["lemma", *all_tags])
    for lemma, d in acc.items():
        row = [d.get(tag, "") for tag in all_tags]
        has_at_least_one_tag = any([len(e) > 0 for e in row])
        assert has_at_least_one_tag

        w.writerow([lemma, *row])
