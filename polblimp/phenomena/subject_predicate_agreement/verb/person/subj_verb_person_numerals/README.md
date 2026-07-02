# subj_verb_person_numerals
With numerals and quantifiers in the subject, the verb appears in 3rd person.

This paradigm covers both:
- verbal predicates, where person is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where person is expressed on the copula.

To create the ungrammatical sentence change the person of:  
- the main verb (\$root) or
- the auxiliary verb (\$aux) (compound future tense) or
- the copular verb (\$cop).

## Examples
```
 Choć może będzie więcej deszczowych dni.
*Choć może będziesz więcej deszczowych dni.

 Dopiero wtedy oba ugrupowania będą mogły mówić o pełnym wyborczym sukcesie.
*Dopiero wtedy oba ugrupowania będziemy mogły mówić o pełnym wyborczym sukcesie.

 Ci dwaj byli na siebie specjalnie uczuleni.
*Ci dwaj byliśmy na siebie specjalnie uczuleni.
```

## Queries

1. Main verb
```
a-node $root := [
  tag = 'VERB',
 
  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',
    
    child a-node $num := [
    tag = 'NUM'
    or 
    (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel ~ 'det')
    ],
  ],

# For generating pairs
(   
  (
    (
      # i. In present and future tense, change the person of $root
      ($root.iset/tense in{'pres', 'fut'} and $root.iset/person = '3')
      or
      # ii. In past tense (or lemma 'powinien'), a suffix must be added to $root
      (($root.iset/tense = 'past' or $root.lemma = 'powinien') and 0x child [deprel = 'aux'])
    )
    and

    # check if the sentences are annotated correctly
    (
      ($root.iset/number = 'sing' and $nsubj.iset/case = 'gen')
      or
      ($root.iset/number = 'plur' and $nsubj.iset/case = 'nom')
    )
  )
      
  or
    
  # iii. In compound future tense, change the person of $aux
    ($root.lemma != 'to' 
    and
      child a-node $aux := [
      deprel = 'aux',

      # check if the sentences are annotated correctly (number of $aux1)
      ((iset/number = 'sing' and $nsubj.iset/case = 'gen')
        or
       (iset/number = 'plur' and $nsubj.iset/case = 'nom'))
      ] 
    )
 )
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
    (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel = 'det')
    ],
  ],

  child a-node $cop :=[ 
    tag = 'AUX',
    # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
  ],
  
  # check if the sentences are annotated correctly
  (
    ($cop.iset/number = 'sing' and $nsubj.iset/case = 'gen')
    or
    ($cop.iset/number = 'plur' and $nsubj.iset/case = 'nom')
  ),

  # For generating pairs
  (
    # i. In present and future tense, change the person of $cop
    ($cop.iset/tense in{'pres', 'fut'})
    or
    # ii. In past tense, a suffix must be added to $cop
    ($cop.iset/tense = 'past')
  )
]
```
## Notes
The results are the same as for the subj_verb_number_numerals paradigm. The only difference in the queries lies in the pair generation conditions.

UD 2.18 results:

1:  
 LFG: 209 + 19,  
 PDB: 636 + 150

2:  
 LFG: 25 + 2,  
 PDB: 11 + 12
 
 (deprel = root + deprel != root)  
 Removed the 'root' constraint. Fixed a typo - it was deprel = 'det', now it is deprel ~ 'det'