#import "@preview/calmly-touying:0.2.0": *

#show: calmly.with(
  config-info(
    title: [Fusjon energi],
    subtitle: [Hvordan brukes fysikk til å lage hydrogen bomber og fremtidens energi?],
    author: [Håvard],
    date: [2026-05-18],
    institution: [Amalie Skram VGS],
  ),
  colortheme: "dracula",
)

#title-slide()

== Fusjon

#place(
  center,
  image(
    "images/fusion.svg",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
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


== Ivy Mike 1952 - første hydrogen bombe, 10.4 megaton TNT

#place(
  center,
  image(
    "images/Ivy_Mike_002.jpg",
    width: 100%,
    height: 100%,
    fit: "cover",
  ),
)


#figure-slide-split(
  image("images/Little_Boy_bomb.jpg"),
  image("images/Fat_Man.jpg"),
  title: [1945 sammenligning],
  caption-left: [
    Little Boy (hiroshima):	13–16 kiloton TNT
  ],
  caption-right: [
    Fat Man (nagasaki): 21 kiloton TNT
  ],
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

== T-3A i 1969 av Sovjet Unionen

#place(
  center,
  image(
    "images/T-3A.png",
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
    Q = frac("fusjon energi ut", "varme energi inn")
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
        Energi tap
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
        Energi gevinst
      ]
    ],
  )
]

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

