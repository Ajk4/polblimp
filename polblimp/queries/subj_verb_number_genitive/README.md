# subj_verb_number_genitive

Change the number of $root.

## Query

```
a-node $root :=  [
  deprel = 'root',
  tag = 'VERB',
  member iset [
    number = 'sing',
  ],

  child a-node $subj :=[
  deprel = 'nsubj',
    member iset [ case = 'gen' ],
  0x child [tag = 'NUM'] # if we dont want numerals
  ],
]
```
