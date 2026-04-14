def hello() -> str:
    return "Hello, world!"

def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b

class Calculator:
    name: str = "Simple Calculator"

    def __init__(self):
        self.last_result = None

    def __call__(self, a: float, b: float) -> float:
        return add(a, b)

    def multiply(self, a: float, b: float) -> float:
        self.last_result = a * b
        return self.last_result

    def divide(self, a: float, b: float) -> float:
        self.last_result = a / b
        return self.last_result
    
calc = Calculator()