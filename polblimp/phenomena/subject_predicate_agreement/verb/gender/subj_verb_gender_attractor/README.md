# subj_verb_gender_attractor
The predicate must agree with its subject in gender.

Queries for this paradigm are split into two categories:
- main verb
- copular verb.

To create the ungrammatical sentence change the gender of:
- the main verb (\$root) or
- the copular verb.

## Examples

```
 W biurze rajdu kolejka kierowców topniała w oczach.
*W biurze rajdu kolejka kierowców topniał w oczach.

 Większość kraju tonęła jednak w ciemności.
*Większość kraju tonął jednak w ciemności.

 Zaledwie połowa miejsc była zajęta.
*Zaledwie połowa miejsc było zajęta.

 Ale teraz jego profil na ścianie przypominał złośliwe rysunki.
*Ale teraz jego profil na ścianie przypominała złośliwe rysunki.
```

## Queries

 1. Main verb
```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel = 'nsubj',
    member iset [
      gender = $root.iset/gender
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],

    # attractor between the subject and the verb
    child a-node $attractor := [
      tag = 'NOUN',

      # relational noun OR PP attractor
      deprel in {'nmod', 'nmod:poss', 'nmod:arg'},
      (
        ($root.iset/number = 'sing' and $attractor.iset/gender != $root.iset/gender)
        or
        ($root.iset/number = 'plur' and (($nsubj.conll/feat ~ 'SubGender=Masc1' and $attractor.conll/feat !~ 'SubGender=Masc1') or ($nsubj.conll/feat ~ 'Animacy=Hum' and $attractor.conll/feat !~'Animacy=Hum')))
        or
        ($root.iset/number = 'plur' and (($nsubj.conll/feat !~ 'SubGender=Masc1' and $attractor.conll/feat ~ 'SubGender=Masc1') or ($nsubj.conll/feat !~ 'Animacy=Hum' and $attractor.conll/feat ~'Animacy=Hum')))
      ),

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
    
    0x descendant $att := [
      deprel in {'nmod', 'nmod:poss', 'nmod:arg', 'xcomp', 'nummod', 'conj'},
      (
        ($root.iset/number = 'sing' and $att.iset/gender != $attractor.iset/gender)
        or
        ($root.iset/number = 'plur' and (($attractor.conll/feat ~ 'SubGender=Masc1' and $att.conll/feat !~ 'SubGender=Masc1') or ($attractor.conll/feat ~ 'Animacy=Hum' and $att.conll/feat !~'Animacy=Hum')))
        or
        ($root.iset/number = 'plur' and (($nsubj.conll/feat !~ 'SubGender=Masc1' and $att.conll/feat ~ 'SubGender=Masc1') or ($nsubj.conll/feat !~ 'Animacy=Hum' and $att.conll/feat ~'Animacy=Hum')))
      ),

      (
        ($attractor.ord < ord and ord < $root.ord)
        or
        ($root.ord < ord and ord < $attractor.ord)
      )
    ]
  ],
# for generating pairs 
  (
    # i. singular - change the gender of $root to that of $attractor
    ($root.iset/number = 'sing')
     or
    # ii. plural, masculine personal - change the subgender (LFG) or the animacy (PDB) of $root (mp → nmp)
    ($root.iset/number = 'plur' and ($nsubj.conll/feat ~ 'SubGender=Masc1' or $nsubj.conll/feat ~ 'Animacy=Hum'))
    or
    # iii. plural, non-masculine-personal - change the subgender (LFG) or the animacy (PDB) of $root (nmp → mp)
    ($root.iset/number = 'plur' and ($nsubj.conll/feat !~ 'SubGender=Masc1' and $nsubj.conll/feat !~ 'Animacy=Hum'))
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
      gender = $cop.iset/gender
    ],

    # no conjunct subject (anywhere)
    0x child [deprel = 'conj'],
    
    # attractor between the subject and the verb
    child a-node $attractor := [
      tag = 'NOUN',

      # relational noun OR PP attractor
      deprel in {'nmod', 'nmod:poss', 'nmod:arg'},
      
      member iset [
        gender != ''
      ],
      
      (
        ($cop.iset/number = 'sing' and $attractor.iset/gender != $cop.iset/gender)
        or
        ($cop.iset/number = 'plur' and (($nsubj.conll/feat ~ 'SubGender=Masc1' and $attractor.conll/feat !~ 'SubGender=Masc1') or ($nsubj.conll/feat ~ 'Animacy=Hum' and $attractor.conll/feat !~'Animacy=Hum')))
        or
        ($cop.iset/number = 'plur' and (($nsubj.conll/feat !~ 'SubGender=Masc1' and $attractor.conll/feat ~ 'SubGender=Masc1') or ($nsubj.conll/feat !~ 'Animacy=Hum' and $attractor.conll/feat ~'Animacy=Hum')))
      ),

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
      (
        ($cop.iset/number = 'sing' and iset/gender != $attractor.iset/gender)
        or
        ($cop.iset/number = 'plur' and ((conll/feat ~ 'SubGender=Masc1' and $attractor.conll/feat !~ 'SubGender=Masc1') or (conll/feat ~ 'Animacy=Hum' and $attractor.conll/feat !~'Animacy=Hum')))
        or
        ($cop.iset/number = 'plur' and ((conll/feat !~ 'SubGender=Masc1' and $attractor.conll/feat ~ 'SubGender=Masc1') or (conll/feat !~ 'Animacy=Hum' and $attractor.conll/feat ~'Animacy=Hum')))
      ),
      (
        ($attractor.ord < ord and ord < $cop.ord)
        or
        ($cop.ord < ord and ord < $attractor.ord)
      )
    ]
  ],
  
# for generating pairs 
  (
    # i. singular - change the gender of $cop to that of $attractor
    ($cop.iset/number = 'sing')
     or
    # ii. plural, masculine personal - change the subgender (LFG) or the animacy (PDB) of $cop (mp → nmp)
    ($cop.iset/number = 'plur' and ($nsubj.conll/feat ~ 'SubGender=Masc1' or $nsubj.conll/feat ~ 'Animacy=Hum'))
    or
    # iii. plural, non-masculine-personal - change the subgender (LFG) or the animacy (PDB) of $cop (nmp → mp)
    ($cop.iset/number = 'plur' and ($nsubj.conll/feat !~ 'SubGender=Masc1' and $nsubj.conll/feat !~ 'Animacy=Hum'))
  )
]
```

## Notes
UD 2.18 results:  

1:  
 LFG: 73 + 7,  
 PDB: 122 + 48

2:  
 LFG: 7 + 0,  
 PDB: 23 + 13

 
(deprel = root + deprel != root)  
