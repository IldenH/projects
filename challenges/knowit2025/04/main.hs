import Data.Maybe (listToMaybe)

parse [] acc chars = length chars
parse (x : xs) acc chars
  | acc <= 0 = (length chars - 1) * 10
  | otherwise =
      let prev1 = listToMaybe chars
          prev2 = listToMaybe (drop 1 chars)
          result = case x of
            'S' -> (-5)
            'B' -> (-10)
            'D' -> (-15)
            'I' -> 0
            'P' ->
              ( case prev1 of
                  Just 'S' -> 5
                  Just 'B' -> 10
                  Just 'D' -> 15
                  otherwise -> 0
              )
                + ( case prev2 of
                      Just 'S' -> 5
                      Just 'B' -> 10
                      Just 'D' -> 15
                      otherwise -> 0
                  )
       in parse xs (acc + result) (x : chars)

main :: IO ()
main = do
  contents <- getContents
  putStr $ show $ parse contents 3000 []
