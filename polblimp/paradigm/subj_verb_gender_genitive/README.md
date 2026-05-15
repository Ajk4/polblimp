# subj_verb_gender_genitive

Change the gender of $root.

## Query

```
a-node $root :=  [
  #lemma = 'być',
  deprel = 'root',
  tag = 'VERB',
  member iset [
    number = 'sing',
    gender = 'neut'
  ],

  child a-node $subj :=[
  deprel = 'nsubj',
    member iset [ case = 'gen' ],
  0x child [tag = 'NUM'] # if we dont want numerals
  ],
]
```
