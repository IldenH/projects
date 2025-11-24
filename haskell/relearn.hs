-- Relearning haskell trough https://learnyouahaskell.github.io since i haven't used haskell in about a year and learning some things about haskell i didn't know existed

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
