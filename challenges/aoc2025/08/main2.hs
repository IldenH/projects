-- part 1 attempt 2

import qualified Data.Array as A
import qualified Data.Graph as G
import Data.List
import qualified Data.Map as M
import Data.Maybe
import qualified Data.Set as S
import qualified Data.Tree as T

example =
  [ "162,817,812",
    "57,618,57",
    "906,360,560",
    "592,479,940",
    "352,342,300",
    "466,668,158",
    "542,29,236",
    "431,825,988",
    "739,650,466",
    "52,470,668",
    "216,146,977",
    "819,987,18",
    "117,168,530",
    "805,96,715",
    "346,949,466",
    "970,615,88",
    "941,993,340",
    "862,61,35",
    "984,92,344",
    "425,690,689"
  ]

type Pos = (Int, Int, Int)

distance :: Pos -> Pos -> Int
distance (x1, y1, z1) (x2, y2, z2) =
  let dx = x2 - x1
      dy = y2 - y1
      dz = z2 - z1
   in dx ^ 2 + dy ^ 2 + dz ^ 2

parsePos :: String -> Pos
parsePos s = read $ "(" ++ s ++ ")"

pairs :: (Eq a) => [a] -> [(a, a)]
pairs xs = [(x, y) | x <- xs, y <- xs, x /= y]

pairs' = sortOn (\(a, b) -> distance a b) . pairs

solve :: [(Pos, Pos)] -> [[Pos]]
solve inputPairs =
  let allTriples = S.toList $ S.fromList $ concatMap (\(a, b) -> [a, b]) inputPairs

      nodeToIdMap :: M.Map Pos Int
      nodeToIdMap = M.fromList $ zip allTriples [0 ..]

      getId :: Pos -> Int
      getId t = fromJust (M.lookup t nodeToIdMap)

      idToNodeArray = A.array (0, length allTriples - 1) (zip [0 ..] allTriples)

      edges :: [(Int, Int)]
      edges = map (\(t1, t2) -> (getId t1, getId t2)) $ inputPairs

      graph :: G.Graph
      graph = G.buildG (0, length allTriples - 1) (edges ++ map swap edges)
        where
          swap (x, y) = (y, x)

      componentIds :: [[Int]]
      componentIds = map T.flatten (G.components graph)
   in map (map (idToNodeArray A.!)) componentIds

main :: IO ()
main = do
  contents <- getContents
  let ps = map parsePos $ lines $ contents
  let joined = solve . take 2000 . pairs' $ ps
  print . product . take 3 . sortOn negate . map length $ joined
