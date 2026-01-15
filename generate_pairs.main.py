import re
import pandas as pd

df = pd.read_excel("poliqarp.xls", names=["before", "matched", "after"])

dict_df = pd.read_csv("dictionary.csv")
print(dict_df.columns)
m_by_f = {row["praet:sg:f:perf"]: row["praet:sg:m1.m2.m3:perf"] for _, row in dict_df.iterrows()}

pattern = r'(\S+)\s*\[[^\]]*\]'

correct_sentences = []
incorrect_sentences = []

ix = 0
for _, row in df.iterrows():
    matched = row["matched"]
    after = row["after"]

    tokens = re.findall(r'(\S+)\s*\[[^\]]*\]', matched)
    noun = tokens[0]
    verb = tokens[1]

    sentence_end = after.find(".")
    if sentence_end != -1:
        after = after[:sentence_end]

    if verb not in m_by_f:
        continue

    masc_verb = m_by_f[verb]

    correct_sentence = f"{noun.capitalize()} {verb}{after}"
    incorrect_sentence = f"{noun.capitalize()} {masc_verb}{after}"

    correct_sentences.append(correct_sentence)
    incorrect_sentences.append(incorrect_sentence)

df = pd.DataFrame({
    'correct': correct_sentences,
    'incorrect': incorrect_sentences
})

df.to_csv("polblimp.csv", index=False)
