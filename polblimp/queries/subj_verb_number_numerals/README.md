# subj_verb_number_numerals

Change the number of $root.

## Query

```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  member iset[number in {'sing', 'plur'}], # check the number

  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',

    child a-node $num := [
    tag = 'NUM',
    ],

# check for number (if the sentences are annotated correctly)
  ($root.iset/number = 'sing' and $nsubj.iset/case = 'gen' and $num.iset/case = 'acc')
  or
  ($root.iset/number = 'plur' and !($nsubj.iset/case = 'gen' and $num.iset/case = 'acc'))

  ]
]
```
