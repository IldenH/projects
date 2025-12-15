import Data.List

start = 167772150

goal = 149848566

total = sum $ map (2 ^) [0 .. 23]

sjokolade = start `div` total

mockulade = sjokolade * (100 - 30) `div` 100

-- x + y = total
-- 10x + 7y = goal
amountSjokolade = 10802687

amountMockulade = 5974528

toBinary 0 = [0]
toBinary n = go n
  where
    go 0 = []
    go x = (x `mod` 2) : go (x `div` 2)

main :: IO ()
main = do
  let luker = map fst $ filter (\(_, x) -> x == 1) $ zip [1 ..] $ toBinary amountMockulade
  putStrLn $ "SjokoladeMg:" ++ show sjokolade ++ ",MockuladeMg:" ++ show mockulade ++ ",AntallMockulader:" ++ show amountMockulade ++ ",Luker:" ++ intercalate "," (map show luker)
