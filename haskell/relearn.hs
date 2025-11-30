-- Relearning haskell trough https://learnyouahaskell.github.io since i haven't used haskell in about a year and learning some things about haskell i didn't know existed

import Data.Char
import Data.List
import qualified Data.Map as Map
import Data.Maybe
import qualified Data.Set as Set

doubleMe :: (Num a) => a -> a
doubleMe x = x + x

doubleUs :: (Num a) => a -> a -> a
doubleUs x y = doubleMe x + doubleMe y

doubleSmallNumber :: (Integral a) => a -> a
doubleSmallNumber x = if x > 100 then x else x * 2

boomBangs :: (Integral a) => [a] -> [String]
boomBangs xs = [if x < 10 then "BOOM!" else "BANG!" | x <- xs, odd x]

length' xs = sum [1 | _ <- xs]

-- fib :: Int -> Int
-- fib 0 = 0
-- fib 1 = 1
-- fib n = fib (n - 1) + fib (n - 2)

fibs :: [Int]
fibs = 1 : 1 : zipWith (+) fibs (drop 1 fibs)

fib :: Int -> Int
fib n = fibs !! n

alphabet = zip ['z', 'y' .. 'a'] ['a' .. 'z']

factorial :: (Num a, Enum a) => a -> a
factorial n = product [1 .. n]

factorial' :: (Num a, Eq a) => a -> a
factorial' 0 = 1
factorial' n = n * factorial' (n - 1)

addVectors :: (Num a) => (a, a) -> (a, a) -> (a, a)
addVectors a b = (fst a + fst b, snd a + snd b)

addVectors' :: (Num a) => (a, a) -> (a, a) -> (a, a)
addVectors' (x1, y1) (x2, y2) = (x1 + x2, y1 + y2)

head' [] = error "empty list"
head' (x : _) = x

numbers = [1, 4, 5, 1, 99, 52, 42, 5, 21, 32, 67, 44, 36, 12, 6, 8, 51]

sum' [] = 0
sum' (x : xs) = x + sum' xs

max' :: (Ord a) => a -> a -> a
max' a b
  | a > b = a
  | otherwise = b

densityTell :: (RealFloat a) => a -> a -> String
densityTell mass volume
  | density < air = "Float"
  | density <= water = "Swim"
  | otherwise = "Sink"
  where
    density = mass / volume
    (air, water) = (1.2, 1000.0)

cylinder :: (RealFloat a) => a -> a -> a
cylinder r h =
  let sideArea = 2 * pi * r * h
      topArea = pi * r ^ 2
   in sideArea + 2 * topArea

swapPair :: (a, b) -> (b, a)
swapPair (a, b) = (b, a)

listDescriptor :: [a] -> String
listDescriptor [] = "Empty"
listDescriptor [x] = "Singleton"
listDescriptor xs = "Long"

listDescriptor' xs = "The list is " ++ what xs
  where
    what [] = "empty"
    what [x] = "singleton"
    what xs = "long"

safeHead :: [a] -> Maybe a
safeHead [] = Nothing
safeHead (x : _) = Just x

product' :: (Num a) => [a] -> a
product' [] = 1
product' (x : xs) = x * product' xs

replicate' :: (Integral n) => n -> a -> [a]
replicate' 0 _ = []
replicate' n x = x : replicate' (n - 1) x

take' :: (Integral n) => n -> [a] -> [a]
take' 0 _ = []
take' _ [] = []
take' n (x : xs)
  | n <= 0 = []
  | otherwise = x : take' (n - 1) xs

getGrade :: (Integral a) => a -> String
getGrade x
  | x < 60 = "F"
  | x < 70 = "D"
  | x < 80 = "C"
  | x < 90 = "B"
  | x < 100 = "A"
  | otherwise = error "score is more than 100"

bmi :: (RealFloat a) => a -> a -> String
bmi mass height
  | bmi < 18.5 = "Underweight"
  | bmi < 25.0 = "Normal"
  | bmi < 30.0 = "Overweight"
  | otherwise = "Obese"
  where
    bmi = mass / height ^ 2

roots :: (Floating a) => a -> a -> a -> (a, a)
roots a b c = (root1, root2)
  where
    root1 = (-b + sqrt (b ^ 2 - 4 * a * c)) / (2 * a)
    root2 = (-b - sqrt (b ^ 2 - 4 * a * c)) / (2 * a)

radii = [1.0, 2.5, 3.0, 0.5]

radiusArea rs = [(r, a) | r <- rs, let a = pi * r ^ 2]

describeList :: [a] -> String
describeList xs =
  "The list is " ++ case xs of
    [] -> "empty"
    [x] -> "singleton"
    xs -> "long"

capital :: String -> String
capital [] = "'' starts with ''"
capital all@(x : _) = "'" ++ all ++ "' starts with " ++ show x

primes = 2 : [x | x <- [3, 5 ..], all (\p -> x `rem` p /= 0) (takeWhile (\p -> p * p <= x) primes)]

tverrsum :: (Integral a) => a -> a
tverrsum x = tverrsum' x 0
  where
    tverrsum' :: (Integral a) => a -> a -> a
    tverrsum' 0 acc = acc
    tverrsum' x acc = tverrsum' (x `div` 10) (acc + x `rem` 10)

maximum' :: (Ord a) => [a] -> a
maximum' [] = error "empty list"
maximum' [x] = x
maximum' (x : xs) = max x maxTail
  where
    maxTail = maximum' xs

reverse' :: [a] -> [a]
reverse' [] = []
reverse' (x : xs) = reverse' xs ++ [x]

repeat' :: a -> [a]
repeat' x = x : repeat' x

zip' :: [a] -> [b] -> [(a, b)]
zip' [] _ = []
zip' _ [] = []
zip' (x : xs) (y : ys) = (x, y) : zip' xs ys

elem' :: (Eq a) => a -> [a] -> Bool
elem' _ [] = False
elem' e (x : xs)
  | e == x = True
  | otherwise = elem' e xs

quicksort :: (Ord a) => [a] -> [a]
quicksort [] = []
quicksort (x : xs) =
  let smallerSorted = quicksort [a | a <- xs, a <= x]
      biggerSorted = quicksort [a | a <- xs, a > x]
   in smallerSorted ++ [x] ++ biggerSorted

drop' :: (Integral n) => n -> [a] -> [a]
drop' 0 xs = xs
drop' _ [] = []
drop' n (x : xs) = drop' (n - 1) xs

filter' :: (a -> Bool) -> [a] -> [a]
filter' _ [] = []
filter' f (x : xs)
  | f x = x : filter' f xs
  | otherwise = filter' f xs

zipWith' :: (a -> b -> c) -> [a] -> [b] -> [c]
zipWith' _ [] _ = []
zipWith' _ _ [] = []
zipWith' f (x : xs) (y : ys) = f x y : zipWith' f xs ys

concat' :: [[a]] -> [a]
concat' [] = []
concat' (xs : xxs) = xs ++ concat' xxs

intersperse' :: a -> [a] -> [a]
intersperse' _ [] = []
intersperse' _ [x] = [x]
intersperse' a (x : xs) = x : a : intersperse' a xs

gcd' :: (Integral a) => a -> a -> a
gcd' a 0 = a
gcd' a b = gcd' b (a `mod` b)

flip' :: (a -> b -> c) -> b -> a -> c
flip' f x y = f y x

-- find the largest number under 100,000 that's divisible by 3829.
largestDivisibleNumberUnder x num = maximum $ filter isDivisible [1 .. x]
  where
    isDivisible = (== 0) . (`rem` num)

collatz :: (Integral a) => a -> [a]
collatz 1 = [1]
collatz n
  | even n = n : collatz (n `div` 2)
  | odd n = n : collatz (n * 3 + 1)

sum'' :: (Num a) => [a] -> a
sum'' xs = foldl (\acc x -> acc + x) 0 xs

sum''' :: (Num a) => [a] -> a
sum''' = foldl (+) 0

elem'' :: (Eq a) => a -> [a] -> Bool
elem'' y = foldl (\acc x -> x == y || acc) False

map' :: (a -> b) -> [a] -> [b]
map' f = foldr (\x acc -> f x : acc) []

maximum'' :: (Ord a) => [a] -> a
maximum'' = foldr1 (\x acc -> if x > acc then x else acc)

reverse'' :: [a] -> [a]
reverse'' = foldl (\acc x -> x : acc) []

product'' :: (Num a) => [a] -> a
product'' = foldr1 (*)

filter'' :: (a -> Bool) -> [a] -> [a]
filter'' f = foldr (\x acc -> if f x then x : acc else acc) []

head'' :: [a] -> a
head'' = foldr1 (\x _ -> x)

last'' :: [a] -> a
last'' = foldl1 (\_ x -> x)

applyIf :: (a -> Bool) -> (a -> a) -> a -> a
applyIf p f x
  | p x = f x
  | otherwise = x

findLongs :: [[a]] -> [[a]]
findLongs = filter $ \x -> length x > 7

squareAndFilterEvens :: (Integral a) => [a] -> [a]
squareAndFilterEvens = filter even . map (^ 2)

countOccurences :: (Eq a, Integral i) => a -> [a] -> i
countOccurences a = foldl (\acc x -> if x == a then acc + 1 else acc) 0

checkerBoard w h = concat . replicate h . unlines $ [rep "ox", rep "xo"]
  where
    rep = concat . replicate w

frequencies :: (Ord a) => [a] -> [(a, Int)]
frequencies = sortBy (\(_, x) (_, y) -> y `compare` x) . occurrences
  where
    occurrences = map (\all@(x : _) -> (x, length all)) . group . sort

frequencies' :: (Ord a, Num b, Ord b) => [a] -> [(a, b)]
frequencies' = reverse . sortOn snd . occurrences
  where
    occurrences = map (\all@(x : _) -> (x, genericLength all)) . group . sort

search :: (Eq a) => [a] -> [a] -> Bool
search needle haystack =
  let nlen = length needle
   in foldl (\acc x -> if take nlen x == needle then True else acc) False (tails haystack)

words' :: String -> [String]
words' s =
  case dropWhile isSpace s of
    "" -> []
    s' -> w : words' s''
      where
        (w, s'') = break isSpace s'

caesar :: (Int -> Int) -> String -> String
caesar shift = map chr . map shift . map ord

sanitize :: String -> String
sanitize = concat . map removeDoubleSpace . group . alphaSpace
  where
    alphaSpace = filter (`elem` ' ' : ['a' .. 'z']) . map toLower
    removeDoubleSpace x = if length x /= 1 && all isSpace x then " " else x

parseInt :: String -> Int
parseInt = foldr (\(x, y) acc -> acc + x * y) 0 . zip (iterate (* 10) 1) . reverse . map digitToInt

parseInt' :: String -> Int
parseInt' = foldl (\acc d -> acc * 10 + d) 0 . map digitToInt

mostFrequent :: (Ord a) => [a] -> Maybe [a]
mostFrequent [] = Nothing
mostFrequent xs = Just . map (\(x : _) -> x) . takeWhile (\x -> length x == length longest) . sorted $ xs
  where
    sorted = sortOn (negate . length) . group . sort
    (longest : _) = sorted $ xs

findLongestRun :: (Eq a) => [a] -> [(a, Int)]
findLongestRun xs = map (\xs@(x : _) -> (x, length xs)) . takeWhile (\x -> length x == length longest) . grouped $ xs
  where
    grouped = sortOn (negate . length) . group
    (longest : _) = grouped $ xs

findLongestRun' :: (Eq a) => [a] -> [(a, Int)]
findLongestRun' xs =
  let groups = group xs
      maxLen = maximum $ map length groups
   in [(x, length g) | g@(x : _) <- groups, length g == maxLen]

jaccardIndex :: (Ord a) => Set.Set a -> Set.Set a -> Double
jaccardIndex x y
  | Set.null x && Set.null y = 0.0
  | otherwise =
      let interSize = fromIntegral $ Set.size $ Set.intersection x y
          unionSize = fromIntegral $ Set.size $ Set.union x y
       in interSize / unionSize

symmetricDiff :: (Ord a) => Set.Set a -> Set.Set a -> Set.Set a
symmetricDiff x y = Set.union x y Set.\\ Set.intersection x y

invertMap :: (Ord k, Ord v) => Map.Map k v -> Map.Map v [k]
invertMap = Map.fromListWith (++) . map (\(k, v) -> (v, [k])) . Map.toList

letterFrequencies :: String -> Map.Map Char Int
letterFrequencies =
  let toMap = foldl (\acc x -> Map.insertWith (+) x 1 acc) Map.empty
      letters = filter (`elem` ['a' .. 'z']) . map toLower
   in toMap . letters
