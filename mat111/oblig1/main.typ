#import "@preview/auto-div:0.1.0": poly-div-working
#set page(
  numbering: "1",
)
#set text(font: "DejaVu Math TeX Gyre", size: 11pt, lang: "no")
#set enum(indent: 1em, numbering: "a)", spacing: 1.5em)
#show heading: set block(below: 1em)

#align(center)[
  #text(16pt, weight: "bold")[MAT111 - Obligatorisk innlevering 1]
]

#v(1em)

= Oppgave 1

+ $
    w = -sqrt(3) - 3 i \
    w = |w| e^(i theta) \
    |w| = sqrt((-sqrt(3))^2 + (-3)^2) = sqrt(12) = 2 sqrt(3) \
    "For å finne" theta "tegner jeg" w "i det komplekse plan som på" #[@oppg1a] \
    #[#figure(
      image("assets/oppg1a.pdf", width: 80%),
      caption: [$w$ avmerket i det komplekse plan],
    ) <oppg1a>] \
    "da er" theta = 2pi - (pi/2 + phi) \
    phi = tan 3/sqrt(3) = tan (3 sqrt(3))/3 = tan sqrt(3) = pi/3 \
    theta = 2pi - pi/2 - pi/3 = (7pi)/6 \
    w = |w| e^(i theta) \
    w = 2 sqrt(3) e^(i (7pi)/6) = 2 sqrt(3) (cos (7pi)/6 + i sin (7pi)/6) \
  $

+ $
    w^15 = (2 sqrt(3))^15 (e^(i (7pi)/6))^15 \
    = 2^15 sqrt(3)^15 e^(i (105pi)/6) quad "subtraherer" 2pi=(12pi)/6 "helt til" theta in (0,2pi) \
    = 2^15 sqrt(3)^15 e^(i (9pi)/6) \
  $

+ (i) $ (i + 5) overline((1 + 3i)) = (i + 5)(i -3i) = i + 5 + 3 - 15i = 8 - 14i $ (ii) $ (2i)/(3+4i) - i = frac(2i overline((3+4i)), (3+4i) overline((3+4i))) - i = (2i(3-4i))/25 - i = frac(6i + 8 - 25i, 25) = 8/25 - 19/25 i $


+ $
    z^3 - 2i = 0 \
    z^3 = 2i \
    w = 2i = |w| e^(i theta) \
    |w| = 2 \
    theta = pi/2 + k dot 2pi, k in ZZ quad "peker bare rett opp fordi" "Re"(w)=0 \
    "siden det er 3 løsninger da det er et tredjegradspolynom" \
    "deler vi sirkelen i 3 deler med vinkel:" (2pi)/3 "mellom dem" \
    w_0 = 2 e^(i(pi/2 + 0 dot (2pi)/3)) = 2 e^(i pi/2) \
    w_1 = 2 e^(i(arg(w_0) + (2pi)/3))) = 2 e^(i (7pi)/6) \
    w_2 = 2 e^(i(arg(w_1) + (2pi)/3))) = 2 e^(i (11pi)/6) \
  $

+ $
    P(z) = z^4 - 3z^3 + 2z^2 + 2z - 4 \
    P(-1) = 1 + 3 + 2 - 2 - 4 = 0 \
    P(2) = 2^4 - 3 dot 2^3 + 2 dot 2^3 + 2 dot 2 - 4 = 2^4 - 2 dot 2^3 = 0 \
    P(z) = (z + 1)(z - 2)(Q(z)) = (z^2 -z - 2)(Q(z)) \
    Q(z) = P(z) : (z^2 - z - 2) \
    #[#poly-div-working((1, -3, 2, 2, -4), (1, -1, -2), var: $z$)] \
    Q(z) = z^2 - 2z + 2 \
    z = frac(2 plus.minus sqrt((-2)^2 - 4 dot 1 dot 2), 2 dot 1) \
    z = 1 plus.minus sqrt(-4)/2 = 1 plus.minus i \
    P(z) = (z + 1)(z - 2)(z - 1 - i)(z - 1 + i) \
    "kvadratisk:" P(z) = (z^2 -z -2)(z^2 - 2z + 2)
  $

+ $
    "Re"(1/z) = "Re"(overline(z)/(z overline(z))) = "Re"(frac(a - b i, a^2 + b^2)) = "Re"(frac(a, a^2 + b^2) - frac(b, a^2 + b^2) i) = frac(a, a^2 + b^2) \
    frac(a, a^2 + b^2) = 1 \
    a = a^2 + b^2 \
    a^2 - a + b^2 = 0 quad "fullfører kvadratet" \
    a^2 - a + 1/4 + b^2 = 1/4 \
    (a - 1/2)^2 + b^2 = (1/2)^2 \
    (a - 1/2)^2 + (b - 0)^2 = (1/2)^2 quad "dette er sirkellikningen" \
    "Løsningene er da på en sirkel med sentrum" S = (1/2, 0) "og radius" r = 1/2 \
    #[Merk at på @oppg1f er altså (0, 0) ikke inkludert da det er z = 0 + 0i = 0 som ble eksludert av $z in CC \\ {0}$]
  $


#figure(
  image("assets/oppg1f.png"),
  caption: [Løsningene til likningen $"Re"(1/z)=1$ i det komplekse plan],
) <oppg1f>


= Oppgave 2

+ $
    sum_(i=1)^(n) frac(i, (i + 1)!) = 1 - frac(1, (n+1)!) \
    "sjekker" n = 1 \
    frac(1, 2!) = 1 - frac(1, (1+1)!) \
    frac(1, 2!) = frac(1, 2!) \
    "anta stemmer for" n = k \
    "sjekker" k + 1 \
    sum_(i=1)^(k) frac(i, (i + 1)!) + frac(k + 1, (k + 2)!) = 1 - frac(1, (k+2)!) \
    1 - frac(1, (k+1)!) + frac(k + 1, (k + 2)!) = 1 - frac(1, (k+2)!) \
    - frac(1, (k+1)!) = frac(-2 - k, (k+2)!) \
    frac(1, (k+1)!) = frac(k + 2, (k+1)!(k+2)) \
    frac(1, (k+1)!) = frac(1, (k+1)!)
  $

+ $
    sum_(i=1)^(n) frac(1, i^2) < 2 - frac(1, n), n >= 2 \
    "sjekker" n=2 \
    frac(1, 2^2) < 2 - frac(1, 2) \
    frac(1, 4) < frac(3, 4) \
    "anta stemmer for" n = k \
    "sjekker" k + 1 \
    sum_(i=1)^(k) frac(1, i^2) + frac(1, (k+1)^2) < 2 - frac(1, k+1), k >= 2 \
    2 - frac(1, k) + frac(1, (k+1)^2) < 2 - frac(1, k+1) \
    -frac(1, k) + frac(1, (k+1)^2) < -frac(1, k+1) quad "fjerner brøkene med" dot k(k+1) \
    -(k+1) + frac(k (k+1), (k+1)^2) < -k \
    frac(k, k+1) < 1 \
    k < k+1 \
    0 < 1
  $

= Oppgave 3

+ $
    lim_(x->-1) (3x+5) = 2 \
    "gitt" epsilon > 0 "finne" delta "slik at" 0 < |x - (-1)| < delta \
    "da er" |3x+5 - 2| < epsilon \
    |3x+3| < epsilon \
    |x+1| < frac(epsilon, 3) \
    delta = frac(epsilon, 3)
  $

+ $
    lim_(x->-2) (x^3 + 4x^2 + 4x -1) = -1 \
    "gitt" epsilon > 0 "finne" delta "slik at" 0 < |x - (-2)| < delta \
    "da er" |x^3 + 4x^2 + 4x -1 -(-1)| < epsilon \
    |x(x^2 + 4x + 4)| < epsilon \
    |x(x+2)^2| < epsilon \
    |x| (x+2)^2 < epsilon \
    |x+2| < sqrt(frac(epsilon, |x|)) \
    "må finne" |x| "sitt interval" \
    |x+2| < delta \
    "antar" delta <= 1 \
    |x+2| < 1 \
    -1 < x+2 < 1 \
    -3 < x < -1 \
    |x| < 3 \
    "setter inn" \
    |x+2| < sqrt(frac(epsilon, 3)) \
    delta = min(1, sqrt(frac(epsilon, 3)))
  $

+ $
    lim_(x->1) frac(1, x) = 1 \
    "gitt" epsilon > 0 "finne" delta "slik at" 0 < |x - 1| < delta \
    "da er" |frac(1, x) - 1| < epsilon \
    |frac(1-x, x)| < epsilon \
    frac(|1-x|, |x|) < epsilon \
    "antar" delta <= frac(1, 2) "(bruker" frac(1, 2) "fordi" delta<=1 "gjør at" x=0 "blir inkludert)" \
    |x - 1| < frac(1, 2) \
    -frac(1, 2) < x - 1 < frac(1, 2) \
    frac(1, 2) < x < frac(3, 2) \
    |x| "står i nevneren i" frac(|1-x|, |x|) < epsilon "og derfor må" |x| > min(frac(1, 2), frac(3, 2)) "for at brøken skal være størst mulig" \
    frac(|1-x|, frac(1, 2)) < epsilon \
    2 dot |1-x| < epsilon \
    |x-1| < frac(epsilon, 2) \
    delta = min(frac(1, 2), frac(epsilon, 2))
  $

= Oppgave 4

+ $
    lim_(x -> -2) frac(x^2 + 7x + 10, x^2 + 3x + 2) \
    lim_(x -> -2) frac((x+2)(x+5), (x+2)(x+1)) \
    lim_(x -> -2) frac(x+5, x+1) \
    = frac(-2+5, -2+1) = frac(3, -1) = -3
  $

+ $
    lim_(x -> -1^-) frac(x^2 + 7x + 10, x^2 + 3x + 2) \
    lim_(x -> -1^-) frac((x+2)(x+5), (x+2)(x+1)) \
    lim_(x -> -1^-) frac(x+5, x+1) \
    x < -1 ==> x + 1 < 0 \
    lim_(x -> -1^-) frac(x+5, x+1) = -infinity \
  $


+ $
    lim_(x -> infinity) frac(3 - 2x, sqrt(3x^2 + 5)) \
    lim_(x -> infinity) frac(3-2x, sqrt(x^2(3 + frac(5, x^2)))) quad (x > 0) \
    lim_(x -> infinity) frac(3-2x, x sqrt(3 + frac(5, x^2))) \
    lim_(x -> infinity) frac(frac(3, x)-2, sqrt(3 + frac(5, x^2))) \
    =frac(-2, sqrt(3))
  $

+ Negativ uendelig er lik som i forrige oppgave da brøkene uansett går til 0 $ lim_(x -> -infinity) frac(3 - 2x, sqrt(3x^2 + 5)) = frac(-2, sqrt(3)) \ $

+ $ lim_(x->0) cos(frac(1, x)) \ $ Grensen eksisterer ikke. Uttrykket konvergerer aldri og går mellom -1 og 1 uendelig mye ved 0

+ $
    lim_(x->0) x cos(frac(1, x)) \
    "Kan ikke bruke grensesetningene da ene grensen ikke eksisterer, bruker heller skviseteoremet" \
    -1 <= cos(frac(1, x)) <= 1 \
    -x <= x cos(frac(1, x)) <= x \
    lim_(x->0) -x <= lim_(x->0) x cos(frac(1, x)) <= lim_(x->0) x \
    0 <= lim_(x->0) x cos(frac(1, x)) <= 0 \
    lim_(x->0) x cos(frac(1, x)) = 0
  $

= Oppgave 5

+ $
    f(x) = 4x^3 - 2x^2 - 4x - 2 \
    f'(x) = 12x^2 - 4x - 4 \
    y = 4x - 1 <==> f'(x) = 4 \
    12x^2 - 4x - 4 = 4 \
    12x^2 - 4x - 8 = 0 \
    3x^2 - x - 2 = 0 \
    x = frac(-(-1) plus.minus sqrt((-1)^2 - 4 dot 3 dot (-2)), 2 dot 3) \
    x = frac(1 plus.minus sqrt(1 + 24), 6) = frac(1 plus.minus 5, 6) \
    f'(1) = 4 and f'(-2/3) = 4 \
    y_1 = f'(1) (x - 1) + f(1) and y_2 = f'(-2/3) (x - (-2/3)) + f(-2/3) \
    y_1 = 4x - 4 - 4 = 4x-8 and y_2 = 4x + 8/3 - 38/27 = 4x + 34/27
  $
+ $
    g(x) = l = 4x - 1 \
    f(-2) = -34 quad f(-1) = -4 \
    "fordi skjæringsteoremet har da" f "alle verdier" (-34, -4) "i" (-2, -1) \
    g(-2) = -9 quad g(-1) = -5 \
    "linjen har" (-9, -5) "i" (-2, -1) \
    "siden alt i" (-9, -5) "eksisterer i" (-26, -4) "vet vi at linjen skjærer her" \
    f(-1) = -4 quad f(0) = -2 \
    g(-1) = -5 quad g(0) = -1 \
    (-4, -2) "og" (-5, -1) "overlapper og vet derfor at de skjærer her også" \
    f(1) = -4 quad f(2) = 14 \
    g(1) = 3 quad g(2) = 7 \
    (3, 7) subset (-4, 14) ==> "skjærer"
  $
+ $
    f(-2) = -34 quad f(2) = 14 \
    g(-2) = -9 quad g(2) = 7 \
    |f(-2)| > |g(-2)| and |f(2)| > |g(2)| \
    "siden" f "er et tredjegradspolynom stiger/synker den mye raskere enn den lineære" g \
    "de vil altså aldri skjære for" x < -2 "eller for" x > 2 "da" f "og linjen divergerer vekk fra hverandre"
  $


= Oppgave 6

+ $
    lim_(x->0) f(x) attach(=, t: upright(x != 0)) lim_(x->0) (-1+x+4x^2cos(1/x)) = -1 + 0 + lim_(x->0) 4x^2cos(1/x) \
    "må bruke skviseteoremet:" \
    |cos(1/x)| <= 1 \
    -4x^2 <= 4x^2cos(1/x) <= 4x^2 quad "snur ikke ulikhet da" 4x^2 > 0 \
    lim_(x->0) -4x^2 <= lim_(x->0) 4x^2cos(1/x) <= lim_(x->0)4x^2 \
    0 <= lim_(x->0) 4x^2cos(1/x) <= 0 \
    lim_(x->0) 4x^2cos(1/x) = 0 \
    lim_(x->0) f(x) = -1 + 0 + 0 = -1 = f(0) ==> "kontinuerlig" \
  $
+ $
    lim_(h->0) frac(f(x+h) - f(x), h) quad x = 0 \
    lim_(h->0) frac(f(h) - f(0), h) \
    lim_(h->0) frac(-1+h+4h^2cos(1/h) - (-1), h) \
    lim_(h->0) (1 + 4h cos(1/h)) = 1 + lim_(h->0) 4h cos(1/h) \
    "bruker igjen skviseteoremet" \
    |cos(1/h)| <= 1 \
    |4h cos(1/h)| <= |4h| \
    -|4h| <= 4h cos(1/h) <= |4h| \
    lim_(h->0) -|4h| <= lim_(h->0) 4h cos(1/h) <= lim_(h->0) |4h| \
    0 <= lim_(h->0) 4h cos(1/h) <= 0 \
    f'(0) = 1 + lim_(h->0) 4h cos(1/h) = 1 + 0 = 1
  $
+ $
    (-1 + x +4x^2 cos(1/x))' \
    1 + 8x cos(1/x) - 4x^2 sin(1/x) (-1/x^2) \
    1 + 8x cos(1/x) + 4 sin(1/x) \
  $
+ $
    lim_(x -> 0) f'(x) = lim_(x -> 0) (1 + 8x cos(1/x) + 4 sin(1/x)) = 1 + lim_(x -> 0) (8x cos(1/x)) + lim_(x -> 0) (4 sin (1/x)) \
    lim_(x -> 0) (4 sin (1/x)) "eksisterer ikke (varierer mellom 4 og -4)"
    f'(x) "er dermed ikke kontinuerlig i" x=0
  $
+ $
    lim_(h->0) frac(f'(0+h) - f'(0), h) \
    lim_(h->0) frac(1 + 8h cos(1/h) + 4sin(1/h), h) \
    lim_(h->0) 1/h (1 + 8h cos(1/h) + 4sin(1/h)) = infinity \
    "eksisterer ikke fordi" lim_(h->0) (4sin(1/h)) "ikke eksisterer (slik som i 6d)" \
    f "er altså ikke dobbeltderiverbar i" 0 \
    "Det er likevel relevant at" f'(0) "har en vertikal tangentlinje i" 0
  $

= Oppgave 7

$f(a) != 0 ==> |f(a)| > 0 ==> (|f(a)|)/2 > 0$

Siden $f$ er kontinuerlig i $a$, vet vi at for $epsilon = (|f(a)|)/2$ finnes det en $delta > 0$ slik at når $|x-a| < delta$ da er
$
  |f(x)-f(a)| < epsilon \
  -epsilon < f(x)-f(a) < epsilon \
  f(a)-(|f(a)|)/2 < f(x) < f(a)+(|f(a)|)/2 \
$

Sjekker først når $f(a) > 0$ ved å bruke venstre ulikhet. Da er $|f(a)| = f(a)$

$
  f(x) > f(a) - f(a)/2 = f(a)/2 > 0
$


Sjekker så når $f(a) < 0$ ved å bruke høyre ulikhet. Da er $|f(a)| = -f(a)$

$
  f(x) < f(a) + (-f(a))/2 = f(a)/2 < 0
$

Da har vi vist at når $f(a) > 0$ er $f(x) > 0$ og at når $f(a) < 0$ er $f(x) < 0$, for alle $x in (a-delta, a+delta)$ som var det vi ville vise.

= Oppgave 8

+ $
    (x-1)sin(pi y) = 4y - 1 \
    u = pi y \
    d/(d x) (x-1) sin(pi y) + (x-1) d/(d u) sin(pi y) (d u)/(d x) = 4 (d y)/(d x) - 0 \
    sin(pi y) + (x-1) cos(pi y) pi (d y)/(d x) = 4 (d y)/(d x) \
    sin(pi y) = (d y)/(d x) (4 - (x-1) cos(pi y) pi) \
    (d y)/(d x) = frac(sin(pi y), 4-(x-1)cos(pi y)pi)
  $
+ $
    (1-1)sin(pi/4) = 4 dot 1/4 - 1 \
    0 = 1 - 1 ==> "kurven går gjennom" (1, 1/4) \
    (d y) / (d x) |_(x = 1, y = 1/4) = frac(sin(pi/4), 4-(1-1)cos(pi/4)pi) = sin(pi/4)/4 = sqrt(2)/8 \
    "tangentlinjen er da:" \
    y = sqrt(2)/8 (x - 1) + 1/4 = sqrt(2)/8 x - sqrt(2)/8 + 1/4 = sqrt(2)/8 x - (sqrt(2)+2)/8
  $
+ $
    (d y)/(d x) = 0 \
    sin(pi y) = 0 quad "gitt at nevneren" 4 - (x-1)cos(pi y)pi != 0 \
    pi y = 0 + 2 pi n or pi y = pi + 2pi n \
    y = 2n or y = 1 + 2n quad n in ZZ \
    "løsningene for" y "gir oss alle partall og oddetall så i praksis er" y = n \
    "Sjekker når nevneren" 4 - (x-1)cos(pi y)pi != 0 \
    x != frac(4, cos(pi y) pi) quad n in ZZ ==> cos(pi n) = plus.minus 1 \
    x != 4/pi and x != -4/pi \
    "Disse trenger vi ikke ta hensyn til da vi skal snart se" x -> plus.minus infinity \
    "Løser nå kurven for" x \
    (x-1)sin(pi y) = 4y -1 \
    x = frac(4y - 1, sin(pi y)) + 1 quad "finner grensen" y->n "fordi " sin(pi n)=0 \
    lim_(y -> n) frac(4y - 1, sin(pi y)) + 1 = plus.minus infinity \
    "Betyr at når" y "nærmer seg å være et heltall går" x->plus.minus infinity \
    (d y)/(d x) = 0 "når" x->plus.minus infinity "i punktene" (x, n) "for alle" n in ZZ
  $
+ $
    (x-1)sin(pi y) = 4y -1 \
    lim_(x -> infinity) (x-1)sin(pi y) = lim_(x -> infinity) (4y - 1) \
    lim_(x->infinity) ((x-1)sin(pi y) - 4y + 1) = 0 \
    x -> -infinity "er det samme" \
    "vet da at uttrykket aldri skjærer x-aksen da den er asymptotisk og blir derfor aldri" y = 0
  $
+ #[
    Vet at hele kurven er kontinuerlig da den består av kontinuerlige uttrykk (trigonometri og polynomer).
    Vet at $(1, 1/4)$ er et punkt på kurven slik vist i 8b. Vet også at $x=-1$ har $y>0$ fordi x-aksen ikke skjæres (slik vist i 8d). \ \
    I følge skjæringsteoremet så må kurven skjære y-aksen mellom $(0,0)$ og $(0,1/2)$ siden kurven er kontinuerlig mellom $(-1, y)$ og $(1, 1/4)$, $0<y<1/2$ \ (vet at $y<1/2$ fordi vi ser grafisk at kurven synker fra x=1 til x=-1).
  ]

