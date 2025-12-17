import Data.List
import Data.Maybe

data Command = ROLL Int | STACK | HAT | CARROT deriving (Read, Show, Eq)

data Snowman = Snowman
  { ball :: Int,
    hat :: Bool,
    carrot :: Bool
  }
  deriving (Show, Eq, Ord)

parse :: String -> Command
parse s =
  case words s of
    "ROLL" : xs -> ROLL (length xs + 1)
    [x] -> read x

isReady :: Snowman -> Bool
isReady (Snowman x _ _) = x == 3

isOk :: Snowman -> Bool
isOk (Snowman _ y z) = y && z

updateAt :: Int -> (a -> a) -> [a] -> [a]
updateAt i f =
  zipWith (\idx x -> if idx == i then f x else x) [0 ..]

decorate :: (Snowman -> Snowman) -> [Snowman] -> Maybe (Int, Snowman) -> [Snowman]
decorate _ acc Nothing = acc
decorate f acc (Just (i, s)) = updateAt i f acc

solve :: [Command] -> [Snowman] -> [Int] -> [Snowman]
solve [] acc _ = acc
solve (x : xs) acc balls =
  let ready =
        reverse
          . sortOn snd
          . filter (isReady . snd)
          $ zip [0 ..] acc
      one = find (\(_, x) -> ball x == 1) $ zip [0 ..] acc
      two = find (\(_, x) -> ball x == 2) $ zip [0 ..] acc
      noHat = find (not . hat . snd) ready
      noCarrot = find (not . carrot . snd) ready
   in case x of
        ROLL 3 -> solve xs (Snowman 1 False False : acc) balls
        ROLL n -> solve xs acc (n : balls)
        STACK ->
          case balls of
            1 : bs -> solve xs (decorate (\s -> s {ball = ball s + 1}) acc two) bs
            2 : bs -> solve xs (decorate (\s -> s {ball = ball s + 1}) acc one) bs
            bs -> solve xs acc (drop 1 bs)
        HAT -> solve xs (decorate (\s -> s {hat = True}) acc noHat) balls
        CARROT -> solve xs (decorate (\s -> s {carrot = True}) acc noCarrot) balls

main :: IO ()
main = do
  cs <- map parse . lines <$> readFile "commands.txt"
  print $ length $ filter isOk $ solve cs [] []
