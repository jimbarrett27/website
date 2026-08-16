numbs = [100..999]
allProds = [x * y | x <- numbs, y <- numbs]

isPalindrome x = let strNumb = show x in strNumb == reverse strNumb

palindromes = filter isPalindrome allProds

main = print $ maximum palindromes