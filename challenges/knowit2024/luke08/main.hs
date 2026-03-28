primes :: [Int]
primes = 2 : 3 : sieve (tail primes) [5, 7 ..]
  where
    sieve (p : ps) xs = h ++ sieve ps [x | x <- t, x `rem` p /= 0]
      where
        (h, ~(_ : t)) = span (< p * p) xs

digits :: Int -> [Int]
digits number
  | number == 0 = [0]
  | otherwise = digits' number []
  where
    digits' :: Int -> [Int] -> [Int]
    digits' 0 accumulator = accumulator
    digits' number accumulator = digits' (number `div` 10) (number `mod` 10 : accumulator)

primesDigits :: [[Int]]
primesDigits = map digits primes

primtalv :: Int -> Int
primtalv n = sum $ concatMap columnProducts primes'
  where
    columnProducts = zipWith (\index number -> number * 10 ^ index) [0 ..]
    primes' = take n primesDigits

primtalvs :: [Int]
primtalvs = map primtalv [1 ..]

isPrime :: Int -> Bool
isPrime number = number == last (takeWhile (<= number) primes)

isPrimtalv :: Int -> Bool
isPrimtalv number = number == last (takeWhile (<= number) primtalvs)

isPerfekt :: Int -> Bool
isPerfekt number = isPrimtalv number && isPrime number

perfektPrimtalvs :: [Int]
perfektPrimtalvs = filter isPrime primtalvs

main :: IO ()
main = do
  print $ (length . takeWhile (< 10_000_000)) perfektPrimtalvs
