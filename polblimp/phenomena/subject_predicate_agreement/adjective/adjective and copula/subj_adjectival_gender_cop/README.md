# subj_adjectival_gender_cop
For adjectival predicates both the adjective and the copula must agree with the noun in gender.

To create the ungrammatical sentence change the gender of the adjective (\$root) and of the copular verb (\$cop). Only consider subjects (\$nsubj) in nominative, as adjectives in genitive have the same form for each gender.

## Example

```
Aż w końcu podział ten został przezwyciężony.
*Aż w końcu podział ten została przezwyciężona.
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
    # past tense for the copula to have gender
    member iset[tense = 'past']
  ]
]
```

## Notes

UD 2.18 results:  

 LFG: 230 + 29,  
 PDB: 342 + 274
 
 (deprel = root + deprel != root)  
