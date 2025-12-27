import qualified Data.ByteString as S
import qualified Data.ByteString.Lazy as B
import System.Environment
import System.IO.Error

main :: IO ()
main = do
  catchIOError
    ( do
        (f : _) <- getArgs
        contents <- readFile f
        print $ length $ lines contents
    )
    $ \e -> case e of
      _
        | isDoesNotExistError e -> case ioeGetFileName e of
            Just f -> putStrLn $ "File " ++ f ++ " doesn't exist"
            Nothing -> putStrLn "File doesn't exist"
        | isUserError e -> do
            progName <- getProgName
            putStrLn $ "Usage: " ++ progName ++ " [file]"
        | otherwise -> ioError e
