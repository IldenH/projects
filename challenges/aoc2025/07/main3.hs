-- part 2 using a branching tree

import qualified Data.Map as M

type Pos = (Int, Int)

type Memo = M.Map Pos Int

findStart :: [String] -> Pos
findStart grid =
  case [(x, y) | (x, row) <- zip [0 ..] grid, (y, c) <- zip [0 ..] row, c == 'S'] of
    [x] -> x
    _ -> error "Missing 'S'"

countPaths :: [String] -> Pos -> Memo -> (Int, Memo)
countPaths grid pos@(x, y) memo
  | x >= length grid = (1, memo)
  | Just v <- M.lookup pos memo = (v, memo)
  | otherwise = case grid !! x !! y of
      'S' -> continue
      '.' -> continue
      '^' -> traverse
  where
    go = countPaths grid
    continue = go (x + 1, y) memo
    traverse =
      let (l, lMemo) = go (x + 1, y - 1) memo
          (r, rMemo) = go (x + 1, y + 1) lMemo
          total = l + r
       in (total, M.insert pos total rMemo)

countPaths' :: [String] -> Int
countPaths' grid = fst $ countPaths grid (findStart grid) M.empty

main :: IO ()
main = do
  contents <- getContents
  print $ countPaths' $ lines $ contents
