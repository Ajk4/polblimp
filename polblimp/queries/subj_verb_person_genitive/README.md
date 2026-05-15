a-node $root := [
  #lemma = 'być',
  deprel = 'root',
  tag = 'VERB',
  member iset [
    number = 'sing',
  ],

  child a-node $subj := [
    deprel = 'nsubj',
    member iset [ case = 'gen' ],
  ],
]
