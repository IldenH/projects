import Data.Char
import Data.List
import qualified Data.Map as M
import Data.Maybe
import qualified Data.Set as S

parse s =

main = do
  contents <- map parse . lines <$> readFile "input.txt"
  print $ solve contents
