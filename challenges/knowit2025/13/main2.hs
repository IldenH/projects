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

parseFood :: TimeMap -> String -> Food
parseFood m s =
  let (name : happy : steps) = words s
   in Food name (read happy) steps

parseTime :: String -> (String, Int)
parseTime s =
  let (step, _ : time) = break (== ':') s
   in (step, read time)

solve :: [Food] -> Int -> TimeMap -> S.Set String -> [([String], Int)]
solve [] _ _ _ = [([], 0)]
solve (x : xs) max tm steps' =
  let skip = solve xs max tm steps'
      time' = time tm $ filter (`S.notMember` steps') $ steps x
      take
        | time' > max = []
        | otherwise =
            [ (name x : ns, h + happy x)
            | (ns, h) <- solve xs (max - time') tm (steps' <> S.fromList (steps x))
            ]
   in skip ++ take

main :: IO ()
main = do
  timeMap <- M.fromList . map parseTime . lines <$> readFile "timemap.txt"
  contents <- lines <$> readFile "input.txt"
  let ((_ : _ : max) : foodsRaw) = contents
      foods = map (parseFood timeMap) foodsRaw
      best = maximumBy (comparing snd) $ solve foods (read max) timeMap S.empty
      foods' = sort $ fst best

  putStrLn $ intercalate "," $ (show $ snd best) : foods'
