-- part 2

import Data.Char
import Data.List
import qualified Data.Set as S

parseInt :: String -> Int
parseInt = foldl (\acc x -> acc * 10 + x) 0 . map digitToInt

parseRange :: String -> [Int]
parseRange [] = []
parseRange r =
  let (r1, _ : r2) = break (== '-') r
   in [parseInt r1 .. parseInt r2]

parseRanges :: String -> [[Int]] -> [[Int]]
parseRanges [] acc = acc
parseRanges ranges acc =
  let (r, _ : rs) = break (== ',') ranges
   in parseRanges rs (parseRange r : acc)

rangesRaw = S.fromList . concat . parseRanges "990244-1009337,5518069-5608946,34273134-34397466,3636295061-3636388848,8613701-8663602,573252-688417,472288-533253,960590-988421,7373678538-7373794411,178-266,63577667-63679502,70-132,487-1146,666631751-666711926,5896-10827,30288-52204,21847924-21889141,69684057-69706531,97142181-97271487,538561-555085,286637-467444,93452333-93519874,69247-119122,8955190262-8955353747,883317-948391,8282803943-8282844514,214125-236989,2518-4693,586540593-586645823,137643-211684,33-47,16210-28409,748488-837584,1381-2281,1-19," $ []

invalids :: [Int]
invalids = nub . concat . map invalids' $ toCheck
  where
    maxNum = show $ maximum rangesRaw
    halfMaxNum
      | length maxNum `rem` 2 /= 0 = length maxNum `div` 2 + 1
      | otherwise = length maxNum `div` 2
    toCheck = [1 .. parseInt (take halfMaxNum maxNum)]

    invalids' x = map parseInt . drop 1 . takeWhile (\x -> parseInt x <= maximum rangesRaw) $ iterate (++ (show x)) $ show x

-- Numeric and roughly 20 times faster
invalids' :: [Int]
invalids' = concatMap invalids'' $ toCheck
  where
    maxNum = show $ maximum rangesRaw
    halfMaxNum
      | length maxNum `rem` 2 /= 0 = length maxNum `div` 2 + 1
      | otherwise = length maxNum `div` 2
    toCheck = [1 .. parseInt (take halfMaxNum maxNum)]

    invalids'' :: Int -> [Int]
    invalids'' x = drop 1 . takeWhile (\x -> x <= maximum rangesRaw) $ iterate (\n -> n * factor + x) x
      where
        factor = 10 ^ (length $ show x)

main :: IO ()
main = do
  putStr $ show . sum . S.intersection rangesRaw $ S.fromList invalids'
