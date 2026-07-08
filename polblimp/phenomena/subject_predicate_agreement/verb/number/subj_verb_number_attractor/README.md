# subj_verb_number_attractor
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
 Uśmiechnięta dziewczynka o jasnych włosach zjeżdża na zjeżdżalni.
*Uśmiechnięta dziewczynka o jasnych włosach zjeżdżają na zjeżdżalni.

 Faceci ze Wschodu siedzą spokojnie w poczekalni, gawędząc.
*Faceci ze Wschodu siedzi spokojnie w poczekalni, gawędząc.

 Liczba infuzji będzie zależeć od okoliczności związanych z chorobą pacjenta lub odpowiedzią na lek.
*Liczba infuzji będą zależeć od okoliczności związanych z chorobą pacjenta lub odpowiedzią na lek.

 Stan rannych jest stabilny.
*Stan rannych są stabilny.
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
    
    0x child [deprel = 'conj'],
    
    0x descendant [iset/case = 'ins', child a-node [lemma = 'z'], (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron'])]
  ],
  
  descendant a-node $attractor := [
    member iset [
      !number in{$nsubj.iset/number, ''},
      ($root.iset/number = 'sing' or number != 'ptan')
    ],
    (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),
      
    (
      ($nsubj.ord < ord and ord < $root.ord)
      or
      ($root.ord < ord and ord < $nsubj.ord)
    )
  ],
  
  0x descendant [
    (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),

    (
      ($attractor.ord < ord and ord < $root.ord)
      or
      ($root.ord < ord and ord < $attractor.ord)
    )
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
    
    0x child [deprel = 'conj'],
    
    0x descendant [iset/case = 'ins', child a-node [lemma = 'z'], (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron'])]
  ],
  
  descendant a-node $attractor := [
    member iset [
      !number in{$nsubj.iset/number, ''},
      ($aux.iset/number = 'sing' or number != 'ptan')
    ],
    (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),
      
    (
      ($nsubj.ord < ord and ord < $aux.ord)
      or
      ($aux.ord < ord and ord < $nsubj.ord)
    )
  ],
  
  0x descendant [
    (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),

    (
      ($attractor.ord < ord and ord < $aux.ord)
      or
      ($aux.ord < ord and ord < $attractor.ord)
    )
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
    member iset [
      case = 'nom',
      number = $cop.iset/number
    ],
    
    0x child [deprel = 'conj'],
    
    0x descendant [iset/case = 'ins', child a-node [lemma = 'z'], (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron'])]
  ],
  
  descendant a-node $attractor := [
    member iset [
      !number in{$nsubj.iset/number, ''},
      ($cop.iset/number = 'sing' or number != 'ptan')
    ],
    (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),
      
    (
      ($nsubj.ord < ord and ord < $cop.ord)
      or
      ($cop.ord < ord and ord < $nsubj.ord)
    )
  ],
  
  0x descendant [
    (member conll [pos ~ 'subst'] or member conll [pos ~ 'ppron']),

    (
      ($attractor.ord < ord and ord < $cop.ord)
      or
      ($cop.ord < ord and ord < $attractor.ord)
    )
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
 LFG: 481,  
 PDB: 1526

2:  
 LFG: 4,  
 PDB: 39

3:  
 LFG: 34,  
 PDB: 267
