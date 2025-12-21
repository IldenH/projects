import Data.List

alphabet = ['A' .. 'Z'] ++ "ÆØÅ"

alphabetIdx = [-l, -l + 1 .. l]
  where
    l = length alphabet

caesar [] _ acc = acc
caesar (x : xs) shift acc =
  let new = case x `elemIndex` alphabet of
        Just i -> alphabet !! ((i + shift) `mod` length alphabet)
        Nothing -> x
   in caesar xs shift (new : acc)

input =
  [ "VÆFUPO",
    "VEFZ SP IUHRZ",
    "JUTGR PCUJWPGT XRN QRWYGT"
  ]

getShift x y = map fst $ filter ((== y) . snd) $ map (\i -> (i, caesar x i [])) [0 .. length alphabet]

getShifts x y = concat $ filter (\x' -> length x' == 1) $ map (\(x', y') -> getShift [x'] [y']) $ zip x y

shifts = cycle $ reverse $ drop 2 $ reverse $ getShifts "VEFZ SP IUHRZ" "RØDT OG GRØNT"

solution = concatMap (\(s, x) -> caesar [x] s []) $ zip shifts "JUTGRPCUJWPGTXRNQRWYGT"
