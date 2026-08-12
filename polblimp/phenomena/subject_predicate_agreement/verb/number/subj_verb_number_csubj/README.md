# subj_verb_number_csubj
With clausal and infinitival subjects (csubj) the default for the verb is 3rd person singular neuter.

This paradigm covers both:

- verbal predicates, where number is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where number is expressed on the copula.

To create the ungrammatical sentence:
- change the number of the main verb (\$root) or
- change the number of the copular verb (\$cop).

## Examples

```
 I okazało się, że doniósł.
*I okazały się, że doniósł.

 Chociaż faktem jest, że Hubal okropnie przeżył te zdarzenia.
*Chociaż faktem są, że Hubal okropnie przeżył te zdarzenia.
```

## Queries

1. Main verb
```
a-node $root := [
  tag = 'VERB',
  member iset [number = 'sing'],

  child a-node $csubj := [
    tag = 'VERB',
    deprel ~ 'subj',
    # exclude sentences with lemma 'kto' - incorrect annotations
    0x child [lemma  = 'kto']
  ]
]
```
2. Copular auxiliary verb
```
a-node $root := [
  tag != 'VERB',
  
  child a-node $csubj := [
    tag = 'VERB',
    deprel ~ 'subj',
    # exclude sentences with lemma 'kto' - incorrect annotations
    0x child [lemma  = 'kto']
  ],

  child a-node $cop :=[ 
    tag = 'AUX',
    # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by', 'niech'},
  ]
]
```
## Notes
Queries are identical to those used for subj_verb_person_csubj.

UD 2.18 results:  
1:  
 LFG: 105,  
 PDB: 127

2:  
 LFG: 7,  
 PDB: 32
 
 Removed the 'root' constraint. Needed to exclude a child node with lemma 'kto'. The annotations are wrong and the verb labeled as 'csubj' is not actually a csubj. 
