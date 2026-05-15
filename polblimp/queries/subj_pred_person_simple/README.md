# subj_pred_person_simple

## Query

```
a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to', # aby nie wyszukiwać zdań, gdzie jest jedynie cop ‘to’, przy okazji nie wyszukuje podwójnie zdań typu ‘to jest’
    !lemma = 'by' # aby nie wyszukiwać podwójnie zdań zawierających np. ‘byłby’
  ]
]
```
