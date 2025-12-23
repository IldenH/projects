import qualified Data.Map as M

data Tile = Open | Block | Start | End deriving (Show, Eq)

type Grid = [[Tile]]

type Pos = (Int, Int)

parse :: String -> [Tile]
parse = map go
  where
    go 'A' = Start
    go 'B' = End
    go 'x' = Block
    go _ = Open

moves :: Pos -> [Pos]
moves (x, y) = [(x + 1, y), (x, y + 1), (x + 1, y + 1)]

getTile :: Grid -> Pos -> Maybe Tile
getTile grid@(row : _) (x, y)
  | x >= length grid = Nothing
  | y >= length row = Nothing
  | otherwise = Just (grid !! x !! y)

validMoves :: Grid -> Pos -> [Pos]
validMoves grid pos =
  [ p
  | p <- moves pos,
    Just t <- [getTile grid p],
    t /= Block
  ]

type Memo = M.Map Pos Int

solve :: Grid -> Pos -> Integer
solve grid@(row : _) start = memo M.! start
  where
    memo =
      M.fromList
        [(p, value p) | p <- allPositions]

    value p
      | Just End <- getTile grid p = 1
      | otherwise = sum [memo M.! q | q <- validMoves grid p]

    allPositions =
      [ (x, y)
      | x <- [0 .. length grid - 1],
        y <- [0 .. length row - 1]
      ]

main :: IO ()
main = do
  contents <- map parse . lines <$> readFile "input.txt"
  print $ solve contents (0, 0)
