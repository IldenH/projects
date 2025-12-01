-- part 2 task

import Data.Char

parseInt :: String -> Int
parseInt = foldl (\acc x -> acc * 10 + x) 0 . map digitToInt

parseDial :: String -> Int
parseDial ('R' : xs) = parseInt xs
parseDial ('L' : xs) = -parseInt xs

isInvalid :: Int -> Bool
isInvalid x = x < 0 || x > 99

fixInvalid :: Int -> Int
fixInvalid x
  | x > 99 = subtract 100 . last . takeWhile (> 99) . iterate (subtract 100) $ x
  | x > 0 = x
  | otherwise = (+) 100 . last . takeWhile (< 0) . iterate (+ 100) $ x

handleInvalid :: Int -> Int
handleInvalid x
  | isInvalid x = fixInvalid x
  | otherwise = x

replicateDial :: String -> [Int]
replicateDial x
  | d > 0 = replicate d 1
  | otherwise = replicate (-d) (-1)
  where
    d = parseDial x

main :: IO ()
main =
  do
    contents <- getContents
    putStrLn $ show . length . filter (== 0) . scanl (\acc x -> handleInvalid (acc + x)) 50 . concat . map replicateDial . lines $ contents
