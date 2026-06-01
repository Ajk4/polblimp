# subj_verb_number_numerals
Numerals from 1 to 4 combine with the noun in nominative and the verb agrees with the noun in number.*

Numerals from 5 upwards and quantifiers combine with genitive, the default for the verb is 3rd person singular neuter.  

*With numerals from 1 to 4, masculine nouns can appear in both nominative and genitive, depending on the case of the numeral (numeral in nominative + nominative, numeral in accusative + genitive).

This paradigm covers both:

- verbal predicates, where number is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where number is expressed on the copula.

To create the ungrammatical sentence change the number of:  
- the main verb (\$root) or
- the auxiliary verb (\$aux) (compound future tense, the verb in infinitive) or
- both the auxiliary and the main verb (compound future tense, the verb in finite form) or
- the copular verb (\$cop).

## Examples
```
 423 razy spotkały się cztery rządowe komitety.
*423 razy spotkało się cztery rządowe komitety.

 Dopiero wtedy oba ugrupowania będą mogły mówić o pełnym wyborczym sukcesie.
*Dopiero wtedy oba ugrupowania będzie mogło mówić o pełnym wyborczym sukcesie.

 W tamtejszych lasach jest dużo dzikich zwierząt.
*W tamtejszych lasach są dużo dzikich zwierząt.
```

## Queries

1. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
 
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
    # i. In present, future simple and past tense, change the number of $root
    ($root.iset/tense in{'pres', 'fut', 'past'}
      and
        # check if the sentences are annotated correctly
      (($root.iset/number = 'sing' and $nsubj.iset/case = 'gen')
         or
       ($root.iset/number = 'plur' and $nsubj.iset/case = 'nom'))
    )
    
    or
    
    # ii. In compound future tense, main verb in infinitive: change the number of $aux
    ($root.lemma != 'to' and $root.iset/verbform != 'fin'
      and child a-node $aux1 := [
            deprel = 'aux', 
            # check if the sentences are annotated correctly (number of $aux1)
            ((iset/number = 'sing' and $nsubj.iset/case = 'gen')
              or
             (iset/number = 'plur' and $nsubj.iset/case = 'nom'))
            ] 
    )
    
    or
    
    # iii. In compound future tense, finite main verb: change the number of $aux and $root
    ($root.lemma != 'to' and $root.iset/verbform = 'fin'
      and child a-node $aux2 := [
            deprel = 'aux', 
            # check if the sentences are annotated correctly (number of $aux2)
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
  deprel = 'root',
  
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
  ],
  
  # check if the sentences are annotated correctly
  ($cop.iset/number = 'sing' and $nsubj.iset/case = 'gen')
  or
  ($cop.iset/number = 'plur' and $nsubj.iset/case = 'nom')
]
```

## Notes
The results are the same as for the subj_verb_person_numerals paradigm. The only difference in the queries lies in the pair generation conditions.

UD 2.18 results:

1:  
 LFG: 209 + 19,  
 PDB: 636 + 150

2:  
 LFG: 25 + 2,  
 PDB: 11 + 12
 
 (deprel = root + deprel != root)  

