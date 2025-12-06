import qualified Data.Map as M
import Data.Maybe
import qualified Data.Sequence as Q
import qualified Data.Set as S

type Coord = (Int, Int)

type CoordGraph = M.Map Coord [Coord]

neighbors :: Coord -> [Coord]
neighbors (x, y) = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

startEnd :: [String] -> [Coord]
startEnd grid = [(x, y) | (x, row) <- zip [0 ..] grid, (y, ch) <- zip [0 ..] row, ch `elem` ['S', '*']]

coords :: [String] -> [Coord]
coords grid = [(x, y) | (x, row) <- zip [0 ..] grid, (y, ch) <- zip [0 ..] row, ch `elem` ['.', 'S', '*']]

buildGraph g =
  let coords' = coords g
      adj c = filter (`elem` coords') $ neighbors c
   in M.fromList [(c, adj c) | c <- coords']

-- i don't really understand this but maybe sometime in the future
bfsGraph :: CoordGraph -> Coord -> [Coord]
bfsGraph g start = go (Q.singleton start) (S.singleton start)
  where
    go queue visited =
      case Q.viewl queue of
        Q.EmptyL -> []
        v Q.:< qs ->
          let ns = filter (`S.notMember` visited) (M.findWithDefault [] v g)
              visited' = visited <> S.fromList ns
              queue' = qs <> Q.fromList ns
           in v : go queue' visited'

-- i don't really understand this but maybe sometime in the future
bfsDistances :: CoordGraph -> Coord -> [(Coord, Int)]
bfsDistances g start = go (Q.singleton (start, 0)) (S.singleton start) []
  where
    go :: Q.Seq (Coord, Int) -> S.Set Coord -> [(Coord, Int)] -> [(Coord, Int)]
    go Q.Empty _ acc = reverse acc
    go ((v, d) Q.:<| qs) visited acc =
      let ns = [n | n <- M.findWithDefault [] v g, n `S.notMember` visited]
          visited' = S.union visited (S.fromList ns)
          qs' = qs <> Q.fromList (zip ns $ repeat $ d + 1)
       in go qs' visited' ((v, d) : acc)

distance :: CoordGraph -> Coord -> Coord -> Maybe Int
distance g start target =
  lookup target (bfsDistances g start)

distance' :: [String] -> Maybe Int
distance' grid = case startEnd grid of
  [start, end] -> distance (buildGraph grid) start end
  _ -> Nothing

stringGrids :: String -> [String]
stringGrids [] = []
stringGrids s =
  let (x, xs) = break (== ';') s
   in x : stringGrids (drop 1 xs)

main :: IO ()
main = do
  contents <- getContents
  let grids = map lines . stringGrids $ contents
  print $ sum $ mapMaybe distance' $ grids
