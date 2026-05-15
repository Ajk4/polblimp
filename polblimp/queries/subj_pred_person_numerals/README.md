Change the person of $cop.

Examples:
 Ci dwaj byli na siebie specjalnie uczuleni.
*Ci dwaj byliśmy na siebie specjalnie uczuleni.

 jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanych.
*jestem na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanych.

Query:
a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',

    child a-node $num := [
    tag = 'NUM',
    ],
  ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]
