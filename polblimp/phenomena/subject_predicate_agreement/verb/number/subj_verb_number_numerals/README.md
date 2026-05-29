# subj_verb_number_numerals
Numerals from 1 to 4 combine with the noun in nominative and the verb agrees with the noun in plural number.*

Numerals from 5 upwards and quantifiers combine with genitive, the default for the verb is 3rd person singular neuter.  

*With numerals from 1 to 4, masculine nouns can be in both nominative and genitive, depending on the case of the numeral (numeral in nominative + nominative, numeral in accusative + genitive).

This paradigm covers both:

- verbal predicates, where number is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where number is expressed on the copula.

To create the ungrammatical sentence:
- change the number of the main verb ($root) or
- change the number of the copular verb (\$cop).


## Queries

1a. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  member iset[number in {'sing', 'plur'}], 
  
  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',
    
    child a-node $num := [
    tag = 'NUM'
    or 
    (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel = 'det')
    ],

# check if the sentences are annotated correctly
  ($root.iset/number = 'sing' and $nsubj.iset/case = 'gen')
  or
  ($root.iset/number = 'plur' and $nsubj.iset/case = 'nom')
  ]
]
```
1b. Main verb, compound future
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  lemma != 'to',

  child a-node $aux :=  [
    deprel = 'aux',
    member iset[
      number in {'sing', 'plur'}
      ]
    ],
    
  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',
    
    child a-node $num := [
    tag = 'NUM'
    or 
    (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel = 'det')
    ],
  ],
  
  # check if the sentences are annotated correctly
  ($aux.iset/number = 'sing' and $nsubj.iset/case = 'gen')
  or
  ($aux.iset/number = 'plur' and $nsubj.iset/case = 'nom')
  ,
  
  # for generating pairs
  (
    # infinitive: change the number of $aux
    $root.iset/verbform != 'fin'
    or
    # finite verb: change the number of $aux and $root
    $root.iset/verbform = 'fin'
  )
]

```
2\. Copular verb
```
a-node $root := [
  tag != 'VERB' or lemma = 'to',
  deprel = 'root',
  
  child a-node $nsubj := [
    deprel in {'nsubj', 'nsubj:pass'}, 
    
    child a-node $num := [
    tag = 'NUM'
    or 
    (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel = 'det')
    ],
  ],

  child a-node $cop :=[ 
    tag = 'AUX',
    # exclude bare copular 'to' 
    # and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
  ],
  
  # check if the sentences are annotated correctly
  ($cop.iset/number = 'sing' and $nsubj.iset/case = 'gen')
  or
  ($cop.iset/number = 'plur' and $nsubj.iset/case = 'nom')
]
```
## Notes
UD 2.18 results:

1a:  
 LFG: 208 + 19,  
 PDB: 504 + 74

1b:  
 LFG: 3 + 0,  
 PDB: 3 + 1

2:  
 LFG: 25 + 2,  
 PDB: 10 + 11
 
 (deprel = root + deprel != root)  

