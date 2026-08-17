nums = [1..100]

sumNums = sum nums
sumNumsSquared = sumNums * sumNums
sumSquares = sum [num * num | num <- nums]

main = print $ sumNumsSquared - sumSquares
