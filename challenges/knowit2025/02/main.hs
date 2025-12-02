import Data.Char
import Data.List

alphabet = ['a' .. 'z'] ++ ['æ', 'ø', 'å']

getIndex :: Char -> Int
getIndex c
  | c `elem` alphabet = x
  | otherwise = error "No such letter"
  where
    (Just x) = elemIndex c alphabet

caesar :: (Int -> Int) -> String -> String
caesar shift = map caesar'
  where
    handleNegative :: Int -> Int
    handleNegative x
      | x < 0 = x + length alphabet
      | otherwise = x
    caesar' :: Char -> Char
    caesar' x
      | isUpper x = toUpper . shift' . toLower $ x
      | otherwise = shift' x
      where
        shift' = (!!) alphabet . handleNegative . shift . getIndex

main :: IO ()
main = do
  contents <- getContents
  putStr $ concat . map (\(i, x) -> caesar (subtract i) x) . zip [1 ..] . lines $ contents
