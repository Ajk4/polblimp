# subj_verb_gender_genitive
With subject in genitive, the default for the verb is 3rd person singular neuter.

To create the ungrammatical sentence change the gender of the main verb (\$root).

## Example

```
 Ale króla kruków już nie było.
*Ale króla kruków już nie był.
```

## Query

```
a-node $root :=  [
  tag = 'VERB',
  deprel = 'root',
  member iset [
    number = 'sing',
    gender = 'neut'
  ],

  child a-node $nsubj :=[
  deprel = 'nsubj',
    member iset [ case = 'gen' ],
    # exclude numerals and quantifiers
    0x child [tag = 'NUM' or (lemma in {'kilka', 'kilkaset', 'kilkanaście', 'kilkadziesiąt', 'sporo', 'mnóstwo', 'dużo', 'wiele', 'więcej', 'najwięcej', 'większość', 'mało', 'mniej', 'najmniej', 'trochę', 'parę', 'niewiele', 'ile', 'tyle'} and deprel = 'det')
    ]
  ],
]
```
## Notes
UD 2.18 results:  

 LFG: 24 + 3,  
 PDB: 86 + 64

 
(deprel = root + deprel != root)  