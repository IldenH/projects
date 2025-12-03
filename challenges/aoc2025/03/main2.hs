-- part 2

import Data.Char
import Data.List
import Data.Maybe

solve :: (Num a) => String -> Int -> Int -> [a] -> String -> [a]
solve xs n0 n nums toCheck
  | length xs == 0 || length nums >= n0 = reverse $ nums
  | otherwise =
      let (i : _) = mapMaybe (`elemIndex` xs) toCheck
          num = digitToInt $ xs !! i
       in case (length xs - i) `compare` n of
            LT -> solve xs n0 n nums (drop 1 toCheck)
            otherwise -> solve (drop (i + 1) xs) n0 (n - 1) (fromIntegral num : nums) ['9', '8' .. '1']

solve' :: (Num a) => String -> a
solve' xs = foldl (\acc x -> acc * 10 + x) 0 $ solve xs 12 12 [] ['9', '8' .. '1']

main :: IO ()
main = do
  contents <- getContents
  putStr $ show . sum . map solve' . lines $ contents
