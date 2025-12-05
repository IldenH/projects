-- part 2 completely different approach (with help from AI)
-- main2.hs is basicly me trying to figure out interval merging without knowing about interval merging

import Data.List

type Range = (Int, Int)

parseRange :: String -> Range
parseRange s =
  let (min, _ : max) = break (== '-') s
   in (read min, read max)

merge :: [Range] -> [Range]
merge = foldr go [] . sort
  where
    go x [] = [x]
    go (a, b) ((c, d) : rs)
      | b < c = (a, b) : (c, d) : rs
      | otherwise = (min a c, max b d) : rs

length' :: Range -> Int
length' (a, b) = b - a + 1

main :: IO ()
main = do
  rangesContents <- readFile "ranges.txt"
  let ranges = map parseRange $ lines rangesContents
  print $ sum . map length' . merge $ ranges
