a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  
  child a-node $nsubj := [
    tag = 'PRON',
    deprel = 'nsubj',
  ],
  
  (
    # W czasach teraźniejszym i przyszłym trzeba zmienić osobę $roota
    ($root.iset/tense in{'present', 'fut'} and $root.iset/person in{'1', '2', '3'} and $nsubj.iset/person = $root.iset/person)
    or
    # W czasie przeszłym przy osobach 1 i 2, trzeba zmienić osobę węzła o własnosci deprel = 'aux:clitic' lub usunąć ten węzeł
    ($root.iset/tense = 'past' and child [deprel = 'aux:clitic'] and $nsubj.iset/person in{'1', '2'})
    or
    # W czasie przeszłym przy osobie 3, trzeba dodać do $roota węzeł o własności deprel = 'aux clitic'
    ($root.iset/tense = 'past' and $nsubj.iset/person = '3')
  )
]
