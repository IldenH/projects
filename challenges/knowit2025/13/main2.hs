-- Attempt 2 with "Felles steg mellom kaker teller bare én gang i tidsbruk."

import Data.List
import qualified Data.Map as M
import Data.Maybe
import Data.Ord
import qualified Data.Set as S

data Food = Food
  { name :: String,
    happy :: Int,
    steps :: [String]
  }
  deriving (Show)

type TimeMap = M.Map String Int

time :: TimeMap -> [String] -> Int
time m = sum . mapMaybe (`M.lookup` m)

timeMap :: TimeMap
timeMap = M.fromList [("Start", 2), ("Mix", 3), ("AddSugar", 2), ("Bake", 5), ("Decorate", 3)]

example =
  [ "Pepperkake 10 Start Mix Bake Decorate",
    "Sjokoladekake 12 Start Mix Bake",
    "Havrekjeks 7 Start Mix Bake"
  ]

parseFood :: TimeMap -> String -> Food
parseFood m s =
  let (name : happy : steps) = words s
   in Food name (read happy) steps

parseTime :: String -> (String, Int)
parseTime s =
  let (step, _ : time) = break (== ':') s
   in (step, read time)

solve :: [Food] -> Int -> TimeMap -> S.Set String -> [(String, Int)]
solve [] _ _ _ = [("", 0)]
solve (x : xs) max m steps' =
  let skip = solve xs max m steps'
      time' = time m $ filter (`S.notMember` steps') $ steps x
      take
        | time' > max = []
        | otherwise =
            [ (n ++ "," ++ name x, h + happy x)
            | (n, h) <- solve xs (max - time') m (steps' <> S.fromList (steps x))
            ]
   in skip ++ take

main :: IO ()
main = do
  times <- readFile "timemap.txt"
  let timeMap = M.fromList . map parseTime . lines $ times
  contents <- readFile "input.txt"
  let ((_ : _ : max) : foodsRaw) = lines $ contents
  let foods = map (parseFood timeMap) foodsRaw
  let best = maximumBy (comparing snd) $ solve foods (read max) timeMap S.empty
  putStrLn $ (show $ snd best) ++ (fst best)
