# subj_adjectival_gender
Adjectival predicates must agree with the noun in gender.

To create the ungrammatical sentence change the gender of the adjective (\$root). Only consider subjects (\$nsubj) in nominative, as adjectives in genitive have the same form for each gender.

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
    deprel in {'nsubj', 'nsubj:pass'},
    member iset [
      case = 'nom', 
      person !in{'1', '2'} # pronouns (ja, ty, my, wy) do not carry gender
      ], 
    ],

  child a-node $cop :=[ 
    tag = 'AUX',
    # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
  ]
]
```

## Notes

UD 2.18 results:  

 LFG: 504 + 79,  
 PDB: 1112 + 913
 
 (deprel = root + deprel != root)  
