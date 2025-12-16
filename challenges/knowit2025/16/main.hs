type Pos = (Int, Int)

parse :: String -> (Pos, String)
parse s =
  let (_, rest1) = span (== '[') s
      (pos, rest2) = break (== ']') rest1
      (_, rest3) = break (/= '(') $ snd $ break (== '(') rest2
      (color, _) = break (== ')') rest3
   in (read ("(" ++ pos ++ ")"), color)

main :: IO ()
main = do
  contents <- map parse . words <$> readFile "input.txt"
  print contents
