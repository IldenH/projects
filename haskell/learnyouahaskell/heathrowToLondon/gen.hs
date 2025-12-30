import System.Random

main = do
  gen <- getStdGen
  let rs = randomRs (1, 1000000) gen :: [Int]
  writeFile "random.txt" $ unlines $ map show $ take (3 * 1000) rs
