dx = 0.001

f x = x ** 2

ds dy = sqrt $ dx ** 2 + dy ** 2

dy x = (f (x + dx) - f x)

bue a b = sum $ map (ds . dy) [a, a + dx .. b]

main = print $ bue (-2.0) 2.0
