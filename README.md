# SnapServe

> Turn your Python functions, classes, objects, and variables into remotely accessible artifacts with zero boilerplate.

**SnapServe** is a lightweight library for exposing Python functions, classes, objects, and variables as remotely accessible artifacts in a single command line of code without writing API boilerplate. Whether you want to build a simple microservice, share a machine learning model, or provide a remote interface to your Python code, SnapServe makes it easy to expose and use Python functionality over the network.


## 📦 Install
```bash
pip install snapserve
```

## 🚀 Quick Start

### Define your Python artifacts
Create a file with anything you want to expose: functions, classes, objects, or variables:
```python
# calculator.py

def add(a: float, b: float) -> float:
    return a + b

class Calculator:
    def __init__(self, bias: float = 0.0):
        self.bias = bias

    def multiply(self, a: float, b: float) -> float:
        return a * b + self.bias

calc = Calculator(bias=2.0)

z = 10
```

### Serve them easily
Expose anything with a single command:
```bash
snapserve serve calculator \
--expose add,Calculator,calc,z \  # List of artifacts to expose (comma-separated)
--host localhost \
--port 8000
```

### Use them remotely
Connect from any Python script:
```python
from snapserve import Remote

with Remote("http://localhost:8000") as remote:
  # Now you can call remote.add, remote.Calculator, remote.calc, and remote.z here as if they were local!
  # 🔹 Functions: Call remote functions like local ones
  result = remote.add(5, 3)
  print(result)   # → 8
  # 🔹 Classes: Instantiate and use remote classes
  calc = remote.Calculator(bias=1.0) # Instantiate with custom arguments
  result = calc.multiply(5, 3)
  print(result)   # → 16 (5 * 3 + 1.0)
  # 🔹 Objects: Use pre-initialized remote objects
  result = remote.calc.multiply(5, 3)
  print(result)   # → 17 (5 * 3 + 2.0)
  # 🔹 Variables: Access shared variables directly
  print(remote.z) # → 10
  remote.z = 20   # Remote variable can be updated and will reflect across all clients
  remote.z += 10  # Remote variable can be updated with operations
  print(remote.z) # → 30
# After the with block, the instantiated objects created on the server will be automatically cleaned up.
```

## 🛠️ CLI Commands

Serve Python functions, classes, and objects as an API.
```
Usage: snapserve serve [OPTIONS] MODULE_PATH
Arguments:
  MODULE_PATH  The module path to serve.
Options:
  --expose STRING         Comma-separated list of artifacts to expose (functions, classes, objects, variables).
  --host STRING           The host to bind the server to. [default: localhost]
  --port INTEGER          The port to bind the server to. [default: 8000]
  --workers INTEGER       The number of worker threads to handle requests. [default: 2 × CPU cores]
  --max-concurrency INTEGER  The maximum number of concurrent requests the server can handle. [default: 100]
  --timeout INTEGER       The request timeout in seconds. [default: 30]
  --allow-cache           Enable caching of function results to improve performance for repeated calls with the same arguments.
  --cache-size INTEGER    The maximum number of entries to store in the cache. [default: 10000]
  --daemon                Run the server as a background daemon process.
```

List all running snapserve servers.
```
Usage: snapserve ps
```

Stop a running snapserve server.
```
Usage: snapserve stop [OPTIONS] SERVER_ID
Arguments:
  SERVER_ID  The ID of the server to stop.
Options:
  --all                   Stop all running servers.
  --delete                Delete the server after stopping it.
```

Start a stopped snapserve server.
```
Usage: snapserve start [OPTIONS] SERVER_ID
Arguments:
  SERVER_ID  The ID of the server to start.
Options:
  --host STRING           The host to bind the server to.
  --port INTEGER          The port to bind the server to.
```