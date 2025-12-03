# noen tanker og ideer til denne oppgaven

"12134"

sorted = [4,3,2,1,1]

elemIndex 4 "12134" -> Just 4
replace 4 '0' "12134" -> "12130"

sorted = drop 1 sorted -> [3,2,1,1]

elemIndex 3 "12130" -> Just 3
replcae 3 '0' "12130" -> "12100"

sorted = drop 1 sorted -> [2,1,1]

elemIndex 2 "12100" -> Just 1
replace 1 '0' "12100" -> "10100"

sorted = drop 1 sorted -> [1,1]

elemIndex 1 "10100" -> Just 0
replace 0 '0' "10100" -> "00100"

sorted = drop 1 sorted -> [1]

elemIndex 1 "00100" -> Just 2
replace 2 '0' "00100" -> "00000"

## Vent vent vent

ghci> sorted
"988821111111"
ghci> raw
"818181911112111"
ghci> expected
"888911112111"
ghci> twelves sorted raw []
[('1',10),('1',9),('1',8),('1',7),('1',5),('1',3),('1',1),('2',11),('8',4),('8',2),('8',0),('9',6)]
ghci>

8 8 8 9
0123456789abcdef

aaaa jeg må liksom endre posisjonen på en måte

## ok kanskje dette i stedet

25415783
2 ++ max 5415783 -> 28

2536
2000,500,30,6
høyere tall mer prioritet så da blir det 53 som høyeste par

358426
300000,50000,8000,400,20,6

234234234234278
2,3,4,2,3,4,2,3,4,2,3,4,2,7,8
434234234278

## :o

24368
elemIndex 9 - nothing
elemeindex 8 - Just 4 -> length xs - 4 - 1 = 0 som er < 3 så nuh uh
elemindex 7 - nothing
elemindex 6 - Just 3 -> length xs - 3 -1= 1 som er < 3 så nuh uh
elem 5 - not
elem 4 - Just 1 -> length xs - 1 -1= 3 som er >= 3 så yuh uh

så looper vi kun på alt etter 4 (index 1)
elem 9 - not
elem 8 - 4 - len xs - 4 = 0 som er < 2 nuh uh
elem 7
elem 6 - 3 - len xs - 3 = yuh uh

elem 9
elem 8 - len xs - 4 = 1 som >= 1 yuh uh
