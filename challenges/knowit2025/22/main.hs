import Data.Char

value x
  | x `elem` "Md+" = 1
  | otherwise = -ord x

solve :: [String] -> Int -> [Int] -> Int
solve [] _ acc = sum acc
solve (x : xs) n acc = solve xs (n + 1) (n * ok + bad : acc)
  where
    ys = map value x
    ok = sum $ filter (== 1) ys
    bad = sum $ filter (< 0) ys

main :: IO ()
main = do
  contents <- lines <$> readFile "input.txt"
  print $ solve contents 1 []
