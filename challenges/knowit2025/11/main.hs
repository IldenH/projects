import Data.List

data Item = Item
  { name :: String,
    weight :: Int,
    happy :: Int
  }
  deriving (Show, Eq)

parse :: String -> Item
parse s =
  let [name, weight, happy] = words s
   in Item name (read weight) (read happy)

solve :: [Item] -> Int -> [(Int, Int)]
solve [] _ = [(0, 0)]
solve (x : xs) maxW =
  let skip = solve xs maxW
      take =
        [ (h + happy x, n + 1)
        | (h, n) <- solve xs (maxW - weight x),
          weight x <= maxW
        ]
   in skip ++ take

main :: IO ()
main = do
  contents <- getContents
  let max = read (head $ lines $ contents) :: Int
  let items = map parse . drop 1 . lines $ contents
  print $ maximum $ solve items max
