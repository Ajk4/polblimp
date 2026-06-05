# subj_verb_number_simple
The predicate must agree with its subject in number.

Queries for this paradigm are split into three categories:
- main verb - past, present, future simple,
- main verb - compound future,
- copular verb.

To create the ungrammatical sentence change the number of:
- the main verb (\$root) or
- the auxiliary verb (\$aux) or both the auxiliary and the main verb or
- the copular verb.

## Examples

```
 A pan poseł powiedział, że nie chce Polski zaściankowej.
*A pan poseł powiedzieli, że nie chce Polski zaściankowej.

 Jak my będziemy wyglądać w ich wieku?
*Jak my będę wyglądać w ich wieku?

 Powiat będzie spłacał obligacje przez następnych 18 lat.
*Powiat będą spłacali obligacje przez następnych 18 lat.

 Był przy niej także syn.
*Byli przy niej także syn.

```

## Queries

 1a. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel = 'nsubj',
    member iset [
      number = $root.iset/number,
      case != 'gen'
    ],

    # no attractors between subject and verb
    0x descendant [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      member iset [number != $root.iset/number],

      (
        ($nsubj.ord < ord and ord < $root.ord)
        or
        ($root.ord < ord and ord < $nsubj.ord)
      )
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],
  ],

# For generating pairs
  (
    # 3rd person: change the number of $root
    ($nsubj.iset/person !in{'1', '2'})
    or
    # 1st and 2nd person, present and future tense: change the number of $root
    ($root.iset/tense in{'pres', 'fut'} and $nsubj.iset/person in{'1', '2'})
    or
    # 1st and 2nd person, past tense: change the number of $auxclitic and of $root 
    (($root.iset/tense = 'past' or $root.lemma = 'powinien') and $nsubj.iset/person in{'1', '2'} and child a-node $auxclitic := [deprel = 'aux:clitic'])
  )
]
```
 1b. Main verb, compound future
```
a-node $root := [
  tag = 'VERB',
  lemma != 'to',
  deprel = 'root',
  
  child a-node $aux :=  [
    deprel = 'aux'],

  
  child a-node $nsubj := [
    deprel = 'nsubj',
    member iset [
      number = $aux.iset/number,
      case != 'gen'
    ],

    
    # no attractors (of different number) between subject and verb
    0x descendant [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      member iset [number != $aux.iset/number],

      (
        ($nsubj.ord < ord and ord < $aux.ord)
        or
        ($aux.ord < ord and ord < $nsubj.ord)
      )
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],

  ],
  
# For generating pairs
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
  tag != 'VERB' or 
  lemma = 'to',
  deprel = 'root',
  
  child a-node $cop :=[ 
    tag = 'AUX',
    lemma !in {'to', 'by'} # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    ],
  
  child a-node $nsubj := [
    deprel in {'nsubj', 'nsubj:pass'}, 
    member iset [ case = 'nom' ],
    
    # no attractors (of different number) between subject and verb
    0x descendant [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      member iset [number != $cop.iset/number],
      (
        ($nsubj.ord < ord and ord < $cop.ord)
        or
        ($cop.ord < ord and ord < $nsubj.ord)
      )
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],
  ],
  
# For generating pairs
    (
    # 3rd person: change the number of $cop
    ($nsubj.iset/person !in{'1', '2'})
    or
    # 1st and 2nd person, present and future tense: change the number of $cop
    ($cop.iset/tense in{'pres', 'fut'} and $nsubj.iset/person in{'1', '2'})
    or
    # 1st and 2nd person, past tense: change the number of $auxclitic and of $cop 
    ($cop.iset/tense = 'past' and $nsubj.iset/person in{'1', '2'} and child a-node $auxclitic := [deprel = 'aux:clitic'])
    ) 
]
```

## Notes
UD 2.18 results:  

1a:  
 LFG: 6570 + 1009,  
 PDB: 9131 + 5721

1b:  
 LFG: 69 + 11,  
 PDB: 154 + 139

2:  
 LFG: 1025 + 153,  
 PDB: 1278 + 1118

 
(deprel = root + deprel != root)  
