# PyServe

> Turn your Python functions, classes, and objects into callable services instantly.

**PyServe** is a lightweight framework that exposes your Python code as a local service with a single command. It lets you serve functions, classes, or stateful objects without writing any API boilerplate, and interact with them through a simple Python client.

Instead of building and maintaining server code (e.g., with FastAPI or Flask), you focus on your application logic, PyServe handles the serving layer and execution for you.

## 📦 Install
```bash
pip install python-serve
```

## 🚀 Quick Start
### 🔹 Serve Functions
Expose one or more functions with a single command:

```python
# calculator.py
def add(a: float, b: float) -> float:
    return a + b

def subtract(a: float, b: float) -> float:
    return a - b
```
```bash
pyserve serve calculator:add,subtract
```
```
🌐 PyServe is live:
- http://localhost:8000/add (function)
- http://localhost:8000/subtract (function)
```

Call them from Python:

```python
from pyserve import remote

add = remote("add")
subtract = remote("subtract")

print(add(5, 3))      # → 8
print(subtract(5, 3)) # → 2
```

PyServe supports multiple Python abstractions with a unified interface.

### 🔹 Serve Classes
Serve a class definition. Each call creates a new isolated instance on the server.

```python
# calculator_class.py
class Calculator:
    def add(self, a: float, b: float) -> float:
        return a + b
    
    def subtract(self, a: float, b: float) -> float:
        return a - b
```
```bash
pyserve serve calculator_class:Calculator
```
```python
from pyserve import remote

Calculator = remote("Calculator")

calc = Calculator()
print(calc.add(5, 3))      # → 8
print(calc.subtract(5, 3)) # → 2
```

### 🔹 Serve Objects (Stateful)
Serve an existing object to preserve state across calls.

```python
# calculator_class.py
class Calculator:
    def __init__(self):
        self.last_result = None

    def add(self, a: float, b: float) -> float:
        self.last_result = a + b
        return self.last_result
    
    def subtract(self, a: float, b: float) -> float:
        self.last_result = a - b
        return self.last_result

calc = Calculator()
```
```bash
pyserve serve calculator_class:calc
```
```python
from pyserve import remote

calc = remote("calc")
print(calc.add(5, 3))      # → 8
print(calc.last_result)    # → 8
print(calc.subtract(5, 3)) # → 2
print(calc.last_result)    # → 2
```

## 🔧 Configuration
PyServe provides flexible runtime configuration via CLI flags:

```bash
pyserve serve calculator:add,subtract \
--host localhost \         # Bind address (default: localhost)
--port 8080 \              # Port (default: 8000)
--workers 4 \              # Worker threads (default: 2 × CPU cores)
--max-concurrency 100 \    # Max concurrent requests
--timeout 30 \             # Request timeout (seconds)
--cachable \               # Enable result caching
--cache-size 10000         # Cache capacity
```