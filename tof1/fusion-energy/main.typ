#import "@preview/calmly-touying:0.2.0": *

#show: calmly.with(
  config-info(
    title: [Fusjon energi],
    subtitle: [Fremtidens energi?],
    author: [Håvard],
    date: [2026-05-07],
    institution: [Amalie Skram VGS],
  ),
)

#title-slide()

== Energi formler


#align(center)[
  #set text(size: 28pt)

  $
    Q = frac("fusion power output", "heating power input")
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

== Kort bakgrunnshistorie

- 1905 Albert Einstein - $E = m dot c^2$
- 1920 Arthur Eddington - fusjon i solen
- 1952 hydrogen bomber
- 1958 Scylla-I første kontrollerte fusjon eksperiment

== Scylla I i 1958 av usa

#place(
  center,
  image(
    "images/Scylla_I_in_1958.jpg",
    width: 100%,
    height: 100%,
    fit: "cover",
  ),
)

== T-3A i 1969 av sovjet union

#place(
  center,
  image(
    "images/T-3A.png",
    width: 100%,
    height: 100%,
    fit: "contain",
  ),
)
