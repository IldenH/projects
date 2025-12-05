parseRange :: String -> (Int, Int)
parseRange s =
  let (min, _ : max) = break (== '-') s
   in (read min, read max)

isFresh :: [(Int, Int)] -> Int -> Bool
isFresh bounds x = foldl (\acc (min, max) -> if min < x && x < max then True else acc) False bounds

main :: IO ()
main = do
  rangesContents <- readFile "ranges.txt"
  idsContents <- readFile "ids.txt"
  let ranges = map parseRange . lines $ rangesContents
  let ids = map read . lines $ idsContents
  putStr $ show . length . filter (== True) . map (isFresh ranges) $ ids
