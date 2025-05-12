#import "@preview/colorful-boxes:1.4.2": colorbox

#set text(font: "Times New Roman", size: 12pt)
#set enum(numbering: "a)")
#set page(
  paper: "a4",
  header: {
    grid(
      columns: (1fr, auto),
      [Skriftlig Eksamen REA3056 Vår 2024 - Del 1 og 2],
      align(right)[Kandidatnummer: ABC123],
    )
    line(length: 100%)
  },
  footer: context {
    line(length: 100%)
    align(right)[
      #counter(page).display("1/1", both: true)
    ]
  },
)

#colorbox(
  width: 100%,
  color: "blue",
  inset: 20pt,
  align(center)[= Del 1],
)

== Oppgave 1

$
  f(x) &= 4x^2 dot ln(3x) \
  f'(x) &= 8x dot 1 / (3x) \
  underline(underline(f'(x) &= 8 / 3))
$


== Oppgave 2

$
  (ln x)^2 - ln x &= 6 \
  (ln x)^2 - ln x - 6 &= 0 "kvadratsetning" \
  (ln x - 3)(ln x + 2) &= 0 \
  ln x = 3 &or ln x = - 2 \
  underline(underline(x = e^3 &or x = e^(-2) = 1 / e^2))
$

== Oppgave 3

$
  f(x) = e^(-x + 1)&, D_f = RR \
  lim_(x -> infinity) f(x) &"og" lim_(x -> -infinity) f(x) \
  lim_(x -> infinity) f(x) &= lim_(x -> infinity) e^(-x + 1) \
  &= lim_(x -> infinity) 1 / e^(x - 1) = 0 "eksponent blir uendelig stor" ==> "deler på uendelig høyt" \
  lim_(x -> -infinity) f(x) &= lim_(x -> -infinity) e^(-x + 1) = infinity "eksponent blir uendelig stor" ==> "eksisterer ikke"
$


== Oppgave 4

#colorbox(color: "green", $A(3,4), B(-1, -2) "og" C(3 + t, 2t) "der" t in RR$)


1.

#colorbox(color: "green", [Finn $t$ slik at A, B og C på linje])

Finner stingningstallet mellom $A$ og $B$:

$
  a = (Delta y) / (Delta x) = (4 - (-2)) / (3 - (-1)) = (6) / (4) = 3 / 2
$

Stigningstallet fra $A$ til $C$ (eller $B$ til $C$) skal være det samme.

$
  3 / 2 &= (2t - 4) / ((3 + t) - 3) \
  3 / 2 &= (2t - 4) / t \
  3t &= 2 dot (2t - 4) \
  3t &= 4t - 8 \
  -t &= -8 \
  t &= 8
$

Alternativt med $arrow("AC") = k dot arrow("AB")$

$
  arrow("AC") &= [t, 2t - 4] \
  arrow("AB") &= [-4, -6] \
  arrow("AC") &= k dot arrow("AB") \
  [t, 2t - 4] &= k dot [-4, -6] \
  3t -4 &= k dot (-10) \
  3t &= -10k - 4 \
  t &= (-10k - 4) / 3
$

2.

#colorbox(color: "green", $angle C = 90degree$)

$
  arrow("BC") dot arrow("AC") &= 0 \
  arrow("BC") &= [3 + t + 1, 2t + 2] = [t + 4, 2t + 2] \
  arrow("AC") &= [t, 2t - 4] \
  [t + 4, 2t + 2] dot [t, 2t - 4] &= 0 \
  (t + 4)t + (2t + 2)(2t - 4) &= 0 \
  t^2 + 4t + 4t^2 + 4t - 8t -8 &= 0 \
  5t^2 &= 8 \
  t^2 &= 8 / 5 \
  t &= plus.minus sqrt(8 / 5)
$
