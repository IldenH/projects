double :: (Num a) => a -> a
double x = x * 2

main :: IO ()
main = do
  print
    "Hello, world!"
  print $ double 3
  let tall =
        [1, 2, 3, 4, 5]
  print $ map (* 2) tall
