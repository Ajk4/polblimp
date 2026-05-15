subj_pred_number_numerals
With numerals <5, the copula agrees with the noun (plural and verb’s gender).
With numerals ≥5 (and for masculine <5 – in case of the numeral in accusative and noun in genitive), the default agreement is 3 singular neuter.

For small numerals (nsubj in nominative): Change the number of $cop and if $root is an adjective –  the number of $root.
For large numerals (nsubj in genitive): Change the number of $cop. or more?

Examples:
 Ci dwaj byli na siebie specjalnie uczuleni.
*Ci dwaj był na siebie specjalnie uczulony.

 jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanych.
*są na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanych.
* jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanej. ?
* jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywana. ?


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

