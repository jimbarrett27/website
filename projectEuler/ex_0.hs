tot = 117000

square x = x * x
squares = map square [1..tot]
oddSquares = filter odd squares 
oddSquaresSum = sum oddSquares

main = print oddSquaresSum