# subj_verb_person_simple
The verb must agree with the subject in person.  

This paradigm covers both:
- verbal predicates, where person is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where person is expressed on the copula.

To create the ungrammatical sentence:
- change the person of the main verb (\$root) or
- change the person of the copular verb (\$cop).

## Examples

```
 Jak my będziemy wyglądać w ich wieku?
*Jak my będziecie wyglądać w ich wieku?

 Ale była to już zupełnie inna opowieść.
*Ale byłam to już zupełnie inna opowieść.
```

## Queries

1. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel = 'nsubj',
    member iset [case != 'gen'] # subject in genitive is covered by a different paradigm
  ],
  
# For generating pairs
  (
    # i) In present and future tense, change the person of $root
    ($root.iset/tense in{'pres', 'fut'} and $root.iset/person in{'1', '2', '3'})
    or
    # ii) In past tense (or lemma 'powinien'), 1st and 2nd person, change the person of $auxclitic or remove this node 
    (($root.iset/tense = 'past' or $root.lemma = 'powinien') and child a-node $auxclitic := [deprel = 'aux:clitic'] and $nsubj.iset/person in{'1', '2'})
    or
    # iii) In past tense (or lemma 'powinien'), 3rd person, a suffix must be added to $root
    (($root.iset/tense = 'past' or $root.lemma = 'powinien') and $nsubj.iset/person !in {'1', '2'} and 0x child [deprel = 'aux'])
    or
    # iv) In future compound, change the person of $aux
    (child a-node $aux := [deprel = 'aux'] and $root.lemma != 'to')
  )
]
```
2. Copular auxiliary verb
```
a-node $root := [
  tag != 'VERB' or 
  lemma = 'to',
  deprel = 'root',

  child a-node $nsubj := [
    deprel in {'nsubj', 'nsubj:pass'}, 
    member iset [ case != 'gen'],
    ],

  child a-node $cop :=[ 
    tag = 'AUX',
    lemma !in {'to', 'by'},
  ],

# For generating pairs
    (
    # i) In present and future tense, change the person of $cop
    ($cop.iset/tense in{'pres', 'fut'})
    or
    # ii) In past tense, 1st and 2nd person, change the person of $auxclitic or remove this node
    ($cop.iset/tense = 'past' and child a-node $auxclitic := [deprel = 'aux:clitic'] and $nsubj.iset/person in{'1', '2'})
    or
    # iii) In past tense, 3rd person, a suffix must be added to $cop
    (($cop.iset/tense = 'past') and $nsubj.iset/person !in{'1', '2'})
  )
]
```

## Notes
UD 2.18 results:  
1:  
 LFG: 7018 + 1067,  
 PDB: 10000+(result limit) + 6320

2:  
 LFG: 1075 + 159,  
 PDB: 1581 + 1279

 (deprel = root + deprel != root)  