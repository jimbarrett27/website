tot = 1000

isMultThreeOrFive x = (mod x 3 == 0) || (mod x 5 == 0)
relevantNums = filter isMultThreeOrFive [1..(tot-1)]
answer = sum relevantNums

main = print answer

