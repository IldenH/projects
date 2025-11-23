-- Relearning haskell trough https://learnyouahaskell.github.io since i haven't used haskell in about a year and learning some things about haskell i didn't know existed

doubleMe x = x + x

doubleUs x y = doubleMe x + doubleMe y

doubleSmallNumber x = if x > 100 then x else x * 2

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
