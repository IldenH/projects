import Data.List

calculate :: [String] -> Int
calculate xs =
  case last xs of
    "+" -> sum $ map read $ init xs
    "*" -> product $ map read $ init xs

main :: IO ()
main = do
  contents <- getContents
  print . sum . map calculate . transpose . map words . lines $ contents
