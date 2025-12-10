import Data.Char
import Data.List
import qualified Data.Map as M
import Data.Maybe
import Text.ParserCombinators.ReadP

data Machine = Machine
  { name :: String,
    temp :: Int,
    vann :: Int,
    kull :: Int
  }
  deriving (Show)

parser :: ReadP Machine
parser = do
  _ <- string "Maskin "
  name <- munch1 (/= ',')
  _ <- string ", temperatur "
  t <- read <$> munch1 isDigit
  _ <- string "C, vann "
  v <- read <$> munch1 isDigit
  _ <- string "L, kullsyre "
  k <- read <$> munch1 isDigit
  _ <- string "L"
  eof
  return (Machine name t v k)

parse :: String -> Maybe Machine
parse s =
  case readP_to_S parser s of
    [(result, _)] -> Just result
    _ -> Nothing

calculate :: Machine -> Int
calculate m
  | temp m < 95 || temp m > 105 = 0
  | vann m < 400 || vann m > 1500 = 0
  | kull m < 300 || kull m > 500 = 0
  | temp m >= 100 = result - result `div` 40
  | otherwise = result
  where
    result = vann m - 100 + kull m `div` 10

main :: IO ()
main = do
  contents <- getContents
  let mMap = M.fromListWith (+) . map (\m -> (name m, calculate m)) . map fromJust . map parse . lines $ contents
  print . sortOn (negate . snd) . M.toList $ mMap
  print . sum . map snd . M.toList $ mMap
