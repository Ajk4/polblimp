# subj_pred_person_csubj

The default for csubj is 3 singular neuter.
Change the person of $cop.

## Examples

```
Chociaż faktem jest, że Hubal okropnie przeżył te zdarzenia.
*Chociaż faktem jesteś, że Hubal okropnie przeżył te zdarzenia.
```

## Query

```
a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $clausal := [
    tag = 'VERB',
    deprel = 'csubj',
  ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]
```
