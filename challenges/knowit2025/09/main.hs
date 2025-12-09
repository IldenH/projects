import Data.Char

isConsonant :: Char -> Bool
isConsonant x = x `elem` "bcdfghjklmnpqrstvwxz"

isLinse :: String -> String -> Int -> [Bool]
isLinse [] _ _ = []
isLinse (x : xs) xs' i
  | isDigit x = True : next
  | isConsonant x && not digitsAround = True : next
  | otherwise = False : next
  where
    digitsAround :: Bool
    digitsAround = length xs >= 2 && isDigit (xs !! 1) && isDigit (xs' !! (i - 2))

    next = isLinse xs xs' (i + 1)

isLinse' xs = isLinse xs xs 0

main :: IO ()
main = do
  contents <- getContents
  print $ map (\(x, y) -> x) $ filter (\(x, y) -> not y) $ zip contents (isLinse' contents)
