double :: (Num a) => a -> a
double x = x * 2

moreThan :: Integer -> Integer -> Bool
moreThan x y
  | x > y = True
  | otherwise = False

haskif :: String
haskif = if 1 == 1 then "wow" else "not wow"

help :: IO ()
help = do
  print "I won't help you :)"

printHaskif :: IO ()
printHaskif = do
  print haskif

arguments :: [String] -> IO ()
arguments args = case args of
  ["help"] -> help
  [] -> print "No arguments provided"
  _ -> printHaskif

funFunction :: Integer -> Integer -> Integer
funFunction x y = x + y

numbersDivisibleBy :: Integer -> [Integer]
numbersDivisibleBy y = filter (\x -> x `rem` y == 0) [1 ..]

-- matrix :: [[Int]]
-- matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
matrix :: [[Int]]
matrix = [map (+ i) [1 .. 6] | i <- [0 .. 5]]

doubledMatrix :: [[Int]]
doubledMatrix = map (map (* 2)) matrix

-- dårlig convention sikkert men kult
(%) :: (Integral a) => a -> a -> a
(%) = rem

(%=) :: (Integral a) => a -> a -> Bool
(%=) x y = x `rem` y == 0

-- hmm this concatnates into one string when list
-- wowFunc :: Int -> Char
-- wowFunc x = if x % 2 == 0 then 'x' else 'o'

xo :: Integer -> String
xo x = if x % 2 == 0 then "x" else "o"

ox :: Integer -> String
ox x = xo (x + 1)

-- checkerBoard width height = replicate height (map xo [0 .. width - 1])
checkerBoard :: Integer -> Integer -> [[String]]
checkerBoard width height =
  let widthRange = [0 .. width - 1]
      heightRange = [0 .. height - 1]
   in [if index %= 2 then map xo widthRange else map ox widthRange | index <- heightRange]

main :: IO ()
main =
  do
    print "Hello, world!"
    print $ double 3
    let tall =
          [1, 2, 3, 4, 5]
    print $ map (* 2) tall
    print $ 4 `moreThan` 6
    print haskif
    arguments ["help", "me"]
    let tall2 = map (+ 1) tall
    print $ map (* 2) tall
    print $ map (* 2) tall2
    print tall2
    print $ foldl funFunction 4 [1, 2, 3]
    print $ foldl (\x y -> 1 * x + y) 4 [1, 2, 3]
    print $ foldl (+) 4 [1, 2, 3] -- hmm that also works
    -- let mangeTall = [1 ..]
    -- print $ map (* 2) mangeTall
    print $ foldl (*) 1 [1, 2, 3, 4]
    print $ sum tall
    print $ product tall
    print $ map (\x -> if x == 2 then "two" else "not two") tall
    print $ take 3 $ numbersDivisibleBy 3
    print $ take (10 - 4 + 1) $ drop 4 $ numbersDivisibleBy 3
    print $ replicate 4 [1 .. 4]
    print matrix
    mapM_ print (checkerBoard 4 3)
