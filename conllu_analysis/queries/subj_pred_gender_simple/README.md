Query for ADJ:
a-node $root := [
  tag = 'ADJ',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    member iset [gender = $root.iset/gender],
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],
  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]

Query for the rest (so we don’t exclude present and future from adjectival):

a-node $root := [
  tag != 'VERB',
  tag != 'ADJ',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],
  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
    member iset [tense = 'past']
  ]
]


