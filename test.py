from pyserve import remote


# Test remote function
hello = remote("hello")
print(hello())
add = remote("add")
print(add(2, 3))
subtract = remote("subtract")
print(subtract(5, 2))

# Test remote object
calc = remote("calc")
print(calc.name)  # Should be "Simple Calculator"
print(calc.last_result)  # Should be None
print(calc.multiply(4, 5))  # Should be 20
print(calc.last_result)  # Should be 20
print(calc.divide(10, 2))  # Should be 5
print(calc.last_result)  # Should be 5
print(calc(3, 7))  # Should be 10 (calls __call__ which adds the numbers)

# Test remote class
Calculator = remote("Calculator")
calc_1 = Calculator()  # Should create a new instance of Calculator on the server
calc_2 = Calculator()  # Should create another instance of Calculator on the server
print(calc_1.name)  # Should be "Simple Calculator"
print(calc_2.name)  # Should be "Simple Calculator"
print(calc_1.multiply(2, 3))  # Should be 6
print(calc_2.multiply(4, 5))  # Should be 20
print(calc_1.last_result)  # Should be 6
print(calc_2.last_result)  # Should be 20