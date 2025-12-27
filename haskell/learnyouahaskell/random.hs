import System.Random

coins :: StdGen -> (Bool, Bool, Bool)
coins g =
  let (c1, g1) = random g
      (c2, g2) = random g1
      (c3, g3) = random g2
   in (c1, c2, c3)

roll :: StdGen -> Int
roll = fst . randomR (1, 6)

main = do
  gen <- getStdGen
  print $ roll gen
