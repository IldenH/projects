import System.Random

data Person = Person
  { name :: String,
    birth :: Int,
    death :: Int
  }
  deriving (Show, Eq, Ord)

randPerson :: (RandomGen g) => g -> Person
randPerson g =
  let (death, _) = randomR (-400, 2026) g
      (age, _) = randomR (0, 100) g
      birth = death - age
      name = take 10 $ randomRs ('a', 'z') g
   in Person name birth death

people = map (randPerson . mkStdGen) [0 ..]

touchable :: Person -> Person -> Bool
touchable x y
  | birth x >= birth y && death x <= death y = True
  | birth y >= birth x && death y <= death x = True
  | death y <= death x && death y >= birth x = True
  | death x <= death y && death x >= birth y = True
  | otherwise = False

touchablePeople ps = [p | p <- ps, all (touchable p) ps]
