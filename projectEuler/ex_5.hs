divisors = [1..20]
bigStep = maximum divisors

trials = [bigStep, 2*bigStep..]

dividesAll trial = all (\x -> (trial `mod` x) == 0) (reverse divisors)

main = print (head $ filter dividesAll trials)

