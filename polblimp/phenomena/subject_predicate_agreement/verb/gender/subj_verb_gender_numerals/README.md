# subj_verb_gender_numerals
Numerals from 1 to 4 combine with the noun in nominative and the verb agrees with the noun in gender.*

Numerals from 5 upwards and quantifiers combine with genitive, the default for the verb is 3rd person singular neuter.  

*With numerals from 1 to 4, masculine nouns can appear in both nominative and genitive, depending on the case of the numeral (numeral in nominative + nominative, numeral in accusative + genitive).

This paradigm covers both:

- verbal predicates, where gender is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where gender is expressed on the copula.

To create the ungrammatical sentence change the gender of:  
- the main verb (\$root) (query 1) or
- the copular verb (\$cop) (query 2).

## Examples
```
 423 razy spotkały się cztery rządowe komitety.
*423 razy spotkali się cztery rządowe komitety.

 Było jeszcze w tym grubym tomie wiele uczonych spekulacji.
*Była jeszcze w tym grubym tomie wiele uczonych spekulacji.
```

## Queries

1. Main verb
```
a-node $root := [
  tag = 'VERB',

  member iset[
    gender in {'masc', 'fem', 'neut'}
    ],
 
  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',
    
    child a-node $num := [
      tag = 'NUM'
      or 
      (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel ~ 'det')
      ],
    ],

  # check for gender (if the sentences are annotated correctly)
  ($root.iset/number = 'sing' and $nsubj.iset/case = 'gen')
  or
  ($root.iset/number = 'plur' and $nsubj.iset/case = 'nom')
  ]
```
2. Copular verb
```
a-node $root := [
  tag != 'VERB' or lemma = 'to',
  
  child a-node $nsubj := [
    deprel in {'nsubj', 'nsubj:pass'}, 
    
    child a-node $num := [
    tag = 'NUM'
    or 
    (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel ~ 'det')
    ],
  ],

  child a-node $cop :=[ 
    tag = 'AUX',
    # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
    # only past tense results for gender
    member iset [tense ='past']
  ],

  # check for gender (if the sentences are annotated correctly)
  ($cop.iset/gender = 'neut' and $nsubj.iset/case = 'gen')
  or
  ($cop.iset/gender = $nsubj.iset/gender and $nsubj.iset/case = 'nom')
]
```
## Notes
UD 2.18 results:  

1:  
 LFG: 139 + 9,  
 PDB: 141 + 54

2:  
 LFG: 13 + 1,  
 PDB: 4 + 5
 
 (deprel = root + deprel != root)  
 Removed the 'root' constraint.