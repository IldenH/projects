import Data.Array
import Data.List
import Data.Maybe
import qualified Data.Set as S

data Gift = Gift
  { name :: String,
    rund :: Bool,
    weight :: Int
  }
  deriving (Show, Eq, Ord)

type Peg = [Gift]

type State = [Peg]

parse :: String -> Gift
parse s =
  let (name, r1) = break (== ',') $ drop 5 s
      (shape, r2) = break (== ',') $ drop 2 r1
      weight = read $ drop 2 r2
      rund = shape `elem` ["rund", "sylinder"]
   in Gift name rund weight

validStack :: Peg -> Bool
validStack [] = True
validStack [_] = True
validStack (x1 : x2 : xs) =
  weight x1 <= weight x2
    && not (rund x1 && rund x2)
    && validStack (x2 : xs)

validBlock :: Peg -> Bool
validBlock x = sum (map weight x) <= 10 && validStack x

validState :: State -> Bool
validState = all validStack . drop 1

takeK :: Int -> Peg -> Maybe (Peg, Peg)
takeK k peg
  | length peg >= k = Just (take k peg, drop k peg)
  | otherwise = Nothing

type Move = (Int, Int, Int)

updateAt :: Int -> (a -> a) -> [a] -> [a]
updateAt i f =
  zipWith (\idx x -> if idx == i then f x else x) [0 ..]

move :: State -> Move -> Maybe State
move state (from, to, k)
  | from == to = Just state
  | otherwise = do
      (block, rest) <- takeK k (state !! from)
      let newState = updateAt to (\x -> block ++ x) $ updateAt from (\_ -> rest) state
      if validBlock block && validState newState
        then Just newState
        else Nothing

validMoves :: State -> [(Move, State)]
validMoves s = mapMaybe tryMove moves
  where
    pegs = [0 .. length s - 1]
    tryMove m = do
      s' <- move s m
      pure (m, s')
    moves =
      [ (f, t, k)
      | f <- pegs,
        t <- pegs,
        f /= t,
        let peg = s !! f,
        not $ null peg,
        k <- [1 .. min 3 (length peg)]
      ]

goal :: State -> Bool
goal state = all null $ take (length state - 1) state

data Queue a = Queue [a] [a]

enqueue :: a -> Queue a -> Queue a
enqueue x (Queue f b) = Queue f (x : b)

dequeue :: Queue a -> Maybe (a, Queue a)
dequeue (Queue [] []) = Nothing
dequeue (Queue [] b) = dequeue (Queue (reverse b) [])
dequeue (Queue (x : xs) b) = Just (x, Queue xs b)

bfs :: Queue (State, [Move]) -> S.Set State -> [Move]
bfs queue visited =
  case dequeue queue of
    Nothing -> error "no solution"
    Just ((state, path), queue')
      | goal state -> reverse path
      | otherwise ->
          let next =
                [ (s, m : path)
                | (m, s) <- validMoves state,
                  S.notMember s visited
                ]

              visited' =
                foldr (S.insert . fst) visited next

              queue'' =
                foldr enqueue queue' next
           in bfs queue'' visited'

solve :: State -> [Move]
solve s = bfs (Queue [(s, [])] []) S.empty

reconstruct :: State -> [Move] -> (State, [(Move, [Gift])])
reconstruct = mapAccumL step
  where
    step state m@(from, _, k) =
      let moved = take k $ state !! from
          Just state' = move state m
       in (state', (m, reverse moved))

format :: State -> [Move] -> String
format s path =
  unwords
    . map (\((f, t, _), xs) -> "[" ++ intercalate "," (map (name) xs) ++ "] " ++ show f ++ " > " ++ show t ++ ".")
    . snd
    $ reconstruct s path

main :: IO ()
main = do
  contents <- reverse . map parse . lines <$> readFile "input.txt"
  let initState = [contents, [], [], [], []]
  putStrLn . format initState $ solve initState
