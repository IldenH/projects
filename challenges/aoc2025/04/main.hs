toGrid :: [String] -> [[Int]]
toGrid = foldl (\acc x -> map (\y -> if y == '@' then 1 else 0) x : acc) []

main :: IO ()
main = do
  contents <- getContents
  let grid = toGrid $ lines contents

      -- assumes equal row lengths
      gridPositions :: [(Int, Int)]
      gridPositions = [(x, y) | x <- [0 .. length grid - 1], y <- [0 .. length (grid !! 0) - 1]]

      getGrid :: Int -> Int -> Int
      getGrid row col
        | row >= 0 && row < length grid && col >= 0 && col < length (grid !! row) = grid !! row !! col
        | otherwise = 0

      adjacent :: (Int, Int) -> Int
      adjacent (row, col) =
        let w = getGrid row (col - 1)
            e = getGrid row (col + 1)
            n = getGrid (row - 1) col
            s = getGrid (row + 1) col

            nw = getGrid (row - 1) (col - 1)
            ne = getGrid (row - 1) (col + 1)
            sw = getGrid (row + 1) (col - 1)
            se = getGrid (row + 1) (col + 1)
         in sum [w, e, n, s, nw, ne, sw, se]

  putStr $ show $ length $ filter (< 4) $ map adjacent $ filter (\(x, y) -> getGrid x y == 1) gridPositions
