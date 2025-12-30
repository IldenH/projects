-- written before reading the solution the book gives

group :: [a] -> [(a, a, a)]
group [] = []
group (x : y : z : xs) = (x, y, z) : group xs

solve :: Int -> [(Int, Int, Int)] -> [Bool]
solve _ [] = []
solve d ((x, y, z) : xs) =
  let a = d + x
      b = d + y + z
   in (a < b) : solve (if a < b then a else b) xs

main :: IO ()
main = interact $ concatMap (\x -> if x then "cross forward cross " else "forward ") . solve 0 . group . map read . words
