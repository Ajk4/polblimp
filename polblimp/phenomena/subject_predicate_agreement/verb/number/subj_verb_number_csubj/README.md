# subj_verb_number_csubj
The default for clausal and infinitival subjects (csubj) is 3rd person singular neuter.

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
  deprel = 'root',
  member iset [number = 'sing'],

  child a-node $csubj := [
    tag = 'VERB',
    deprel ~ 'subj'
  ]
]
```
2. Copular auxiliary verb
```
a-node $root := [
  tag != 'VERB',
  deprel = 'root',
  
  child a-node $csubj := [
    tag = 'VERB',
    deprel ~ 'subj',
  ],

  child a-node $cop :=[ 
    tag = 'AUX',
    lemma !in {'to', 'by'},
  ]
]
```
## Notes
UD 2.18 results:  
1:  
 LFG: 93 + 13,  
 PDB: 92 + 40

2:  
 LFG: 6 + 1,  
 PDB: 15 + 18
 
 (deprel = root + deprel != root)  