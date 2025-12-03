import Data.Char
import Data.List

good = (* 50)

bad = (* (-25))

pepperkake = (* 15)

calculate :: (Int, Int, Int) -> Int
calculate (x, y, z) = good x + bad y + pepperkake z

parseInt :: String -> Int
parseInt = foldl (\acc x -> acc * 10 + x) 0 . map digitToInt

parseLine :: String -> (String, Int)
parseLine s =
  let (name, rest1) = break (== ',') s
      (good, rest2) = break (== ',') (drop 1 rest1)
      (bad, rest3) = break (== ',') (drop 1 rest2)
      (pepperkake, _) = break (== ',') (drop 1 rest3)
   in (name, calculate (parseInt good, parseInt bad, parseInt pepperkake))

main :: IO ()
main = do
  contents <- getContents
  let values = sortOn snd $ map parseLine $ drop 1 $ lines $ contents
  putStr $ intercalate "," $ map (\(x, y) -> x ++ " " ++ show y) $ take 3 (reverse values) ++ reverse (take 3 values)
