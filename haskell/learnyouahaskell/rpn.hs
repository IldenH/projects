-- reverse polish notation

example = words "10 4 3 + 2 * -"

type Operator = Integer -> Integer -> Integer

toOp :: [(String, Operator)]
toOp =
  [ ("+", (+)),
    ("*", (*)),
    ("-", (-)),
    ("/", div)
  ]

rpn :: [String] -> [Integer] -> Integer
rpn [] [s] = s
-- rpn (x : xs) stack@(s1 : s2 : ss) =
rpn (x : xs) stack =
  case lookup x toOp of
    Nothing -> rpn xs (read x : stack)
    Just op -> rpn xs ((stack !! 1) `op` (stack !! 0) : drop 2 stack)
