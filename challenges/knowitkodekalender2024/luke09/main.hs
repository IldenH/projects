import Data.List (isPrefixOf)
import Data.Maybe (fromMaybe)

numbers :: [(String, Int)]
numbers = [("nitti", 90), ("åttifire", 84), ("syttiåtte", 78), ("syttito", 72), ("seksti", 60), ("femtifire", 54), ("førtiåtte", 48), ("førtito", 42), ("tretti", 30), ("tjuefire", 24), ("atten", 18), ("tolv", 12), ("seks", 6)] -- 96, 66 og 36 fjernet grunnet at 6 allerede ordner dem

-- stringToNumber :: String -> Int
-- stringToNumber text = fromMaybe 0 $ lookup text numbers

decode :: String -> Maybe [Int]
decode [] = Just []
decode text = tryMatches matches
  where
    matches = [(number, value) | (number, value) <- numbers, number `isPrefixOf` text]

    tryMatches :: [(String, Int)] -> Maybe [Int]
    tryMatches [] = Nothing
    tryMatches ((number, value) : remainingNumbers) = case decode (drop (length number) text) of
      Just result -> Just (value : result)
      Nothing -> tryMatches remainingNumbers

-- occurrences :: String -> String -> Int
-- occurrences search = count 0
--   where
--     count accumulator [] = accumulator
--     count accumulator text
--       | search `isPrefixOf` text = count (accumulator + 1) (drop (length search) text)
--       | otherwise = count accumulator (tail text)
--
-- occurrences' :: String -> String -> Int
-- occurrences' tallTekst inputFile = occurrences tallTekst inputFile * stringToNumber tallTekst `div` 6
--
-- snøfnugg :: String -> [Int]
-- snøfnugg inputFile = map (\(key, value) -> occurrences' key inputFile) numbers

main :: IO ()
main = do
  inputFile <- readFile "tall.txt"
  -- print $ sum $ snøfnugg inputFile
  print $ fmap ((`div` 6) . sum) (decode inputFile)
