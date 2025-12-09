import Data.List

example :: [String]
example =
  [ "7,1",
    "11,1",
    "11,7",
    "9,7",
    "9,5",
    "2,5",
    "2,3",
    "7,3"
  ]

type Pos = (Int, Int)

parsePos :: String -> Pos
parsePos s = read $ "(" ++ s ++ ")"

area :: Pos -> Pos -> Int
area (ax, ay) (bx, by) =
  let dx = (+) 1 $ abs $ bx - ax
      dy = (+) 1 $ abs $ by - ay
   in dx * dy

pairs :: [Pos] -> [(Pos, Pos)]
pairs xs = [(x, y) | x <- xs, y <- xs, x /= y]

ps = map parsePos example

main :: IO ()
main = do
  contents <- getContents
  let ps = map parsePos . lines $ contents
  print . head . sortOn negate . map (\(x, y) -> area x y) $ pairs ps
