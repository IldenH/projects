import Data.Function
import Data.List
import qualified Data.Map.Strict as M
import Data.Maybe
import qualified Data.Set as S

type Node = Int

type Weight = Int

type Graph = M.Map Node [(Node, Weight)]

type Prev = M.Map Node Node

parse :: String -> (Node, Node, Weight)
parse s =
  let [a, b, w] = map read $ words s
   in (a, b, w)

buildGraph :: [(Node, Node, Weight)] -> Graph
buildGraph = M.fromListWith (++) . map (\(a, b, w) -> (a, [(b, w)]))

dijkstra :: Graph -> Node -> (M.Map Node Weight, Prev)
dijkstra graph start = go (M.singleton start 0) M.empty (S.singleton (0, start))
  where
    go dist prev pq
      | S.null pq = (dist, prev)
      | otherwise =
          let ((d, u), pq') = S.deleteFindMin pq
           in if d > fromMaybe maxBound (M.lookup u dist)
                then go dist prev pq'
                else
                  let neighbors = fromMaybe [] (M.lookup u graph)
                      (dist', prev', pq'') = relax u d neighbors dist prev pq'
                   in go dist' prev' pq''

    relax u d neighbors dist prev pq =
      foldl step (dist, prev, pq) neighbors
      where
        step (distAcc, prevAcc, pqAcc) (v, w) =
          let alt = d + w
              dv = M.lookup v distAcc
           in if maybe True (alt <) dv
                then (M.insert v alt distAcc, M.insert v u prevAcc, S.insert (alt, v) pqAcc)
                else (distAcc, prevAcc, pqAcc)

reconstructPath :: Prev -> Node -> Node -> Maybe [Node]
reconstructPath prev start goal = reverse <$> go goal
  where
    go v
      | v == start = Just [start]
      | otherwise = (v :) <$> (M.lookup v prev >>= go)

shortestCycle :: Graph -> Node -> Maybe (Weight, [Node])
shortestCycle graph v =
  let neighbors = M.findWithDefault [] v graph
      try (u, w) = do
        (dist, prev) <- Just $ dijkstra graph u
        d <- M.lookup v dist
        path <- reconstructPath prev u v
        pure (w + d, v : path)
   in listToMaybe . sortBy (compare `on` fst) $ (mapMaybe try neighbors)

format :: (Weight, [Node]) -> String
format (w, ns) = ns' ++ w'
  where
    ns' = intercalate " -> " $ map (\n -> 'R' : show n) ns
    w' = " (" ++ show w ++ ")"

main :: IO ()
main = do
  contents <- map parse . lines <$> readFile "input_simple.txt"
  let graph = buildGraph contents
      nodes = M.keys graph
  putStrLn . format . minimum . mapMaybe (shortestCycle graph) $ nodes
