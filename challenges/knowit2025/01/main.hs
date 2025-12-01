import Data.Char

type Command = (String, Char)

commands :: String -> [Command]
commands = map (\(x : xs) -> (x, if xs == [] then ' ' else let ((x : _) : _) = xs in x)) . map words . lines

handleCommands :: [Command] -> String -> String -> String
handleCommands [] _ acc = reverse $ acc
handleCommands (c : cs) accitems acc = case fst c of
  "ADD" -> handleCommands cs (snd c : accitems) acc
  "PROCESS" -> handleCommands cs (init accitems) ((if accitems == "" then 'X' else last accitems) : acc)
  "COUNT" -> handleCommands cs accitems ((last $ show . length $ accitems) : acc)

main :: IO ()
main = do
  contents <- getContents
  putStrLn $ handleCommands (commands contents) "" ""
