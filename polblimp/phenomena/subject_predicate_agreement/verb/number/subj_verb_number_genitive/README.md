# subj_verb_number_genitive
With subject in genitive, the default for the verb is 3rd person singular neuter.

To create the ungrammatical sentence change the number of the main verb (\$root).

## Example

```
 Ale króla kruków już nie było.
*Ale króla kruków już nie były.
```


## Query

```
a-node $root :=  [
  tag = 'VERB',
  deprel = 'root',
  member iset [number = 'sing'],

  child a-node $subj :=[
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

 LFG: 78 + 15,  
 PDB: 241 + 197

 
(deprel = root + deprel != root)  
