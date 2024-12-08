# Perfekte primtalv

Alva Lovelace mener det er på høy tid at alvene kommer med sitt bidrag til matematikken og definerer to nye avanserte typer tall: primtalv og perfekte primtalv. De er definert som følger:

For primtalv n, ta de n første primtallene og skriv dem under hverandre fra venstre. Summer sifrene langs kolonnene, multipliser summene med 1 for kolonne 1, 10 for kolonne 2, 100 for kolonne 3 etc. og til slutt summer disse produktene.

Beregningen av primtalv n=5 og n=27 ser slik ut:

```
      n=5       |          n=27
                |
                |     2
                |    +3
                |    +5
                |    +7
  2             |    +1      1
+ 3             |    +1     +3
+ 5             |   ...    ...
+ 7             |    +1     +0     +1
+ 1     1       |    +1     +0     +3
 =      =       |     =      =      =
 18     1       |   113    103      4
* 1   *10       |  *  1   * 10   *100
  =     =       |     =      =      =
 18  + 10 = 28  |   113 + 1030  + 400 = 1543
```

Primtalv 5 er 28 og primtalv 27 er 1543.

Hvis et primtalv også er et vanlig primtall kaller vi det et perfekt primtalv. 28 er et primtalv, men det er ikke et primtall så det er ikke et perfekt primtalv. 1543 er et perfekt primtalv fordi det er et primtalv og også et vanlig primtall.

Hvor mange perfekte primtalv finnes det som er lavere enn 10 000 000?
