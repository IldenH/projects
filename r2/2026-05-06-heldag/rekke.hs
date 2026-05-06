a 1 = 4
a 2 = 8
a n
  | n >= 2 = 3 * a (n - 1) - 2 * a (n - 2) - 3
  | otherwise = 0

s n = sum $ map a [1 .. n]
