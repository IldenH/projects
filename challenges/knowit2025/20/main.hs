import Data.List
import qualified Data.Map as M
import Data.Ord
import qualified Data.Text as T

data Candy = Element
  { name :: String,
    price :: Int,
    sugar :: Int,
    minQ :: Int,
    maxQ :: Int,
    toTest :: Int
  }
  deriving (Show)

parse :: String -> Candy
parse s =
  let [n, p, wPer, sugar, maxW, min] = map T.unpack $ T.splitOn (T.pack ",") (T.pack s)
      max = read maxW * 100 `div` (floor $ (read wPer :: Float) * 100)
   in Element n (read p) (read sugar) (read min) max (max - read min)

decompose :: Int -> [Int]
decompose x = go x 1 []
  where
    go :: Int -> Int -> [Int] -> [Int]
    go x pow acc
      | pow > x = x : acc
      | otherwise = go (x - pow) (pow * 2) (pow : acc)

flatCandy :: [Candy] -> [(Int, Int, Int, Int)]
flatCandy cs = concatMap (\(i, c) -> map (\cs' -> (i, cs', cs' * price c, cs' * sugar c)) (decompose $ toTest c)) $ zip [0 ..] cs

knapsack :: Int -> [(Int, Int)] -> [Int]
knapsack capacity items = reverse $ go n capacity
  where
    n = length items

    dp = [[best i w | w <- [0 .. capacity]] | i <- [0 .. n]]
    best 0 _ = 0
    best _ 0 = 0
    best i w
      | wt > w = dp !! (i - 1) !! w
      | otherwise =
          max
            (dp !! (i - 1) !! w)
            (val + dp !! (i - 1) !! (w - wt))
      where
        (wt, val) = items !! (i - 1)

    go 0 _ = []
    go _ 0 = []
    go i w
      | dp !! i !! w == dp !! (i - 1) !! w = go (i - 1) w
      | otherwise =
          let (wt, _) = items !! (i - 1)
           in (i - 1) : go (i - 1) (w - wt)

main :: IO ()
main = do
  contents <- map parse . lines <$> readFile "input.txt"
  let minPrice = sum $ map (\x -> price x * minQ x) $ contents
      capacity = 50000 - minPrice
      flatCandy' = flatCandy contents
      dpItems = map (\(_, _, wt, val) -> (wt, val)) flatCandy'
      chosen = knapsack capacity dpItems
      countsMap =
        foldl
          ( \m idx ->
              let (ci, cs, _, _) = flatCandy' !! idx
               in M.insertWith (+) ci cs m
          )
          M.empty
          chosen
      fullCounts =
        [(i, minQ (contents !! i) + M.findWithDefault 0 i countsMap) | i <- [0 .. length contents - 1]]
      chosenList = [(name $ contents !! i, c) | (i, c) <- fullCounts]
      totalPrice = sum [price (contents !! i) * c | (i, c) <- fullCounts]

  putStrLn $ intercalate "," (show totalPrice : map (\(n, c) -> n ++ ":" ++ show c) chosenList)
