# subj_verb_person_csubj
With clausal and infinitival subjects (csubj) the default for the verb is 3rd person singular neuter.

This paradigm covers both:

- verbal predicates, where person is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where person is expressed on the copula.

To create the ungrammatical sentence:
- change the person of the main verb (\$root) or
- change the person of the copular verb (\$cop).

## Examples

```
 I okazało się, że doniósł.
*I okazałeś się, że doniósł.

 Chociaż faktem jest, że Hubal okropnie przeżył te zdarzenia.
*Chociaż faktem jestem, że Hubal okropnie przeżył te zdarzenia.

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
    # exclude bare copular 'to' and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
  ]
]
```
## Notes
Queries are identical to those used for subj_verb_number_csubj.

UD 2.18 results:  
1:  
 LFG: 93 + 13,  
 PDB: 92 + 40

2:  
 LFG: 6 + 1,  
 PDB: 15 + 18
 
 (deprel = root + deprel != root)  