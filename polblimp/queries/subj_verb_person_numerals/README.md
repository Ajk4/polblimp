subj_verb_person_numerals
Change the person of $root.
Probably more complicated - if the person is not labeled on the verb and must be changed differently – analogically to subj_verb_person_simple

Query:
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  member iset[person = '3'], # check person

  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',

    child a-node $num := [
    tag = 'NUM',
    ],

  ]
]
