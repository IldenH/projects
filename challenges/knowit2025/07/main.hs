import Data.List

match :: String -> String -> (Int, Int) -> Bool
match xs' t' (min', max') = go xs' t' (min', max') max' True
  where
    go _ [] _ _ _ = True
    go [] _ _ _ _ = False
    go (x : xs) ts@(t : ts') (min, max) n start
      | n > max && not start = False
      | x == t && n >= min = go xs ts' (min, max) 0 False || next
      | otherwise = next
      where
        next = go xs ts (min, max) (n + 1) start

isTroll s = match s "troll" (1, 5)

isNisse s
  | head s == 'n' = False
  | last s == 'e' = False
  | otherwise = match s "nisse" (0, 2)

main :: IO ()
main = do
  contents <- getContents
  print . length . filter (\x -> isTroll x || isNisse x) . lines $ contents
