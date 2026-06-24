# subj_verb_gender_csubj
With clausal and infinitival subjects (csubj) the default for the verb is 3rd person singular neuter.

This paradigm covers both:

- verbal predicates, where gender is expressed directly on the finite verb,
- non-verbal predicates with a copular construction, where gender is expressed on the copula.

To create the ungrammatical sentence change the gender of:
- the main verb (\$root) or
- the copular verb (\$cop).

## Examples

```
 I okazało się, że doniósł.
*I okazał się, że doniósł.

 Wymknęło ci się, że przesadą byłoby zginąć za komunizm.
*Wymknęła ci się, że przesadą byłoby zginąć za komunizm.

```

## Queries

1. Main verb
```
a-node $root := [
  tag = 'VERB',
  member iset [
    number = 'sing',
    gender = 'neut' 
  ],   

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
    # exclude bare copular 'to' 
    # and avoid duplicate matches with forms such as 'byłby'
    lemma !in {'to', 'by'},
    member iset [
      number = 'sing',
      gender = 'neut']
  ]
]
```
## Notes
UD 2.18 results:  

1:  
 LFG: 48,  
 PDB: 48

2:  
 LFG: 1,  
 PDB: 9
 
Removed the 'root' constraint. Needed to exclude a child node with lemma 'kto'. The annotations are wrong and the verb labeled as 'csubj' is not actually a csubj.
