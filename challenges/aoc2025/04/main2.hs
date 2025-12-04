type Pos = (Int, Int)

type Grid = [[Int]]

grid :: Grid
grid =
  [ [0, 0, 1, 1, 0, 1, 1, 1, 1, 0],
    [1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
    [1, 1, 1, 1, 1, 0, 1, 0, 1, 1],
    [1, 0, 1, 1, 1, 1, 0, 0, 1, 0],
    [1, 1, 0, 1, 1, 1, 1, 0, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 1, 0, 1],
    [0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
    [1, 0, 1, 1, 1, 0, 1, 1, 1, 1],
    [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
    [1, 0, 1, 0, 1, 1, 1, 0, 1, 0]
  ]

-- assumes equal row lengths
gridPositions :: Grid -> [Pos]
gridPositions grid = [(x, y) | x <- [0 .. length grid - 1], y <- [0 .. length (grid !! 0) - 1]]

getGrid :: Grid -> Pos -> Int
getGrid grid (row, col)
  | row >= 0 && row < length grid && col >= 0 && col < length (grid !! row) = grid !! row !! col
  | otherwise = 0

adjacent :: Grid -> Pos -> (Pos, Int)
adjacent grid (row, col) =
  let getGrid' = getGrid grid
      w = getGrid' (row, (col - 1))
      e = getGrid' (row, (col + 1))
      n = getGrid' ((row - 1), col)
      s = getGrid' ((row + 1), col)
      nw = getGrid' ((row - 1), (col - 1))
      ne = getGrid' ((row - 1), (col + 1))
      sw = getGrid' ((row + 1), (col - 1))
      se = getGrid' ((row + 1), (col + 1))
   in ((row, col), sum [w, e, n, s, nw, ne, sw, se])

removable :: Grid -> [Pos]
removable grid = map fst . filter (\(x, y) -> y < 4) . map (adjacent grid) . filter (\x -> getGrid grid x == 1) . gridPositions $ grid

replace :: Grid -> Pos -> Int -> Grid
replace grid (row, col) new =
  let (gridBefore, gridRest) = splitAt row grid
      (before, rest) = splitAt col (grid !! row)
   in gridBefore
        ++ [ case rest of
               [] -> grid !! row
               (_ : rs) -> before ++ (new : rs)
           ]
        ++ (drop 1 gridRest)

remove :: Grid -> (Int, Grid)
remove grid =
  let removed = scanl (\acc x -> replace acc x 0) grid $ removable grid
   in (length removed - 1, last removed)

toGrid :: [String] -> [[Int]]
toGrid = foldl (\acc x -> map (\y -> if y == '@' then 1 else 0) x : acc) []

main :: IO ()
main = do
  contents <- getContents
  let grid = toGrid . lines $ contents
  putStr $ show . sum . map fst . drop 1 . takeWhile (\(x, y) -> x > 0) . iterate (\(x, y) -> remove y) $ (1, grid)
