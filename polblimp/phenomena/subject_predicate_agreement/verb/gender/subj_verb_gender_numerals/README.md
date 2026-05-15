# subj_verb_gender_numerals

Change the gender of $root:
from neut to the gender of $nsubj,
from any other to neut.

## Query

```
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  member iset[gender in {'masc', 'fem', 'neut'}], # check gender

  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',

    child a-node $num := [
    tag = 'NUM',
    ],

# check for gender (if the sentences are annotated correctly)
  ($root.iset/gender = "neut" and $nsubj.iset/case = 'gen' and $num.iset/case = 'acc')
  or
  ($root.iset/gender = $nsubj.iset/gender and !($nsubj.iset/case = 'gen' and $num.iset/case = 'acc'))

  ]
]
```
