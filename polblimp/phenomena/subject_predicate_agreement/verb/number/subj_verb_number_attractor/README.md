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

 1a. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel = 'nsubj',
    member iset [
      number = $root.iset/number
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],

    # attractor between the subject and the verb
    child a-node $attractor := [
      tag = 'NOUN',

      # relational noun OR PP attractor
      deprel in {'nmod', 'nmod:poss', 'nmod:arg'},

      member iset [
        number != $root.iset/number,
        number != ''
      ],

      (
        # relational noun attractor
        deprel in {'nmod:poss', 'nmod:arg'}

        or

        # PP attractor
        (
          deprel = 'nmod'

          and child a-node $prep := [
            tag = 'ADP',
            deprel = 'case',

            # avoid "z" + instrumental
            (
              (lemma = 'z' and $attractor.iset/case != 'ins')
              or
              (lemma != 'z')
            )
          ]
        )
      ),

      # attractor intervenes between subject and predicate
      (
        ($nsubj.ord < $attractor.ord and $attractor.ord < $root.ord)
        or
        ($root.ord < $attractor.ord and $attractor.ord < $nsubj.ord)
      )
    ],
    
    0x descendant [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      member iset [number = $root.iset/number],

      (
        ($attractor.ord < ord and ord < $root.ord)
        or
        ($root.ord < ord and ord < $attractor.ord)
      )
    ]
  ]
# For generating pairs change number of $root
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
    
    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],
    
    # attractor between the subject and the verb
    child a-node $attractor := [
      tag = 'NOUN',

      # relational noun OR PP attractor
      deprel in {'nmod', 'nmod:poss', 'nmod:arg'},

      member iset [
        number != $aux.iset/number,
        number != ''
      ],

      (
        # relational noun attractor
        deprel in {'nmod:poss', 'nmod:arg'}

        or

        # PP attractor
        (
          deprel = 'nmod'

          and child a-node $prep := [
            tag = 'ADP',
            deprel = 'case',

            # avoid "z" + instrumental
            (
              (lemma = 'z' and $attractor.iset/case != 'ins')
              or
              (lemma != 'z')
            )
          ]
        )
      ),

      # attractor intervenes between subject and auxiliary
      (
        ($nsubj.ord < $attractor.ord and $attractor.ord < $aux.ord)
        or
        ($aux.ord < $attractor.ord and $attractor.ord < $nsubj.ord)
      )
    ],
    
    0x descendant [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      member iset [number = $aux.iset/number],

      (
        ($attractor.ord < ord and ord < $aux.ord)
        or
        ($aux.ord < ord and ord < $attractor.ord)
      )
    ]
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
 2. Copular verb
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
    member iset [
      case = 'nom',
      number = $cop.iset/number
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],
    
    # attractor between the subject and the verb
    child a-node $attractor := [
      tag = 'NOUN',

      # relational noun OR PP attractor
      deprel in {'nmod', 'nmod:poss', 'nmod:arg'},

      member iset [
        number != $cop.iset/number,
        number != ''
      ],

      (
        # relational noun attractor
        deprel in {'nmod:poss', 'nmod:arg'}

        or

        # PP attractor
        (
          deprel = 'nmod'

          and child a-node $prep := [
            tag = 'ADP',
            deprel = 'case',

            # avoid "z" + instrumental
            (
              (lemma = 'z' and $attractor.iset/case != 'ins')
              or
              (lemma != 'z')
            )
          ]
        )
      ),

      # attractor intervenes between subject and auxilitary
      (
        ($nsubj.ord < $attractor.ord and $attractor.ord < $cop.ord)
        or
        ($cop.ord < $attractor.ord and $attractor.ord < $nsubj.ord)
      )
    ],
    
    0x descendant [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      member iset [number != $cop.iset/number],
      (
        ($attractor.ord < ord and ord < $cop.ord)
        or
        ($cop.ord < ord and ord < $attractor.ord)
      )
    ]
  ]
# For generating pairs change number of $cop
]
```

## Notes
UD 2.18 results:  

1a:  
 LFG: 97 + 11,  
 PDB: 362 + 90

1b:  
 LFG: 1 + 1,  
 PDB: 9 + 2

2:  
 LFG: 11 + 1,  
 PDB: 67 + 39

 
(deprel = root + deprel != root)  
