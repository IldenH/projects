import Data.Char

parseInt :: String -> Int
parseInt = foldl (\acc x -> acc * 10 + x) 0 . map digitToInt

pairs :: String -> [Int]
pairs [] = []
pairs (x : xs) = [parseInt [x, y] | y <- xs] ++ pairs xs

main :: IO ()
main = do
  contents <- getContents
  putStr $ show . sum . map maximum . map pairs . lines $ contents
