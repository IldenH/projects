-- 5g av en type og 3g av en annen type
-- 2g kjøtt om gangen
-- 1g julekringle om gangen, går ikke å spise sammen med annet
--
tallerken :: [(String, Int)]
tallerken = [("ris", 100), ("erter", 100), ("gulrøtter", 100), ("reinsdyrkjøtt", 100), ("julekringle", 100)]

påfyll = [("ris", [0, 0, 1, 0, 0, 2]), ("erter", [0, 3, 0, 0]), ("gulrøtter", [0, 1, 0, 0, 0, 8]), ("reinsdyrkjøtt", [100, 80, 40, 20, 10])]

main :: IO ()
main = do
  print tallerken
  print påfyll
  print $ map (\(key, value) -> value + 1) tallerken
