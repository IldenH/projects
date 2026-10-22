#set page(
  numbering: "1",
)
#set text(font: "DejaVu Sans", size: 11pt, lang: "no")
#set enum(indent: 1em, numbering: "a)", spacing: 1.5em)
#show heading: set block(below: 1em)

#align(center)[
  #text(16pt, weight: "bold")[MAT111 - Obligatorisk innlevering 2]
]

#v(1em)

= Oppgave 1

+ $
    x in [6/((12n+11)pi), 6/((12n+7)pi)] \
    1/x in [((12n+7)pi)/6, ((12n+11)pi)/6] \
    1/x in [2pi n + 7/6 pi, 2pi n + 11/6 pi] \
    "perioden er lik" 2pi ", betrakter endepunktene for en vilkårlig periode" \
    sin(7/6 pi) = - sin(1/6 pi) = - 1/2 \
    sin(11/6 pi) = sin(-1/6 pi) = - 1/2 \
    "vet så ved enhetssirkelen at sinus er på sitt høyeste i disse to endepunktene" \
    sin(1/x) <= -1/2 \
    4sin(1/x) <= -4/2 = -2 \
    "sjekker så cosinus leddet i" f' \
    x <= 6/((12n+7)pi) <= 6/(19pi) < 1/8 \
    x < 1/8 \
    cos(1/x) <= 1 \
    8x cos(1/x) <= 8x < 8 dot 1/8 = 1 \
    f'(x) = 1 + 8x cos(1/x) + 4sin(1/x) < 1 + 1 -2 = 0 \
    f'(x) < 0, x in [6/((12n+11)pi), 6/((12n+7)pi)] \
  $
+ Siden $f$ svinger uendelig mye mellom å være strengt voksende og å være strengt avtagende i et omegn om $0$ er den ikke strengt voksende i et omegn om $0$. Dette strider ikke mot Teorem 12 i 2.8 da det teoeremet sier at $f'(x)>0$ for alle $x$ i omegnet om $0$, ikke bare for $f'(0)$, og at $f'(x)$ er kontinuerlig i omegnet, som det ikke er fordi $f'(x)$ er ikke kontinuerlig i $0$ per oblig1.
+ Det som står i sinus boken stemmer så lenge funksjonen er kontinuerlig i punktet. Siden de har valgt et polynom som eksempel på bildet, virker altså det de sier om at funksjonen stiger/avtar i omegn om punkten, siden alle polynomer er kontinuerlige.
+ En tilstrekelig tillegsbetingelse er at $f'(x)$ er kontinuerlig i punktet. Da vil $f(x) > f(x_0)$ for alle $x in (x, x+delta)$ og $f(x) < f(x_0)$ for alle $x in (x-delta, x)$ gitt $delta > 0$ og $f'(x_0) > 0$.

= Oppgave 2

+ $
    f(x) = 2e^(-2x) - e^(-x) + 1 \
    "bruker at " (e^(k x))' = k e^(k x) \
    f'(x) = -4e^(-2x) + e^(-x)
  $
+ $
    lim_(x -> infinity) f(x) = lim_(x->infinity) (2/(e^(2x)) - 1/(e^x) + 1) = 0 - 0 + 1 = 1 \
    lim_(x -> -infinity) f(x) = lim_(x->infinity) f(-x) = lim_(x->infinity) (2e^(2x) - e^x + 1) = lim_(x->infinity) e^x (2e^2 - 1 + 1) = infinity
  $
+ $
    "finner ekstremalpunkt" \
    f'(x) = 0 \
    -4e^(-2x) + e^(-x) = 0 \
    4e^(-2x) = e^(-x) \
    ln(4e^(-2x)) = -x \
    ln(4) - 2x = -x \
    x = ln(4) \
    "kun ett ekstremalpunkt" ==> f "er enten strengt avtagende eller strengt voksende på hver side av punktet" \
    "vil finne om" f(ln(4)) < 1 ==> "strengt voksende når" x in [ln(4), infinity) \
    "eller motsatt" f(ln(4)) > 1 ==> "strengt avtagende når" x in [ln(4), infinity) \
    f(ln(4)) < 1 \
    2e^(-2 ln(4)) - e^(- ln(4)) + 1 < 1 \
    2e^(-2 ln(4)) - e^(- ln(4)) < 0 \
    -ln(4) (2e^(-2) - 1) < 0 \
    2e^(-2) - 1 > 0 \
    e^(-2) > 1/2 \
    e^2 > 2 \
    "Det vil si at" f "er strengt voksende i intervallet" x in [ln(4), infinity) \
    "og strengt avtagende i intervallet" x in (-infinity, ln(4)] "fordi fra oppgave b så er" lim_(x->-infinity) f(x) = infinity
  $
+ $f$ har ikke en invers funksjon da den ikke er strengt voksende eller strengt avtagende i hele sin definisjonsmengde. Den har likevel to mulige inverse funksjoner dersom man begrenser definisjonsmengden til å være ett av intervallene nevnt i oppgave c.
+ $
    ln(4) < 2 \
    4 < e^2 \
    2^2 < e^2 \
    "Vil si at" 2 in [ln(4), infinity) = I
  $
+ $
    V(g^(-1)) = D(g) = I = [ln(4), infinity) \
    D(g^(-1)) = V(g) = [g(ln(4)), lim_(x->infinity) g(x)) = [0.875, 1) \
  $
+ $
    y = 2e^(-2x) - e^(-x) + 1 \
    y - 1 = e^(-x) (2e^(-2) - 1) \
    frac(y - 1, 2e^(-2) - 1) = e^(-x) \
    e^(x) = frac(2e^(-2) - 1, y - 1) \
    x = ln(frac(2e^(-2) - 1, y - 1)) \
    g^(-1)(x) = ln(frac(2e^(-2) - 1, x - 1)) \
    x != 1 "fordi" 1 in.not D(g^(-1)) "så nevner blir aldri null"
  $


= Oppgave 3

+ $
    y'(t) = -1/5 y(t) + M, y(0) = 0 \
    y(0) = 0 "gir mening da, per antakelse, er kroppen fritt for stoffet idet inntaket starter." \
    -1/5 y(t) = -20% dot y(t) "gir mening fordi det skilles ut" 20% "av mengden stoff i kroppen per dag." \
    +M "gir mening for endringsraten da det er det du inntar hver dag." \
    "Subsituterer inn" u(t) = y(t) - 5M "altså" y(t) = u(t) + 5M \
    u'(t) = -1/5 (u(t) + 5M) + M = -1/5 u(t) - M + M = -1/5 u(t) \
    u(0) = y(0) - 5M = - 5M
  $
+ $
    u'(t) = -1/5 u(t) ==> u(t) = u(0) e^(-1/5 t) = -5M e^(-1/5 t) \
    y(t) = u(t) + 5M = -5M e^(-1/5 t) + 5M \
  $
+ $
    "vil finne når:" lim_(t -> infinity) y(t) = 100 \
    lim_(t -> infinity) (-5M e^(-1/5 t) + 5M) = lim_(t -> infinity) ((-5M)/(e^(1/5 t)) + 5M) = 5M = 100 ==> M = 20 \
    "Man kan innta" 20 "gram per dag uten at det er helseskadelig"
  $

= Oppgave 4

Kaller avstand mellom båten og kaien for $x$ og taulengden for $s$.
Bruker pytagoras:

$
  s^2 = x^2 + 8^2 \
  x^2 = s^2 - 8^2 \
  x = sqrt(s^2 - 8^2) = sqrt(17^2 - 8^2) = 15 "m når" s = 17
$

Kan så derivere begge sider av pytagoras ligningen.

$
  d/(d t) s^2 = d/(d t) x^2 + d/(d t) 8^2 \
  2s (d s)/(d t) = 2x (d x)/(d t) \
  s (d s)/(d t) = x (d x)/(d t) \
  17 (-30) = 15 (d x)/(d t) \
  (d x)/(d t) = (17 (-30))/15 = 17 (-2) = -34 "m/min"
$

Båten nærmer seg kaien med en fart på 34m/min i retning mot kaien, når taulengden er 17m

= Oppgave 5

Hvis $s_A (t)$ er hvor langt jeg har løpt og $s_B (t)$ er hvor langt venninnen har løpt, vet vi at
$s_A (t_0) = s_B (t_0)$ og at $s_A (t_1) = s_B (t_1)$ hvis $t_0$ er starttidspunktet og $t_1$ er slutttidspunktet.

Vet så at avstanden mellom løperene er $f(t) = s_A (t) - s_B (t)$. Og at avstanden er null i start- og slutttidspunktet: $f(t_0) = 0$ og $f(t_1) = 0$.

Det betyr i følge Rolle's teorem at i intervallet $(t_0, t_1)$ finnes det minst ett tidspunkt $t_c$ hvor $f'(t_c) = 0$.

$f'(t) = s_A '(t) - s_B '(t) = v_A (t) - v_B (t)$. Vet da at når $f'(t_c) = 0$ er $v_A (t_c) = v_B (t_c)$ som var det vi ville vise.


= Oppgave 6

+ $
    lim_(x -> 0) f(x) = f(0) = 1/2 ==> f "kont i" 0 \
    lim_(x -> 0) frac(cos(x) + sin(x) - 1, x + tan^(-1)(x)) quad "'0/0' uttrykk, bruker L'Hôpital" \
    lim_(x -> 0) frac(-sin(x) + cos(x), 1 + 1/(1+x^2)) = frac(-0 + 1, 1 + 1/(1 + 0)) = 1/2 = f(0) \
    f "er kontinuerlig i" 0
  $
+ $
    lim_(h -> 0) frac(f(0+h)-f(0), h) \
    lim_(h->0) frac(frac(cos(h)+sin(h)-1, h+tan^(-1)(h)) - 1/2, h) \
    lim_(h->0) frac(cos(h)+sin(h)-1 - 1/2 (h+tan^(-1)(h)), h^2+h tan^(-1)(h)) \
    lim_(h->0) frac(2 cos(h)+2 sin(h)-2 - h - tan^(-1)(h), 2 h^2+ 2 h tan^(-1)(h)) quad "'0/0', bruker L'Hôpital"\
    lim_(h->0) frac(-2 sin(h) + 2 cos(h) - 1 - 1/(1+h^2), 4h + 2 tan^(-1)(h) + (2 h)/(1 + h^2)) quad "'0/0', bruker igjen L'Hôpital" \
    lim_(h->0) frac(-2 cos(h) - 2 sin(h) + 1/((1+h^2)^2) 2h, 4 + 2/(1 + h^2) + (2 + 2h^2 - 4h^2)/(1+h^2)^2) \
    lim_(h->0) frac(-cos(h) - sin(h) + h/((1+h^2)^2), 2 + 1/(1 + h^2) + (1 - h^2)/(1+h^2)^2) \
    frac(-1 - 0 + 0/1, 2 + 1/1 + 1/1^2) = -frac(1, 4) ==> f "er deriverbar i" 0
  $
+ $
    lim_(x -> infinity) f(x) = lim_(x->infinity) frac(cos(x) +sin(x) -1, x+tan^(-1)(x)) \
    "nevneren: " x + tan^(-1)(x) -> infinity "når" x -> infinity "mens telleren konvergerer ikke og forblir lavt" \
    lim_(x->infinity) f(x) = 0 \
    lim_(x->-infinity) f(x) = -0 = 0 \
    f "har horisontale asymptoter" y = 0 "når" x -> plus.minus infinity \
    lim_(x -> a^+) f(x) = plus.minus infinity "eller" lim_(x->a^-) f(x) = plus.minus infinity "er definisjon for vertikale asymptoter" \
    "for at" f(x) = frac(cos(x)+sin(x)-1, x+tan^(-1)(x)) "skal gå mot" infinity "må nevneren gå mot" 0 "siden teller ikke går mot" infinity \
    x + tan^(-1)(x) -> 0 "når" x -> 0 "men vet fra oppgave 6a at" lim_(x->0) f(x) = 1/2 != plus.minus infinity \
    f "har altså ingen vertikale asymptoter"
  $
+ Bruker teoerm 8 i seksjon 4.4 fra boken. Siden $f$ er kontinuerlig på $(-infinity, infinity)$, slik vi fant i 6a, og at $lim_(x->infinity)=lim_(x->-infinity)=0$ fra oppgave 6c. Kan da sjekke om det finnes en $u$ slik at enten: $f(u) > 0 ==>$ finnes en global maksimalverdi, eller at $f(u) < 0 ==>$ finnes en global minimalverdi. \ \ Vet at $f(0) = 1/2 > 0 ==>$ finnes en global maksimalverdi. \ Sjekker noen verdier av $u$: $f(1) = 0.21$, $f(2) = -0.16 < 0 ==>$ finnes en global minimalverdi.

= Oppgave 7

+ $
    f(x) approx P_4(x) = sum_(i=0)^k (f^((i))(0))/(i!)(x - 0)^i = sum_(i=0)^k ((e^0 cos(0))^((i))(0))/(i!)x^i \
    = f(0) + f'(0)x + (f''(0))/2 x^2 + (f'''(0))/(3!) x^3 + (f^((4))(x))/(4!) x^4 \
    = e^0 cos(0) + (e^0 cos(0) - e^0 sin(0))x + (- 2 e^0 sin(0))/2 x^2 + (-2 e^0 sin(0) - 2 e^0 cos(0))/6 x^3 + (-4 e^0 cos(0))/24 x^4 \
    = 1 + x - 1/3 x^3 - 1/6 x^4 \
  $
+ $
    E_4(x) = (f^((5))(s))/(5!) x^5 = (e^s (sin(s) - cos(s)))/30 x^5, quad 0 < s < x <= pi/4 \
    "begrenser" f^((5))(s) \
    sin(s) < cos(s) ==> sin(s) - cos(s) < 0, quad 0 < s < pi/4 \
    f^((5))(s) < 0 ==> E_4(x) < 0 "fordi" x > 0 \
    "sjekker så nedre grense" \
    "siden" f^((5))(pi/4) < f^((5))(0) "bruker jeg" s > 0 "i stedet for" s < pi/4 \
    f^((5))(0) > e^0 (sin(0) - cos(0)) = -1 \
    E_4(x) > -1/30 x^5 \
    -1/30 x^5 < E_4(x) < 0 \
    P_4(x) - 1/30 x^5 < P_4(x) + E_4(x) < P_4(x) \
    P_4(x) - 1/30 x^5 < f(x) < P_4(x)
  $
+ $
    P_4(3/4) - 1/30 (3/4)^5 < f(3/4) < P_4(3/4) \
    P_4(3/4) = 1 + 3/4 - 1/3 (3/4)^3 - 1/6 (3/4)^4 = 797/512 \
    797/512 - 81/10240 < f(3/4) < 797/512 \
    "har 3 desimaler nøyaktighet pga" 81/10240 approx 0.00791015... approx 0.008 \
    f(3/4) "ligger i" (1.548, 1.556)
  $

= Oppgave 8

+ $
    f(x) = x ln x + x - 6
    f(e) = e ln e + e - 6 = 2e - 6 < 0 "fordi" e < 3 \
    f(3) = 3 ln 3 + 3 - 6 = 3 ln 3 - 3 = 3 (ln 3 - 1) > 0 "fordi" ln 3 > 1 "fordi" 3 > e^1 \
    "vet da ved skjæringsteoremet at det finnes en" r in [e, 3] \ "som oppfyller likningen fordi" f(e) < 0 < f(3)
  $
+ $
    "Definerer arealet til rektanglet:" \
    A(x) = y(x) dot x = 2ln(6 - x) x \
    A'(x) = 2 (x ln(6-x))' = 2 (ln(6-x) - x/(6 - x)) \
    A'(x) = 0 \
    2 ln(6-x) - (2x)/(6-x) = 0 \
    ln(6-x) = x/(6-x) \
    (6-x)ln(6-x) = x \
    "substituerer" r = 6-x \
    r ln(r) = 6 - r \
    r ln(r) + r - 6 = 0 \
    "som er på formen av likningen i oppgave 8a" \
    "når vi finner" r "slik gjøres i de neste deloppgavene har man da:" \
    A(x), x = 6 - r \
    "det gir det største arealet til bokhyllen" \
    "og hvor langt bokhylleveggen skal være fra veggen altså" x
  $
+ $
    r ln r + r - 6 = 0 \
    r ln r + r = 6 \
    r = 6 - r ln r \
    "og"
    r ln r + r - 6 = 0 \
    r (ln r + 1) = 6 \
    r = frac(6, ln r + 1) \
    "kaller første for" f(x) = 6 - x ln x "og andre for" g(x) = frac(6, ln x + 1) \
    x_1 = f(x_0) = f(3) = 6 - 3 ln 3 = 2.704 < e quad "gikk vekk fra hvor vi vet løsnignen ligger:" [e, 3] \
    x_1 = g(x_0) = g(3) = frac(6, ln 3 + 1) = 2.859 quad "forble inne i løsningsintervallet"
  $
+ $
    "for at fikspunktiterasjon skal virke må" |f'(x)| < 1 "for en" x "i et omegn om løsningen" \
    "vet at" f'(x) = - ln x - 1 "da er" f'(e) = -2 < -1 ==> "kan ikke bruke fikspunktiterasjon" \
    "vet så at" g'(x) = - frac(6, (ln x + 1)^2) 1/x "og at" g'(e) = - frac(6, 2^2) 1/e = - 3/(2e) > -1 ==> "kan bruke fikspunktiterasjon" \
  $
+ $
    f(x) = x ln x + x - 6, x > 0 \
    x_1 = x_0 - frac(f(x_0), f'(x_0)) = 3 - frac(3 ln 3 - 3, ln 3 + 2) = frac(3 ln 3 + 6 - 3 ln 3 + 3, ln 3 + 2) = 9/(ln 3 + 2) \
    f''(x) = 1/x > 0 "fordi" x > 0 "betyr positiv krumning for hele" f \
    "vet da at tangentlinjen" y = f(x_0) + f'(x_0)(x-x_0) \
    "vil være under" f "og derfor vil" r < x_1 <= x_0
  $
+ $
    "har allerde gjort første steg for induksjonsbeviset i oppgave 8e" \
    x_(n+1) < x_n \
    x_(n+1) = x_n - (f(x_n))/(f'(x_n)) \
    "siden" f(r) = 0 "og" x_n > r "og at" f "er strengt voksende, betyr det at" f(x_n) > 0 \
    f'(x_n) > 0 "fordi" f "er strengt voksende" \
    "dermed er brøken" (f(x_n))/(f'(x_n)) > 0 "og vi har vist at" x_(n+1) "er" x_n "minus noe positivt" ==> x_(n+1) < x_n \
    "fra oppgave 8e er alle tangentlinjer tegnet på en konveks funksjon vil ligge under grafen" \
    "vi får dermed at" r < x_(n+1) \
    "og har derved vist at" r < x_(n+1) < x_n <= x_0 = 3
  $
