Hello world!

- smil
- til
- meg

1. 2 3
4. mef
5. her

*oi* det er _kult_ å `gjøre ting` med https://typst.app/ mener
- hei
+ oi
/ Term: oi
figure hei
table hei
$1 + 2 = x$

@hei: viser liksom greier

#figure(
  table(
    columns: 4,
    [t], [1], [2], [3],
    [y], [0.3s], [0.4s], [0.8s],
  ),
  caption: [Timing results],
) <hei>

mens @hei viser også liksom greier

kan jeg liksom

#show figure.caption: emph

#figure(
  rect[btn],
  caption: [_*bold of you to assume this is a mere button*_],
) <lilleaila>

ok ja det er ganske kult hva som vises i @lilleaila

videre kan vel jeg gjøre
#figure(
  table(
    columns: 2,
    [x], $1 / 2$,
    [y], $sqrt(2)$,
  ),
  caption: [ja det virker ja $ln(2x + 3) ^ 4 ^ x / 3$],
)

#for x in range(1, 4) [
  #x. Fisk

]

#let tall = 5

#let dobbelt(x) = x * 2

Jeg har #tall epler som ganget med #text(32pt)[to] blir #dobbelt(tall)

#set text(14pt)

Alt er større fra nå av

#let aaa-er = "aaaaa"

#lower(aaa-er) kan skrives som #upper(aaa-er) eller som #super(aaa-er) eller til og med som #underline(aaa-er) eller kanskje #align(center, [hei]) ja det ganske kult

oja man har også #footnote([hei]) og det virker å trykke på den ja @hei

#set math.equation(numbering: "1.")

Men ja det jeg er mest her for er jo matematikk aspektet:
$f(x) := cases(
    x "for" 1 < 0,
    2x "for" 2 > 0,
    lim(x, infinity) "for" 63,
  )$ <her>

hmm $lim_(x -> infinity) f(x)$ virket ikke i @her

$display(lim_(x -> infinity)) f(x)$
