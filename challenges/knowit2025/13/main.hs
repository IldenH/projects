import Data.List
import qualified Data.Map as M
import Data.Maybe
import Data.Ord

data Food = Food
  { name :: String,
    happy :: Int,
    time :: Int
  }
  deriving (Show)

timeMap :: M.Map String Int
timeMap = M.fromList [("Start", 2), ("Mix", 3), ("AddSugar", 2), ("Bake", 5), ("Decorate", 3)]

example =
  [ "Pepperkake 10 Start Mix Bake Decorate",
    "Sjokoladekake 12 Start Mix Bake",
    "Havrekjeks 7 Start Mix Bake"
  ]

parseFood :: M.Map String Int -> String -> Food
parseFood m s =
  let (name : happy : rest) = words s
      time = sum $ mapMaybe (`M.lookup` m) rest
   in Food name (read happy) time

parseTime :: String -> (String, Int)
parseTime s =
  let (step, _ : time) = break (== ':') s
   in (step, read time)

solve :: [Food] -> Int -> [(String, Int)]
solve [] _ = [("", 0)]
solve (x : xs) max =
  let skip = solve xs max
      take =
        [ (n ++ "," ++ name x, h + happy x)
        | (n, h) <- solve xs (max - time x),
          time x <= max
        ]
   in skip ++ take

main :: IO ()
main = do
  times <- readFile "timemap.txt"
  let timeMap = M.fromList . map parseTime . lines $ times
  contents <- readFile "input.txt"
  let ((_ : _ : max) : foodsRaw) = lines $ contents
  let foods = map (parseFood timeMap) foodsRaw
  print $ maximumBy (comparing snd) $ solve foods (read max)
