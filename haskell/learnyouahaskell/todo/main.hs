import System.Environment
import System.IO

cmds :: [(String, [String] -> IO ())]
cmds =
  [ ("view", view),
    ("add", add),
    ("remove", remove),
    ("clear", clear)
  ]

view :: [String] -> IO ()
view (f : _) = do
  xs <- lines <$> readFile f
  mapM_ putStrLn $ zipWith (\i x -> show i ++ " - " ++ x) [0 ..] xs

add :: [String] -> IO ()
add (f : x : _) = appendFile f $ x ++ "\n"

remove :: [String] -> IO ()
remove (f : n : _) = do
  xs <- lines <$> readFile' f
  let (prev, xs') = splitAt (read n) xs
      after = prev ++ drop 1 xs'
  writeFile f $ unlines after

clear :: [String] -> IO ()
clear (f : _) = writeFile f ""

main :: IO ()
main = do
  cmd : args <- getArgs
  let (Just action) = lookup cmd cmds
  action args
