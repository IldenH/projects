-- part 2

import Data.Char
import Data.List

example :: [String]
example =
  [ "123 328  51 64 ",
    " 45 64  387 23 ",
    "  6 98  215 314",
    "*   +   *   +  "
  ]

exampleTrans = transpose $ example

nums :: [String] -> [[String]]
nums [] = []
nums s =
  let (x, xs) = break (\x -> all isSpace x) s
   in x : nums (drop 1 xs)

contains :: String -> Char -> Bool
contains s c = length go /= 0
  where
    go = filter (== c) s

calculate :: [String] -> Int
calculate (x : xs) =
  case x of
    "+" -> sum $ map read $ xs
    "*" -> product $ map read $ xs

parseProblems :: [[String]] -> [[String]]
parseProblems = map (\(x : xs) -> if x `contains` '*' then "*" : init x : xs else "+" : init x : xs)

main :: IO ()
main = do
  contents <- getContents
  print . sum . map calculate . parseProblems . nums . transpose . lines $ contents
