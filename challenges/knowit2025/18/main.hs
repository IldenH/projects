import Data.List
import qualified Data.Map as M
import Data.Ord (comparing)

parse :: Int -> Int -> Int -> Int -> [String] -> [(Int, [String])]
parse w h gapw gaph xs = concat $ go (map parseRow xs) 1
  where
    parseRow s =
      let (a, rest1) = splitAt w s
          (b, rest2) = splitAt w $ drop gapw rest1
          (c, rest3) = splitAt w $ drop gapw rest2
       in [a, b, c]
    go [] _ = []
    go xs n = zip [n ..] go' : go (drop (h + gaph) xs) (n + 3)
      where
        go' = transpose $ take h xs

mode :: [(Int, [String])] -> [String]
mode = fst . maximumBy (comparing snd) . M.toList . M.fromListWith (+) . map (\(_, x) -> (x, 1))

main :: IO ()
main = do
  contents <- parse 20 10 3 1 . lines <$> readFile "input.txt"
  putStrLn . concatMap (show . fst) . filter ((== mode contents) . snd) $ contents
