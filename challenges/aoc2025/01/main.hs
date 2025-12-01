import Data.Char

parseInt :: String -> Int
parseInt = foldl (\acc x -> acc * 10 + x) 0 . map digitToInt

parseDial :: String -> Int
parseDial ('R' : xs) = parseInt xs
parseDial ('L' : xs) = -parseInt xs

isInvalid x = x < 0 || x > 99

fixInvalid :: Int -> Int
fixInvalid x
  | x > 99 = subtract 100 . last . takeWhile (> 99) . iterate (subtract 100) $ x
  | x > 0 = x
  | otherwise = (+) 100 . last . takeWhile (< 0) . iterate (+ 100) $ x

main :: IO ()
main = do
  contents <- getContents
  putStrLn $ show . length . filter (== 0) . scanl1 (\acc x -> if isInvalid (acc + x) then fixInvalid (acc + x) else acc + x) . (:) 50 . map parseDial . lines $ contents
