digits :: Int -> [Int]
digits number
  | number == 0 = [0]
  | otherwise = digits' number []
  where
    digits' :: Int -> [Int] -> [Int]
    digits' 0 accumulator = accumulator
    digits' number accumulator = digits' (number `div` 10) (number `mod` 10 : accumulator)

juletall :: Int -> Bool
juletall number = isJuletall number == 1
  where
    isJuletall :: Int -> Int
    isJuletall 1 = 1
    isJuletall number = isJuletall (sum $ map (^ 2) (digits number))

main :: IO ()
main = do
  print $ juletall 19
