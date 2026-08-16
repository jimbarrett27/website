tot = 4000000

fib 0 = 1
fib 1 = 1
fib x = (fib $ x-1) + (fib $ x-2)

lowerThanTot x = x < tot
evenFib = filter even $ map fib [1..]

answer = sum $ takeWhile lowerThanTot evenFib

main = print answer