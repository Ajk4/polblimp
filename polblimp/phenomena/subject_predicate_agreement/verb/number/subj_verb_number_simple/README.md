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

 1. Main verb
```
a-node $root := [
  tag = 'VERB',

  child a-node $nsubj := [
    deprel = 'nsubj',
    member iset [
      number = $root.iset/number,
      case != 'gen'
    ],

    # no attractors between subject and verb
    0x descendant [
      (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),
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
 2. Main verb, compound future
```
a-node $root := [
  tag = 'VERB',
  lemma != 'to',
  
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
      (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),
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
 3. Copular verb
```
a-node $root := [
  tag != 'VERB' or 
  lemma = 'to',
  
  child a-node $cop :=[ 
    tag = 'AUX',
    lemma !in {'to', 'by'} # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    ],
  
  child a-node $nsubj := [
    deprel in {'nsubj', 'nsubj:pass'}, 
    member iset [ case = 'nom' ],
    
    # no attractors (of different number) between subject and verb
    0x descendant [
      (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),
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
    # change the number of $cop
    ($nsubj.iset/person !in{'1', '2'}) or ($nsubj.iset/person in{'1', '2'} and $cop.iset/tense in{'pres', 'fut'})
    or
    # 1st and 2nd person, past tense: change the number of $auxclitic and of $cop 
    ($cop.iset/tense = 'past' and $nsubj.iset/person in{'1', '2'} and child a-node $auxclitic := [deprel = 'aux:clitic'])
    ) 
]
```

## Notes
UD 2.18 results:  

1:  
 LFG: 6560 + 1007,  
 PDB: 9032 + 5648

2:  
 LFG: 68 + 11,  
 PDB: 149 + 138

3:  
 LFG: 1020 + 153,  
 PDB: 1257 + 1109

 
(deprel = root + deprel != root)  
Removed the 'root' constraint.

Changed the way we search for attractors.
