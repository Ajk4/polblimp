a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    member iset [ case = 'gen' ],
    0x child [tag = 'NUM'] # if we dont want numerals
  ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by',
    member iset [gender = 'neut']
  ]`
]
