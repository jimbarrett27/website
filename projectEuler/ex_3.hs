import Data.List (find)

--composite = 13195
composite = 600851475143

primesFromCandidates :: [Int] -> [Int]
primesFromCandidates (p:xs) = p : primesFromCandidates (filter (\y -> (mod y p) /= 0) xs)
primes = primesFromCandidates [2..]

smallestFactor x = case find (\y -> (mod x y) == 0) (takeWhile (\y -> y*y <= x) primes) of
    Just y -> y
    Nothing -> x

primeFactors 1 = []
primeFactors x = let p = smallestFactor x 
    in takeWhile (\y -> y > 1) (p : primeFactors (x `div` p))

biggestPrimeFactor x = last (primeFactors x)

main = print $ biggestPrimeFactor composite