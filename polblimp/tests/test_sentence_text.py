from __future__ import annotations

import unittest
from pathlib import Path

import conllu

from phenomena.common import load_sentences
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.adjective.adjective_and_copula.subj_adjectival_gender_cop.generator import (
    run_subj_adjectival_gender_cop,
)
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_case.generator import (
    run_subj_adjectival_case,
)
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_gender.generator import (
    run_subj_adjectival_gender,
)
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_simple.generator import (
    run_subj_verb_gender_simple,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_attractor.generator import (
    run_subj_verb_number_attractor,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_numerals.generator import (
    run_subj_verb_number_numerals,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_simple.generator import (
    run_subj_verb_number_simple,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    run_subj_verb_person_csubj,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_genitive.generator import (
    run_subj_verb_person_genitive,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_simple.generator import (
    run_subj_verb_person_simple,
)


CONDITIONAL_PERSON_CASES = [('pl_lfg-ud-dev.conllu', 211, 'Czy teraz pan ekspert chciałbyś ?'),
 ('pl_lfg-ud-dev.conllu', 308, 'Fortecki mógłbym udźwignąć każdy ciężar, ale nie zbrodnię.'),
 ('pl_lfg-ud-dev.conllu', 512, 'Kmetko nie mógłbyś udowodnić, że ciężarówki należą do jego firm.'),
 ('pl_lfg-ud-dev.conllu', 631, 'Może nie życzyłbyś sobie tego episkopat?'),
 ('pl_lfg-ud-dev.conllu', 1193, 'Sebastian za tydzień obchodziłbym urodziny.'),
 ('pl_lfg-ud-test.conllu', 232, 'Czy ktoś jeszcze chciałbyś się zapisać?'),
 ('pl_lfg-ud-test.conllu', 233, 'Czy ktoś z państwa jeszcze chciałbym zadać pytanie?'),
 ('pl_lfg-ud-test.conllu', 377, '- Gdyby był Pan na boisku, musiałbym Pan strzelać karnego?'),
 ('pl_lfg-ud-train.conllu', 135, 'A może pan chciałbym recytować?'),
 ('pl_lfg-ud-train.conllu', 410, 'Ale kto chciałbyś żyć wiecznie?'),
 ('pl_lfg-ud-train.conllu', 626, 'Andrew wolałbym, aby Elizabeth pożegnali tylko najbliżsi.'),
 ('pl_lfg-ud-train.conllu', 1216, 'Chciałbym pan pewnie wrócić do Polski.'),
 ('pl_lfg-ud-train.conllu', 1677, 'Czy bez Marka Pola w rządzie miałbym pan pełnomocnika do spraw kobiet albo pomysły autostradowo-winietowe?'),
 ('pl_lfg-ud-train.conllu', 1727, 'Czy jeszcze ktoś chciałbyś się zapisać do zadania pytania?'),
 ('pl_lfg-ud-train.conllu', 1774, 'Czy mógłbym Pan powiedzieć kilka słów o tej kampanii?'),
 ('pl_lfg-ud-train.conllu', 2743, 'Gdyby wybory ukraińskie odbywały się w Polsce, zdecydowanie wygrałbyś Juszczenko.'),
 ('pl_lfg-ud-train.conllu', 3845, '- Jeśli prezydent chciałbyś nam pomóc w zjednoczeniu, może to zrobić.'),
 ('pl_lfg-ud-train.conllu', 4268, 'Krasicki mógłbym się znaleźć w kłopocie.'),
 ('pl_lfg-ud-train.conllu', 4323, 'Kto chciałbym zabrać głos?'),
 ('pl_lfg-ud-train.conllu', 4401, 'Który milioner żyłbyś w takim syfie?'),
 ('pl_lfg-ud-train.conllu', 4408, 'Któż pielęgnowałbym go wtedy z takim oddaniem?...'),
 ('pl_lfg-ud-train.conllu', 4719, 'Marek mógłbyś doznać szoku.'),
 ('pl_lfg-ud-train.conllu', 4757, 'Masowy powrót przyniósłbym doraźne korzyści budżetowi.'),
 ('pl_lfg-ud-train.conllu', 4802, 'Mało brakowało, a miłość do zajączka Kamil przypłaciłbyś życiem.'),
 ('pl_lfg-ud-train.conllu', 5521, 'Na razie nie wiadomo, kto miałbym zastąpić aelowców.'),
 ('pl_lfg-ud-train.conllu', 5637, 'Nagle ktoś mi mówi, że doktor Kuszner nadawałbyś się do filmu.'),
 ('pl_lfg-ud-train.conllu', 6370, '- Nie twierdzę, że jesteśmy bez winy, ale w zasadzie zarzut ten mógłbyś dotyczyć strony państwowej.'),
 ('pl_lfg-ud-train.conllu', 6755, 'Nikt nie uwierzyłbyś w powodzenie...'),
 ('pl_lfg-ud-train.conllu', 7538, 'Pan chciałbym szefa podporządkować bezpośrednio prezydentowi.'),
 ('pl_lfg-ud-train.conllu', 8308, 'Porosłaby gęstym lasem, jak cała okolica, gdyż chudy piasek nie dałbym życia.'),
 ('pl_lfg-ud-train.conllu', 8527, 'Powstałbyś wtedy jedyny prawdziwy Kościół ojca Rydzyka.'),
 ('pl_lfg-ud-train.conllu', 8801, 'Przeciętny Polak musiałbyś na nią pracować sto lat.'),
 ('pl_lfg-ud-train.conllu', 9275, 'Rezultat wydaje się z góry przesądzony, ale każdy z autorów chciałbym dorzucić własne argumenty.'),
 ('pl_lfg-ud-train.conllu', 9470, 'Równie dobrze przeciw płaceniu podatków oponować mógłbym kupiec.'),
 ('pl_lfg-ud-train.conllu', 9735, '- Spojrzał triumfalnie po obecnych, jakby przypuszczał, że ktoś mógłbym nie znać tego cytatu.'),
 ('pl_lfg-ud-train.conllu', 9814, '– Sprzedałbyś pan obcemu ziemię?'),
 ('pl_lfg-ud-train.conllu', 10485, '- Teraz pan poseł chciałbyś coś powiedzieć?'),
 ('pl_lfg-ud-train.conllu', 11284, 'Uważamy, że goniec przyniósłbym je szybciej pieszo z Gdańska.'),
 ('pl_lfg-ud-train.conllu', 12533, 'Wykonano ją chałupniczo, ale nie powstydziłbym się ich żaden fachowiec.'),
 ('pl_lfg-ud-train.conllu', 12783, 'Z kim chciałbyś Pan znaleźć się w jednej partii?'),
 ('pl_lfg-ud-train.conllu', 13513, 'Zresztą Batura mógłbym popsuć.'),
 ('pl_lfg-ud-train.conllu', 13675, 'Świadek zeznawałbyś w procesach pozostałych członków gangu.'),
 ('pl_pdb-ud-dev.conllu', 311, 'Kmetko nie mógłbyś udowodnić, że ciężarówki należą do jego firm.'),
 ('pl_pdb-ud-dev.conllu', 724, '3. Udowodnić, że "sprawca" jest "typem człowieka", który mógłbyś się dopuścić inkryminowanego czynu.'),
 ('pl_pdb-ud-dev.conllu', 732, 'Są bardzo niebezpieczne, ich wybuch spowodowałbyś falę uderzeniową o promieniu do jednego kilometra.'),
 ('pl_pdb-ud-dev.conllu',
  819,
  'Przeciętny Polak mógłbym się oburzyć: z czego się cieszyć, skoro on nie ma czego do garnka włożyć? - zauważa prof. Edmund Wnuk-Lipiński.'),
 ('pl_pdb-ud-dev.conllu', 1292, 'Prezes firmy, gdzie średnia płaca wynosi ok. 2 tys. zł zarabiałbyś ze wszelkimi dodatkami nie więcej niż 23 tys. zł.'),
 ('pl_pdb-ud-dev.conllu', 1383, 'GDYBY NIE BYŁO WAGINY, PENIS BYŁBY GENERAŁEM W STANIE SPOCZYNKU i świat nie miałbyś problemu z grzechem i "tymi rzeczami".'),
 ('pl_pdb-ud-dev.conllu',
  1791,
  'Peres energicznie zaprzecza, jakoby miał zawiązywać wewnątrzpartyjne spiski, a Rabin z uporem powtarza ostrzeżenia: jeśli ktoś chciałbym sprzymierzyć się z '
  'prawicą - popełni polityczne samobójstwo.'),
 ('pl_pdb-ud-dev.conllu',
  2198,
  'Tekst brzmiałbym wówczas: "wzywa do włączania zaleceń i związanych z nimi uwag do rozmów prowadzonych przez UE z obiema stronami konfliktu, a także na '
  'forach wielostronnych”.'),
 ('pl_pdb-ud-test.conllu', 549, 'Czy ktoś z państwa jeszcze chciałbym zadać pytanie?'),
 ('pl_pdb-ud-test.conllu', 569, 'Czy ktoś jeszcze chciałbyś się zapisać?'),
 ('pl_pdb-ud-test.conllu',
  995,
  'Chesterton w swych wydanych w Anglii wspomnieniach z wizyty w naszym kraju cytuje tę mowę i zamyka ją komentarzem, zapytując: "Ciekaw jestem, czy w całym '
  'Brytyjskim Imperium znalazłbym się choć jeden pułkownik kawalerii, który byłby zdolny zabłysnąć taką inteligencją i zdobyć się na takie przemówienie?".'),
 ('pl_pdb-ud-test.conllu', 1428, 'W ten sposób Sejm miałbym szansę mieć prawdziwy mandat społeczny.'),
 ('pl_pdb-ud-test.conllu',
  1592,
  'Miałbym on wspierać uczniów uzdolnionych, którzy mają trudności z kontynuowaniem nauki z przyczyn rodzinnych czy ekonomicznych.'),
 ('pl_pdb-ud-test.conllu',
  1820,
  'Nie potrafię dostrzec, jaki apel Parlamentu do państw członkowskich o wytyczanie ścieżek rowerowych (pkt 7) lub obniżenie opłat lotniskowych (pkt 32) '
  'miałbym się przyczynić do poprawy sytuacji w branży turystycznej.'),
 ('pl_pdb-ud-test.conllu', 1931, 'Porządny człowiek zostawiłbym żonę w spokoju.'),
 ('pl_pdb-ud-test.conllu', 1960, 'Czy jest jakikolwiek rodzaj oświadczenia, pod którym mógłbyś pan się podpisać.'),
 ('pl_pdb-ud-train.conllu', 2296, 'Świadek zeznawałbyś w procesach pozostałych członków gangu.'),
 ('pl_pdb-ud-train.conllu', 2354, 'Pan chciałbym szefa podporządkować bezpośrednio prezydentowi.'),
 ('pl_pdb-ud-train.conllu', 2913, 'Zresztą Batura mógłbym popsuć.'),
 ('pl_pdb-ud-train.conllu', 3302, 'Nikt nie uwierzyłbyś w powodzenie...'),
 ('pl_pdb-ud-train.conllu', 3405, 'Nagle ktoś mi mówi, że doktor Kuszner nadawałbyś się do filmu.'),
 ('pl_pdb-ud-train.conllu', 3622, 'Czy mógłbym Pan powiedzieć kilka słów o tej kampanii?'),
 ('pl_pdb-ud-train.conllu', 4013, 'Gdyby wybory ukraińskie odbywały się w Polsce, zdecydowanie wygrałbyś Juszczenko.'),
 ('pl_pdb-ud-train.conllu', 4113, 'Mało brakowało, a miłość do zajączka Kamil przypłaciłbyś życiem.'),
 ('pl_pdb-ud-train.conllu', 4300, 'Z kim chciałbyś Pan znaleźć się w jednej partii?'),
 ('pl_pdb-ud-train.conllu', 4548, 'Tylko który z tych "milionerów" poddałbyś się sprawdzeniu.'),
 ('pl_pdb-ud-train.conllu', 4701, 'W przeliczeniu na jednego mieszkańca koszt wyniósłbyś ok. 300 zł.'),
 ('pl_pdb-ud-train.conllu', 5037, 'I wreszcie rząd odpowiadałbyś za logistykę, finanse, prawo, uruchamiałby rezerwy i sprzęt specjalistyczny.'),
 ('pl_pdb-ud-train.conllu', 5081, 'Nie wiem, czy Putin to Piotr II, który chciałbyś przywiązać Rosję do Zachodu, by uczynić ją silną.'),
 ('pl_pdb-ud-train.conllu',
  5370,
  'Gdybym opisywała tę scenę jako literatka, mój bohater dostałbyś w tym momencie apopleksji, czyli trafił by go szlag na miejscu.'),
 ('pl_pdb-ud-train.conllu', 5438, '- Czy ktoś z państwa chciałbyś jeszcze zabrać głos w tej sprawie?'),
 ('pl_pdb-ud-train.conllu', 5472, 'Szereg takich poleceń składałbym się na całą procedurę, którą urządzenie byłoby sterowane.'),
 ('pl_pdb-ud-train.conllu',
  5524,
  'Niejeden z naszych rodaków usiłowałbyś opylić skarby na czarnym rynku, geolodzy byli jednak ludźmi o niezachwianych zasadach etycznych.'),
 ('pl_pdb-ud-train.conllu',
  5820,
  'Policjanci będą mogli też dorabiać przy zabezpieczaniu imprez masowych w czasie wolnym od służby - za ich pracę płaciłbyś organizator imprezy.'),
 ('pl_pdb-ud-train.conllu',
  6476,
  'Kserowanie oraz dostęp do informacji o utraconych dokumentach tożsamości pozwoliłbym - według KRROG - na ograniczenie wykorzystywania tych dokumentów w '
  'procederze wyłudzania.'),
 ('pl_pdb-ud-train.conllu',
  6890,
  '"Oni wszyscy są dzisiaj mętni - myślał patrząc na kierownika i kelnerów uwijających się po kawiarni jak mrówki w zburzonym mrowisku - przydałbym się im '
  'jaki zastrzyk na uspokojenie".'),
 ('pl_pdb-ud-train.conllu', 6903, 'Styl ten też uwzględniłbyś edukacyjny rozwój jednostki.'),
 ('pl_pdb-ud-train.conllu', 7226, '- Każdy zrobiłbym to samo - mówią funkcjonariusze Piotr Grochowski i Jacek Kałuski.'),
 ('pl_pdb-ud-train.conllu',
  7749,
  'Gdyby nie klimat, który stworzyły referenda, to prezydent Republiki Czeskiej nie wystąpiłbyś pewnie z projektem zlikwidowania Unii Europejskiej i '
  'utworzenia "Organizacji Państw Europejskich", która - jak można wnioskować z doniesień i komentarzy prasowych - byłaby bardzo podobna do przedwojennej Ligi '
  'Narodów.'),
 ('pl_pdb-ud-train.conllu',
  8949,
  'Gdyby kierownictwo ZUS zdecydowało się na Mercedesa lub BMW, to koszt jednego samochodu przekroczyłbym 200 tys. nowych złotych.'),
 ('pl_pdb-ud-train.conllu', 9242, 'Gdyby tak zgolił romantyczną bródkę, a w sobie stwardniał i jakoś się wyprościł, to byłbym może z niego człowiek.'),
 ('pl_pdb-ud-train.conllu', 9282, 'Któż lepiej niż Ty mógłbym mnie poprowadzić przez życie.'),
 ('pl_pdb-ud-train.conllu',
  9493,
  'Już tylko ten argument w sposób przekonywający przemawiałbym za rozwojem własnego rybołówstwa i jego zaplecza - fabryk lodu, zamrażalni, chłodni, '
  'specjalistycznego transportu.'),
 ('pl_pdb-ud-train.conllu', 9685, 'A pytanie moje - podobałbym Ci się świat ludzi plujących w radości istnienia jadem "nihilistycznym" zabijającym złudzenia.'),
 ('pl_pdb-ud-train.conllu',
  9827,
  'Jesteśmy więc zainteresowani powstaniem systemu wolontariatu, który pomógłbym naszym rodzinom normalniej żyć: by matka mogła zrobić zakupy, pójść do '
  'lekarza.'),
 ('pl_pdb-ud-train.conllu', 10421, 'Ciekaw jestem, jak Jean Gimpel oceniłbyś swoje prognozy pięć lat później?'),
 ('pl_pdb-ud-train.conllu', 10670, 'Jej osobowość najlepiej przedstawiałbym potulny baranek, rzadko kiedy stawia na swoim, prawie w ogóle się nie kłóci.'),
 ('pl_pdb-ud-train.conllu', 11146, 'Gdyby tak było, w roli matematyka doskonale spisywałbyś się komputer.'),
 ('pl_pdb-ud-train.conllu',
  11323,
  '- Są dwa wyjścia, albo usunąć ten znak, ponieważ tylko dezorientuje kierowców, albo postawić jeszcze jeden znak, który sygnalizowałbym o tym, iż na ulicy '
  'jest ruch dwukierunkowy - powiedział.'),
 ('pl_pdb-ud-train.conllu',
  11427,
  'Czy pan senator Chronowski, jako sprawozdawca wniosku mniejszości Komisji Praw Człowieka i Praworządności, chciałbyś coś dodać?'),
 ('pl_pdb-ud-train.conllu', 11678, 'Zarazem na wszystkich studentach zaciążyłbyś obowiązek przedstawiania WKU dokumentów świadczących, że nadal studiują.'),
 ('pl_pdb-ud-train.conllu', 11960, '- Rozsądek nakazywałbyś zabrać go ze sobą.'),
 ('pl_pdb-ud-train.conllu', 12377, 'Koniec wiecu przed Białym Domem ucieszyłbym z pewnością właściciela parkingu przed parlamentem.'),
 ('pl_pdb-ud-train.conllu',
  12743,
  'W Polsce minister edukacji chciałbyś zwiększyć 18-godzinne pensum, nauczyciele zaś - zarabiać tyle, ile wynosi średnia krajowa, a nie 60 proc. tej kwoty.'),
 ('pl_pdb-ud-train.conllu',
  13359,
  'Ponieważ wszędzie czai się wróg, który chętnie schrupałbyś nasze kości na obiad, do ręki dostajemy - oczywiście w miarę postępu w grze - potężny arsenał '
  '(włącznie z miniatomówkami).'),
 ('pl_pdb-ud-train.conllu', 13471, 'On uważałbyś za rzecz śmieszną i niestosowną dzielenie się z nią swoimi nadziejami i troskami.'),
 ('pl_pdb-ud-train.conllu', 13481, 'Kto, czego i dlaczego miałbyś lękać się?'),
 ('pl_pdb-ud-train.conllu',
  13626,
  'Czy mógłbym pan powiedzieć, co tutaj państwo postanowili, jaka jest formuła egzekwowania tego, bo opinię publiczną bulwersuje, jeśli spółka przynosi '
  'deficyt, a mimo to windowane są bardzo wysokie płace prezesów i zarządów.'),
 ('pl_pdb-ud-train.conllu', 14267, '- Mogli zaaresztować mnie za próbę wywiezienia jej z ojczyzny, a jednocześnie nie było tam nikogo, kto mógłbyś jej pomóc.'),
 ('pl_pdb-ud-train.conllu',
  14327,
  'Skoro stosunki niemiecko-izraelskie są bliskie i bardzo przyjazne i skoro to samo można powiedzieć o stosunkach polsko-niemieckich po 1989 roku, to '
  'wydawałoby się, że podobny rozwój mógłbyś charakteryzować stosunki między Polakami a Żydami.'),
 ('pl_pdb-ud-train.conllu', 15359, 'Ale jest ktoś kto chciałbyś się z tobą spotkać.'),
 ('pl_pdb-ud-train.conllu',
  15805,
  'Szlam mógłbyś być składowany w gospodarstwach i przetwarzany w biogaz, a odpady z tego pochodzące mogłyby zostać rozprowadzane po ziemi.'),
 ('pl_pdb-ud-train.conllu',
  16111,
  'Gdyby zagrożenie było prawdziwe, twój strach ocaliłbyś ci życie, ponieważ wydzielona wtedy adrenalina pomogłaby ci w ucieczce.'),
 ('pl_pdb-ud-train.conllu',
  16216,
  'Nowy system zawierałbym program ciągły, obejmujący średniookresowe raporty, które pozwoliłyby na powtórne dostosowywanie celów w miarę potrzeby.'),
 ('pl_pdb-ud-train.conllu',
  16824,
  'System taki mógłbym prowadzić do sytuacji, w której minimalny okres corocznego płatnego urlopu zostałby zastąpiony ekwiwalentem pieniężnym.'),
 ('pl_pdb-ud-train.conllu', 17378, 'Oznacza to, że nowy system recyklingu statków stałbyś się skuteczny około 2015 r.')]


PAST_PERSON_STEM_CASES = [
    (
        "pl_lfg-ud-dev.conllu",
        549,
        "Któż z marynarzy w dawnych czasach mógł sobie na to pozwolić.",
        "Któż z marynarzy w dawnych czasach mogłeś sobie na to pozwolić.",
    ),
    (
        "pl_lfg-ud-test.conllu",
        85,
        "Alfons Piotrowski poniósł śmierć nie odzyskawszy przytomności.",
        "Alfons Piotrowski poniosłem śmierć nie odzyskawszy przytomności.",
    ),
    (
        "pl_lfg-ud-test.conllu",
        527,
        "Kelner przyniósł jej zamówione capuccino.",
        "Kelner przyniosłem jej zamówione capuccino.",
    ),
    (
        "pl_lfg-ud-test.conllu",
        645,
        "Mnich uniósł oczy.",
        "Mnich uniosłeś oczy.",
    ),
    (
        "pl_lfg-ud-train.conllu",
        250,
        "- A więc Leszek Balcerowicz odniósł już zwycięstwo?",
        "- A więc Leszek Balcerowicz odniosłeś już zwycięstwo?",
    ),
    (
        "pl_lfg-ud-train.conllu",
        1066,
        "Ból rósł.",
        "Ból rosłem.",
    ),
    (
        "pl_lfg-ud-train.conllu",
        3376,
        "- Jajo przywiózł do nas osobiście dyrektor płockiego zoo.",
        "- Jajo przywiozłem do nas osobiście dyrektor płockiego zoo.",
    ),
    (
        "pl_lfg-ud-train.conllu",
        5593,
        "Na środku kolejnego ronda wyrósł murek z roślinami na szczycie.",
        "Na środku kolejnego ronda wyrosłem murek z roślinami na szczycie.",
    ),
    (
        "pl_lfg-ud-train.conllu",
        13465,
        "Znów pomógł mu aspirant.",
        "Znów pomogłem mu aspirant.",
    ),
    (
        "pl_pdb-ud-test.conllu",
        1854,
        "Howard odwiózł go do obozu, a żołnierzy załadowano na ciężarówki.",
        "Howard odwiozłeś go do obozu, a żołnierzy załadowano na ciężarówki.",
    ),
]


PAST_PERSON_CLITIC_CASES = [
    (
        "pl_pdb-ud-dev.conllu",
        857,
        "- Rozumiem, pani poseł, ale ja na przykład, jeżeli starałbym się o wpis na listę doradców "
        "podatkowych, to na podstawie tego przepisu - oświadczam to przed Wysoką Izbą - na pewno "
        "nie byłbym wpisany, bo naprawdę nie jestem osobą nieskazitelnego charakteru.",
        "- Rozumiem, pani poseł, ale ja na przykład, jeżeli starałbym się o wpis na listę doradców "
        "podatkowych, to na podstawie tego przepisu - oświadczam to przed Wysoką Izbą - na pewno "
        "nie byłby wpisany, bo naprawdę nie jestem osobą nieskazitelnego charakteru.",
    ),
    (
        "pl_pdb-ud-dev.conllu",
        1091,
        "Tak jakby – zgodził się niechętnie Wiktor, a ja byłem skłonny postawić każde pieniądze, "
        "że niewypowiedziana część zdania brzmiała: “Zawsze możemy go zgnoić później”.",
        "Tak jakby – zgodził się niechętnie Wiktor, a ja był skłonny postawić każde pieniądze, "
        "że niewypowiedziana część zdania brzmiała: “Zawsze możemy go zgnoić później”.",
    ),
    (
        "pl_pdb-ud-train.conllu",
        6735,
        "- Gdybym ja był prezydentem, to powiedziałbym tak: gen. Jaruzelski był sybirakiem i dostał "
        "krzyż za to, że był sybirakiem - mówił wczoraj Andrzej Lepper.",
        "- Gdybyś ja był prezydentem, to powiedziałbym tak: gen. Jaruzelski był sybirakiem i dostał "
        "krzyż za to, że był sybirakiem - mówił wczoraj Andrzej Lepper.",
    ),
    (
        "pl_pdb-ud-train.conllu",
        7189,
        "Ja nie byłem zbyt głodny, więc poprzestałem na sałatce.",
        "Ja nie był zbyt głodny, więc poprzestałem na sałatce.",
    ),
    (
        "pl_pdb-ud-train.conllu",
        14809,
        "Ja też taka byłam, kiedy mnie tu deportowali.",
        "Ja też taka była, kiedy mnie tu deportowali.",
    ),
    (
        "pl_pdb-ud-test.conllu",
        926,
        "- To nie potrwa długo, kochanie - uspokajał cię, patrząc pytająco, bo nie był pewien, czy "
        "zechcesz zostać sama z Feliksem, a ty przyzwalająco skinęłaś głową i Feliks opadł na "
        "krzesło, chociaż wiedział, że powinien wyjść razem z Maurycym.",
        "- To nie potrwa długo, kochanie - uspokajał cię, patrząc pytająco, bo nie był pewien, czy "
        "zechcesz zostać sama z Feliksem, a ty przyzwalająco skinęłam głową i Feliks opadł na "
        "krzesło, chociaż wiedział, że powinien wyjść razem z Maurycym.",
    ),
    (
        "pl_pdb-ud-train.conllu",
        10381,
        "Zebrałem się na odwagę i wypaliłem: - Bo myśmy właśnie z Baśką postanowili się pobrać "
        "wkrótce i ja przyjechałem do Warszawy, bo pragniemy zamieszkać w stolicy, ja muszę "
        "ukończyć studia, a i Baśka by chciała dyplom zrobić.",
        "Zebrałem się na odwagę i wypaliłem: - Bo myście właśnie z Baśką postanowili się pobrać "
        "wkrótce i ja przyjechałem do Warszawy, bo pragniemy zamieszkać w stolicy, ja muszę "
        "ukończyć studia, a i Baśka by chciała dyplom zrobić.",
    ),
]


NUMBER_CLITIC_CASES = [
    (
        run_subj_verb_number_simple,
        "pl_lfg-ud-test.conllu",
        684,
        "Myśmy nikomu nie zagrażali.",
        "My nikomu nie zagrażałem.",
    ),
    (
        run_subj_verb_number_simple,
        "pl_lfg-ud-train.conllu",
        5320,
        "myśmy tak w butach wleźli.",
        "my tak w butach wlazłem.",
    ),
    (
        run_subj_verb_number_simple,
        "pl_pdb-ud-train.conllu",
        5115,
        "- Myśmy wtedy wszyscy - powiada pewien znajomy - trochę grzeszyli pychą.",
        "- My wtedy wszyscy - powiada pewien znajomy - trochę grzeszyłem pychą.",
    ),
    (
        run_subj_verb_number_simple,
        "pl_pdb-ud-train.conllu",
        10381,
        "Zebrałem się na odwagę i wypaliłem: - Bo myśmy właśnie z Baśką postanowili się pobrać "
        "wkrótce i ja przyjechałem do Warszawy, bo pragniemy zamieszkać w stolicy, ja muszę "
        "ukończyć studia, a i Baśka by chciała dyplom zrobić.",
        "Zebrałem się na odwagę i wypaliłem: - Bo my właśnie z Baśką postanowiłem się pobrać "
        "wkrótce i ja przyjechałem do Warszawy, bo pragniemy zamieszkać w stolicy, ja muszę "
        "ukończyć studia, a i Baśka by chciała dyplom zrobić.",
    ),
    (
        run_subj_verb_number_simple,
        "pl_pdb-ud-train.conllu",
        13443,
        "Do tej pory było tak, Unię strasznie to wzburzało, że myśmy ich towary tam sprawdzone "
        "tutaj poddawali znowuż kolejnym sprawdzeniom, że tak powiem, fizycznym, obróbce.",
        "Do tej pory było tak, Unię strasznie to wzburzało, że my ich towary tam sprawdzone "
        "tutaj poddawałem znowuż kolejnym sprawdzeniom, że tak powiem, fizycznym, obróbce.",
    ),
    (
        run_subj_verb_number_attractor,
        "pl_lfg-ud-test.conllu",
        684,
        "Myśmy nikomu nie zagrażali.",
        "My nikomu nie zagrażałem.",
    ),
    (
        run_subj_verb_number_attractor,
        "pl_pdb-ud-train.conllu",
        10381,
        "Zebrałem się na odwagę i wypaliłem: - Bo myśmy właśnie z Baśką postanowili się pobrać "
        "wkrótce i ja przyjechałem do Warszawy, bo pragniemy zamieszkać w stolicy, ja muszę "
        "ukończyć studia, a i Baśka by chciała dyplom zrobić.",
        "Zebrałem się na odwagę i wypaliłem: - Bo my właśnie z Baśką postanowiłem się pobrać "
        "wkrótce i ja przyjechałem do Warszawy, bo pragniemy zamieszkać w stolicy, ja muszę "
        "ukończyć studia, a i Baśka by chciała dyplom zrobić.",
    ),
]


UPPERCASE_CASES = [
    (
        run_subj_verb_number_simple,
        "pl_lfg-ud-train.conllu",
        3414,
        "JAK ONE TO ROBIĄ?",
        "JAK ONE TO ROBI?",
    ),
    (
        run_subj_verb_number_simple,
        "pl_lfg-ud-train.conllu",
        6043,
        "NIE JEST TO PRAWDĄ.",
        "NIE SĄ TO PRAWDĄ.",
    ),
    (
        run_subj_verb_person_simple,
        "pl_pdb-ud-dev.conllu",
        1383,
        "GDYBY NIE BYŁO WAGINY, PENIS BYŁBY GENERAŁEM W STANIE SPOCZYNKU i świat nie miałby "
        "problemu z grzechem i \"tymi rzeczami\".",
        "GDYBY NIE BYŁO WAGINY, PENIS BYŁBYŚ GENERAŁEM W STANIE SPOCZYNKU i świat nie miałby "
        "problemu z grzechem i \"tymi rzeczami\".",
    ),
]


NUMBER_NUMERALS_INFINITIVE_CASES = [
    (
        "pl_lfg-ud-train.conllu",
        5618,
        "Nad wszystkim czuwać będzie trzech lekarzy i personel pielęgniarski.",
        "Nad wszystkim czuwać będą trzech lekarzy i personel pielęgniarski.",
    ),
    (
        "pl_pdb-ud-dev.conllu",
        1344,
        "Nad bezpieczeństwem i utrzymaniem porządku czuwać będzie 45 tys. funkcjonariuszy i 32 "
        "tys. pomocników.",
        "Nad bezpieczeństwem i utrzymaniem porządku czuwać będą 45 tys. funkcjonariuszy i 32 "
        "tys. pomocników.",
    ),
    (
        "pl_pdb-ud-test.conllu",
        843,
        "Imprezę obsługiwać będzie 11 tys. dziennikarzy i pracowników technicznych.",
        "Imprezę obsługiwać będą 11 tys. dziennikarzy i pracowników technicznych.",
    ),
    (
        "pl_pdb-ud-train.conllu",
        6353,
        "Wyciągał jedynie wnioski z obszaru i potencjału państwa rosyjskiego twierdząc, że dwa "
        "mocarstwa, Rosja i Ameryka, określać będą przyszłość świata.",
        "Wyciągał jedynie wnioski z obszaru i potencjału państwa rosyjskiego twierdząc, że dwa "
        "mocarstwa, Rosja i Ameryka, określać będzie przyszłość świata.",
    ),
    (
        "pl_pdb-ud-train.conllu",
        16224,
        "Wielu obywateli będzie to postrzegać jako kolejny przykład, że elita UE robi dokładnie "
        "to, na co ma ochotę.",
        "Wielu obywateli będą to postrzegać jako kolejny przykład, że elita UE robi dokładnie "
        "to, na co ma ochotę.",
    ),
]




class TestSentenceText(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.morph_dict = MorphDictionary.load(cls.repo_root / "dictionary.v4.csv")
        cls.sentences: dict[str, list[conllu.TokenList]] = {}

    def test_generated_sentence_outputs(self) -> None:
        cases = [
            {
                "dataset": ("pl_lfg-ud-dev.conllu", 1061),
                "source": "- Pozostałe punkty zostały zatwierdzone.",
                "transform": run_subj_adjectival_gender_cop,
                "expected": "- Pozostałe punkty zostali zatwierdzeni.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 2393),
                "source": "Drzwi były zamknięte.",
                "transform": run_subj_adjectival_gender,
                "expected": "Drzwi były zamknięci.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 10545),
                "source": "- To bywa męczące.",
                "transform": run_subj_adjectival_gender,
                "expected": "- To bywa męczący.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 10545),
                "source": "- To bywa męczące.",
                "transform": run_subj_adjectival_case,
                "expected": "- To bywa męczącego.",
            },
            {
                "dataset": ("pl_lfg-ud-test.conllu", 1574),
                "source": "Wydawało mi się, że prowadzę z drzewem bezgłośny dialog.",
                "transform": run_subj_verb_person_csubj,
                "expected": "Wydawałoś mi się, że prowadzę z drzewem bezgłośny dialog.",
            },
            {
                "dataset": ("pl_lfg-ud-test.conllu", 1575),
                "source": "Wydawało się, że jej życie dobiegnie końca bez większych niespodzianek.",
                "transform": run_subj_verb_person_csubj,
                "expected": "Wydawałoś się, że jej życie dobiegnie końca bez większych niespodzianek.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 3082),
                "source": "I to była prawda.",
                "transform": run_subj_verb_person_simple,
                "expected": "I to byłam prawda.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 176),
                "source": "A pan ma?",
                "transform": run_subj_verb_person_simple,
                "expected": "A pan masz?",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 892),
                "source": "Bożena też nie ma z czego zwrócić pożyczki.",
                "transform": run_subj_verb_person_simple,
                "expected": "Bożena też nie masz z czego zwrócić pożyczki.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 3083),
                "source": "i to byłby komplet..",
                "transform": run_subj_verb_person_simple,
                "expected": "i to byłbyś komplet..",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 2173),
                "source": "Potem polski papież zostałby w Watykanie kanonizowany.",
                "transform": run_subj_verb_person_simple,
                "expected": "Potem polski papież zostałbyś w Watykanie kanonizowany.",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 2799),
                "source": "Taribal byłby oddał taniej.",
                "transform": run_subj_verb_person_simple,
                "expected": "Taribal byłbyś oddał taniej.",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 12194),
                "source": (
                    "Jednak podczas telewizyjnego programu wyborczego przed wyborami 4 czerwca 1989 roku, "
                    "zapytany przez prowadzącego, czy napisał \"Balladę o Janku Wiśniewskim\", Dowgiałło "
                    "odpowiada enigmatycznie: \"Co miało być anonimowe, niech będzie anonimowe\"."
                ),
                "transform": run_subj_verb_person_csubj,
                "expected": (
                    "Jednak podczas telewizyjnego programu wyborczego przed wyborami 4 czerwca 1989 roku, "
                    "zapytany przez prowadzącego, czy napisał \"Balladę o Janku Wiśniewskim\", Dowgiałło "
                    "odpowiada enigmatycznie: \"Co miało być anonimowe, niech będę anonimowe\"."
                ),
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 7189),
                "source": "Ja nie byłem zbyt głodny, więc poprzestałem na sałatce.",
                "transform": run_subj_verb_number_simple,
                "expected": "Ja nie byliśmy zbyt głodny, więc poprzestałem na sałatce.",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 5673),
                "source": "W kratkach z cyframi skarbów nie ma.",
                "transform": run_subj_verb_person_genitive,
                "expected": "W kratkach z cyframi skarbów nie jestem.",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 13969),
                "source": (
                    "Wracając jednak do zaburzenia rytmu domowego, którego nastolatki nie zauważyły, "
                    "połowa przepytanych nastolatków przyznała też, że regularnie budzi się w nocy, "
                    "żeby zaktualizować statusy, wrzucić zdjęcia, dać jakieś lajki albo sprawdzić, "
                    "ile ma się własnych lajków."
                ),
                "transform": run_subj_verb_gender_simple,
                "expected": (
                    "Wracając jednak do zaburzenia rytmu domowego, którego nastolatki nie zauważyli, "
                    "połowa przepytanych nastolatków przyznała też, że regularnie budzi się w nocy, "
                    "żeby zaktualizować statusy, wrzucić zdjęcia, dać jakieś lajki albo sprawdzić, "
                    "ile ma się własnych lajków."
                ),
            },
        ]

        for case in cases:
            with self.subTest(expected=case["expected"]):
                sentence = self._get_sentence(case)
                self.assertEqual(case["source"], sentence.metadata["text"])
                transform = case["transform"]
                df = transform([sentence], self.morph_dict, None)

                self.assertEqual(1, len(df))
                self.assertEqual(case["expected"], df.iloc[0]["incorrect"])

    def test_conditional_person_outputs(self) -> None:
        for filename, index, expected in CONDITIONAL_PERSON_CASES:
            with self.subTest(dataset=filename, index=index):
                sentence = self._get_sentence({"dataset": (filename, index)})
                df = run_subj_verb_person_simple([sentence], self.morph_dict, None)

                self.assertIn(expected, df["incorrect"].tolist())

    def test_past_person_stem_outputs(self) -> None:
        for filename, index, source, expected in PAST_PERSON_STEM_CASES:
            with self.subTest(dataset=filename, index=index):
                sentence = self._get_sentence({"dataset": (filename, index)})
                self.assertEqual(source, sentence.metadata["text"])
                df = run_subj_verb_person_simple([sentence], self.morph_dict, None)

                self.assertIn(expected, df["incorrect"].tolist())

    def test_past_person_clitic_outputs(self) -> None:
        for filename, index, source, expected in PAST_PERSON_CLITIC_CASES:
            with self.subTest(dataset=filename, index=index):
                sentence = self._get_sentence({"dataset": (filename, index)})
                self.assertEqual(source, sentence.metadata["text"])
                df = run_subj_verb_person_simple([sentence], self.morph_dict, None)

                self.assertIn(expected, df["incorrect"].tolist())

    def test_number_clitic_outputs(self) -> None:
        for transform, filename, index, source, expected in NUMBER_CLITIC_CASES:
            with self.subTest(transform=transform.__name__, dataset=filename, index=index):
                sentence = self._get_sentence({"dataset": (filename, index)})
                self.assertEqual(source, sentence.metadata["text"])
                df = transform([sentence], self.morph_dict, None)

                self.assertIn(expected, df["incorrect"].tolist())

    def test_uppercase_outputs(self) -> None:
        for transform, filename, index, source, expected in UPPERCASE_CASES:
            with self.subTest(transform=transform.__name__, dataset=filename, index=index):
                sentence = self._get_sentence({"dataset": (filename, index)})
                self.assertEqual(source, sentence.metadata["text"])
                df = transform([sentence], self.morph_dict, None)

                self.assertIn(expected, df["incorrect"].tolist())

    def test_number_numerals_infinitive_outputs(self) -> None:
        for filename, index, source, expected in NUMBER_NUMERALS_INFINITIVE_CASES:
            with self.subTest(dataset=filename, index=index):
                sentence = self._get_sentence({"dataset": (filename, index)})
                self.assertEqual(source, sentence.metadata["text"])
                df = run_subj_verb_number_numerals([sentence], self.morph_dict, None)

                self.assertIn(expected, df["incorrect"].tolist())

    def _get_sentence(self, case: dict) -> conllu.TokenList:
        filename, index = case["dataset"]
        if filename not in self.sentences:
            self.sentences[filename] = load_sentences(
                self.repo_root / "data" / filename,
                skip_duplicates=False,
            )
        return self.sentences[filename][index]
