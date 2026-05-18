#import "@preview/calmly-touying:0.2.0": *

#show: calmly.with(
  config-info(
    title: [Fusjonsenergi],
    subtitle: [Hvordan brukes fysikk til å lage hydrogenbomber og fremtidens energi?],
    author: [Håvard],
    date: [2026-05-18],
    institution: [Amalie Skram VGS],
  ),
  colortheme: "dracula",
)

#title-slide()

#figure-slide-split(
  image("images/fission.svg"),
  image("images/fusion.svg"),
  title: [Fisjon og Fusjon],
)

#equation-slide(
  $E = m c^2$,
  title: [Masse-Energi Ekvivalens - Albert Einstein i 1905],
  definitions: [
    $E$ — Energi \
    $m$ — Masse \
    $c$ — Lysets hastighet
  ],
)

== Fusjon i solen - Arthur Eddington 1920

#place(
  center,
  image(
    "images/fusion-sun.svg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)


#figure-slide-split(
  image("images/Little_Boy_bomb.jpg"),
  image("images/Fat_Man.jpg"),
  title: [1945 - atombomber blir brukt],
  caption-left: [
    Little Boy (hiroshima):	13–16 kilotonn TNT
  ],
  caption-right: [
    Fat Man (nagasaki): 21 kilotonn TNT
  ],
)


== Ivy Mike 1952 - første hydrogenbombe, 10.4 megatonn TNT

#place(
  center,
  image(
    "images/Ivy_Mike_002.jpg",
    width: 100%,
    height: 100%,
    fit: "cover",
  ),
)




== Scylla I i 1958 av USA, $theta$-pinch utforming

#place(
  center,
  image(
    "images/Scylla_I_in_1958.jpg",
    width: 100%,
    height: 100%,
    fit: "cover",
  ),
)

== $theta$-pinch, $I_C$: primary current, $I_p$: induced plasma current

#place(
  center,
  image(
    "images/theta-pinch.webp",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)

== Tokamak T-1 i 1958 av Kurchatov i Russland

#place(
  center,
  image(
    "images/Tokamak_T-1.jpg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)

== T-3A i 1969 av Sovjetunionen

#place(
  center,
  image(
    "images/T-3A.png",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)

== Joint European Torus 1991

#place(
  center,
  image(
    "images/JET.jpg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)


== EAST i 2006, Kina, (bilde: 2017)

#place(
  center,
  image(
    "images/EAST_tokamak.jpg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)

== Inertial Confinement Fusion


== Joint European Torus

== Virkningsgrad


#align(center)[
  #set text(size: 28pt)

  $
    Q = frac("fusjonsenergi ut", "varmeenergi inn")
  $
]

#v(2em)

#align(center)[
  #grid(
    columns: 3,
    gutter: 2cm,

    align(center)[
      #text(size: 40pt)[
        $
          Q < 1
        $
      ]

      #v(0.4em)

      #text(size: 22pt)[
        Energitap
      ]
    ],

    align(center)[
      #text(size: 40pt)[
        $
          Q = 1
        $
      ]

      #v(0.4em)

      #text(size: 22pt)[
        Energi lik
      ]
    ],

    align(center)[
      #text(size: 40pt)[
        $
          Q > 1
        $
      ]

      #v(0.4em)

      #text(size: 22pt)[
        Energigevinst
      ]
    ],
  )
]

== 2022 National Ignition Facility, USA, $Q = 1.5$

#place(
  right,
  image(
    "images/NIF_building_layout.png",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)


== 2022 National Ignition Facility, USA, $Q = 1.5$

#place(
  center,
  image(
    "images/NIF_target_chamber_2.jpg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)


== NIF 2022 - 2025

#place(
  center,
  image(
    "images/NIF_experiments.jpg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)

// #focus-slide(
//   [
//     - $E = m c^2$
//     - Fusjon i solen
//     - Hydrogen bomber
//     - $theta$-pinch
//     - Tokamak
//     - Inertial Confinement Fusion
//   ],
// )


// https://www.nrk.no/tromsogfinnmark/fusjonsenergi-kan-vaere-losningen-vi-trenger.-men-regjeringen-vil-ikke-snakke-om-det-1.15244143
// "Ifølge Garcia kan vi ved hjelp av et badekar med havvann og litiumet fra batteriet til en bærbar PC, produsere den energien en europeer bruker i løpet av et helt liv. Det tilsvarer å brenne 3.000 tonn olje."
#focus-slide(
  [Bærekraftig?],
)
