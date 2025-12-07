-- part 1 attempt 2, here i am instead modifing the grid to be # for "hit" and ^ for "not hit (yet)"

import qualified Data.Map as M
import qualified Data.Set as S

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

type GridMap = M.Map Coord Char

coords :: [String] -> GridMap
coords grid = M.fromList [((x, y), ch) | (x, row) <- zip [0 ..] grid, (y, ch) <- zip [0 ..] row]

bottom :: M.Map (a, b) c -> a
bottom = fst . fst . M.findMax

under :: Coord -> Coord
under (x, y) = (x + 1, y)

split :: Coord -> S.Set Coord
split (x, y) = S.fromList [(x + 1, y - 1), (x + 1, y + 1)]

toSplit :: GridMap -> Coord -> (GridMap, S.Set Coord)
toSplit grid xy@(x, y)
  | u == Just '^' = (M.insert (under xy) '#' grid, split xy)
  | u == Just '.' = toSplit grid (under xy)
  | u == Just '#' = (grid, S.empty)
  | otherwise = (grid, S.singleton (x, bottom grid))
  where
    u = M.lookup (under xy) grid

solve :: GridMap -> S.Set Coord -> GridMap
solve grid coords
  | all (\(x, y) -> y == bottom grid) coords' = grid
  | otherwise = solve grid' coords'
  where
    (grid', split) = foldl step (grid, []) (S.toList coords)
      where
        step (g, acc) coord =
          let (g', s) = toSplit g coord
           in (g', s : acc)
    coords' = S.unions split

main :: IO ()
main = do
  contents <- getContents
  let grid = coords . lines $ contents
  let ((start, _) : _) = M.toList . M.filter (== 'S') $ grid
  print $ length $ M.filter (== '#') $ solve grid (S.singleton start)
