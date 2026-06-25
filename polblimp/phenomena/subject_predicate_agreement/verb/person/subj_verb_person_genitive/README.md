# subj_verb_person_genitive
With subject in genitive, the default for the verb is 3rd person singular neuter.

To create the ungrammatical sentence change the person of the main verb (\$root).

## Example

```
 Ale króla kruków już nie było.
*Ale króla kruków już nie byłam.
```

## Query

```
a-node $root :=  [
  tag = 'VERB',

  child a-node $nsubj :=[
    deprel = 'nsubj',
    member iset [ case = 'gen' ],
    
    # exclude numerals and quantifiers
    0x child [tag = 'NUM' or (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel ~ 'det')
    ]
  ],

# For generating pairs
  ( 
   # i. In present and future tense, change the person of $root
    ($root.iset/tense in{'pres', 'fut'} and $root.iset/person ='3')
    or
   # ii. In past tense (or lemma 'powinien'), a suffix must be added to $root
    ($root.iset/tense = 'past' or $root.lemma = 'powinien')
  )
]
```

## Notes
UD 2.18 results:  

 LFG: 78 + 15 = 93,  
 PDB: 103 + 111 = 214

(deprel = root + deprel != root)  
Removed the 'root' constraint.