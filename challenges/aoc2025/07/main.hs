-- part 1 attempt 1

import qualified Data.Map as M
import qualified Data.Set as S
import Debug.Trace

example =
  [ ".......S.......",
    "...............",
    ".......^.......",
    "...............",
    "......^.^......",
    "...............",
    ".....^.^.^.....",
    "...............",
    "....^.^...^....",
    "...............",
    "...^.^...^.^...",
    "...............",
    "..^...^.....^..",
    "...............",
    ".^.^.^.^.^...^.",
    "..............."
  ]

type Coord = (Int, Int)

coords :: [String] -> M.Map Coord Char
coords grid = M.fromList [((y, x), ch) | (x, row) <- zip [0 ..] grid, (y, ch) <- zip [0 ..] row]

bottomY :: M.Map (a, b) c -> b
bottomY = snd . fst . M.findMax

under :: Coord -> Coord
under (x, y) = (x, y + 1)

split :: Coord -> S.Set Coord
split (x, y) = S.fromList [(x - 1, y + 1), (x + 1, y + 1)]

toSplit :: M.Map Coord Char -> Coord -> S.Set Coord
toSplit grid xy@(x, y)
  | u == Just '^' = split xy
  | u == Just '.' = toSplit grid (under xy)
  | otherwise = S.singleton (x, bottomY grid)
  where
    u = M.lookup (under xy) grid

solve :: M.Map Coord Char -> S.Set Coord -> Int -> Int
solve grid coords n
  | all (\(x, y) -> y == bottomY grid) coords' = n
  | otherwise = trace (show coords ++ show coords' ++ " n: " ++ show n' ++ " y: " ++ show ylevel) $ solve grid coords' n'
  where
    split = map (toSplit grid) . S.toList $ coords
    coords' = S.unions $ split
    ((_, ylevel) : _) = S.toList coords
    n' = n + length (S.filter (\(x, y) -> y == ylevel && let ((_, nextY) : _) = S.toList (toSplit grid (x, y)) in nextY == ylevel + 2) coords)

main :: IO ()
main = do
  contents <- getContents
  let grid = coords . lines $ contents
  let ((start, _) : _) = M.toList . M.filter (== 'S') $ grid
  print $ solve grid (S.singleton start) 0
