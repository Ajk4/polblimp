a-node $root := [
  tag != 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    child a-node $num := [
      tag = 'NUM'
    ]
  ],

  child a-node $cop := [
    tag = 'AUX',
    lemma != 'to',
    lemma != 'by',
    member iset [tense ='past']
  ],



]
