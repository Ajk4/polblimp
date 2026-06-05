# subj_verb_gender_simple
The predicate must agree with its subject in gender. In Polish language there are 3 genders in singular (masculine, feminine, neuter) and 2 genders in plural (masculine personal, non-masculine personal).

This paradigm covers both:
- verbal predicates, where gender is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where gender is expressed on the copula.

To create the ungrammatical sentence change the gender of:  
- the main verb (\$root) or
- the copular verb (\$cop).

## Examples

```
 A pan poseł powiedział, że nie chce Polski zaściankowej.
*A pan poseł powiedziała, że nie chce Polski zaściankowej.

 A nowe, dwupokojowe mieszkanko otrzymali państwo Sknerowie.
*A nowe, dwupokojowe mieszkanko otrzymały państwo Sknerowie.

 Dostawy nie zmniejszyły się również w bieżącym miesiącu.
*Dostawy nie zmniejszyli się również w bieżącym miesiącu.

```

## Queries

 1. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  member iset [
    number in {'sing', 'plur'} 
  ],
  

  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',
    member iset [
      gender = $root.iset/gender,
      number = $root.iset/number
    ],
    
    # no attractors between subject and verb
    0x descendant $att := [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'conj', 'nummod'},
      (
        ($root.iset/number = 'sing' and $att.iset/gender != $root.iset/gender)
        or
        ($root.iset/number = 'plur' and (($nsubj.conll/feat ~ 'SubGender=Masc1' and $att.conll/feat !~ 'SubGender=Masc1') or ($nsubj.conll/feat ~ 'Animacy=Hum' and $att.conll/feat !~'Animacy=Hum')))
        or
        ($root.iset/number = 'plur' and (($nsubj.conll/feat !~ 'SubGender=Masc1' and $att.conll/feat ~ 'SubGender=Masc1') or ($nsubj.conll/feat !~ 'Animacy=Hum' and $att.conll/feat ~'Animacy=Hum')))
      ),

      (
        ($nsubj.ord < ord and ord < $root.ord)
        or
        ($root.ord < ord and ord < $nsubj.ord)
      )
    ],
    
# for generating pairs 
  (
    # i. singular - change the gender of $root
    ($root.iset/number = 'sing')
     or
    # ii. plural, masculine personal - change the subgender (LFG) or the animacy (PDB) of $root (mp → nmp)
    ($root.iset/number = 'plur' and ($nsubj.conll/feat ~ 'SubGender=Masc1' or $nsubj.conll/feat ~ 'Animacy=Hum'))
    or
    # iii. plural, masculine personal - change the subgender (LFG) or the animacy (PDB) of $root (nmp → mp)
    ($root.iset/number = 'plur' and ($nsubj.conll/feat !~ 'SubGender=Masc1' or $nsubj.conll/feat !~ 'Animacy=Hum'))
  ),
  ]
]

```
2. Copular verb

```

```

## Notes
UD 2.18 results:  

1:  
 LFG: 2264 + 347,  
 PDB: 2550 + 1404

2:  
 LFG:  
 PDB: 

 
(deprel = root + deprel != root)  
