-- part 2 attempt 1, gradually became very overcomplicated

type Range = (Int, Int)

parseRange :: String -> Range
parseRange s =
  let (min, _ : max) = break (== '-') s
   in (read min, read max)

amountFresh :: Range -> Int
amountFresh (min, max) = (max + 1) - min

isOverlap :: Range -> Range -> Bool
isOverlap (min1, max1) (min2, max2)
  | min1 <= max2 && max2 <= max1 = True
  | min1 <= min2 && min2 <= max1 = True
  | min2 <= min1 && max1 <= max2 = True
  | otherwise = False

fixOverlap :: Range -> Range -> Range
fixOverlap a@(min1, max1) b@(min2, max2)
  | not $ isOverlap a b = b
  | min2 <= min1 && max1 <= max2 = b
  | min1 <= min2 && max2 <= max1 = a
  | max2 == min1 = (min2, max2 - 1)
  | max2 == max1 = (min2, max2 - min1)
  | min2 == min1 = (min2 + (max1 - min1 + 1), max2)
  | min2 == max1 = (min2 + 1, max2)
  | max2 < max1 = (min2, max2 + (min1 - max2 - 1))
  | min2 < min1 = (min2 + (min2 + min1 - 1), max2)
  | min2 < max1 = (min2 - (min2 - max1 - 1), max2)
  | otherwise = error (show a ++ " " ++ show b)

handleOverlap :: Range -> [Range] -> Range
handleOverlap x prev =
  let xs = handleOverlap' x prev
      mins = map fst xs
      maxs = map snd xs
   in (maximum mins, minimum maxs)

handleOverlap' :: Range -> [Range] -> [Range]
handleOverlap' x prev = foldl (\acc y -> if isOverlap y x then fixOverlap y x : acc else acc) [] prev

solve :: [Range] -> [Range] -> [Int] -> (Int, [Range], [Int])
solve [] prev debug = (sum debug, prev, debug)
solve (x@(min, max) : xs) prev debug =
  let (fresh, debugNew) = case any (`isOverlap` x) prev of
        False -> (amountFresh x, debug)
        True ->
          ( let ys@(y : _) = handleOverlap' x prev
             in ( if length ys == 1
                    then (amountFresh $ handleOverlap x prev, debug)
                    else case (all (== y) ys) of
                      False -> (amountFresh $ handleOverlap x prev, debug)
                      True -> (amountFresh $ handleOverlap x prev, drop (length ys) debug)
                )
          )
   in solve xs (x : prev) (fresh : debugNew)

main :: IO ()
main = do
  rangesContents <- readFile "ranges2.txt"
  let ranges = map parseRange . lines $ rangesContents
  putStr $ show $ solve ranges [] []
