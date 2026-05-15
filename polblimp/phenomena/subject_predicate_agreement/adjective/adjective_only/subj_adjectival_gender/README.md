# subj_adjectival_gender

Change the gender of $root. Only consider nsubj in nominative, as adjectives in genitive have the same form for each gender.

## Example

```
Aż w końcu podział ten został przezwyciężony.
*Aż w końcu podział ten został przezwyciężona.
```

## Query

```
a-node $root := [
  tag = 'ADJ',
  deprel = 'root',
  
  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    member iset [case = 'nom'], #the only difference here
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],

  child a-node $cop :=[ 
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]
```

## Notes

PDB query viewer - https://lindat.mff.cuni.cz/services/pmltq/?query=pdb#!/treebank/udpl_pdb217/query/IYWgdg9gJgpgBAEgE4QgFzgLgLxwNoBQccawA5nLgOQCCAIgFJUA0RcsADkjADaVxUU6FmzYBjABYBLHlDihIsRGADOAVwBGAKyy5CxYp258AfgIB6AClWatAHxvbMHYCpUBKBCINwAtjF8NGCQ4KRUYDDwxV3hqSF8qAF1mOABiNAl4CDAeAE92KQAzQuCYMDF4TO42YgAGAA92GBUKsChgMEijXn4qMF9oKjgIEO6+OIGoZwg3KhGmrh7qerEIXw4h+bHe1bAtTdGYRfGBMDVfSaTWH2SCcWlZeXBoeARVjl08OBqScl6aACqAA1vAYAIQ8AK+YC9NAQUHECFQmHUDS5KhsRIELFAA/result/svg?filter=true&timeout=30&limit=10000
Results: 697 sentences
