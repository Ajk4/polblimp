# subj_adjectival_case
Adjectival predicates must agree with the noun in case.

To create the ungrammatical sentence change the case of the adjective (\$root):
- from genitive to nominative,
- from nominative to genitive.

## Examples

```
 Aż w końcu podział ten został przezwyciężony.
*Aż w końcu podział ten został przezwyciężonego.

 W powiecie puławskim kilka wiosek będzie kompleksowo zadrzewianych.
*W powiecie puławskim kilka wiosek będzie kompleksowo zadrzewiane.
```

## Query

```
a-node $root := [
  tag = 'ADJ',
  deprel = 'root',
  
  child a-node $nsubj := [
    deprel in {'nsubj', 'nsubj:pass'},
    ],

  child a-node $cop :=[ 
    tag = 'AUX',
    # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
  ]
]
```
## Notes
Query is identical to the one used for subj_adjectival_number.

UD 2.18 results:  

 LFG: 523 + 80,  
 PDB: 1127 + 936
 
 (deprel = root + deprel != root)  