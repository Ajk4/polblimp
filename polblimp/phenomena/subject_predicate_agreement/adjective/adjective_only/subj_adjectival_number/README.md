# subj_adjectival_number

Change the number of $root.

## Examples

```
Aż w końcu podział ten został przezwyciężony.
*Aż w końcu podział ten został przezwyciężone.

W powiecie puławskim kilka wiosek będzie kompleksowo zadrzewianych.
*W powiecie puławskim kilka wiosek będzie kompleksowo zadrzewianej.
```

## Query

```
a-node $root := [
  tag = 'ADJ',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]
```
