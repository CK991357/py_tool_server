# Python Sandbox Service: User & Developer Guide

## 1. Overview

The Python Sandbox Service provides a secure and isolated environment to execute arbitrary snippets of Python code. It is designed primarily as a tool for AI models, enabling them to perform calculations, run algorithms, and manipulate data without exposing the host system to any security risks.

The core design philosophy is **"security-first"**. Every component of the service is built to minimize risk, assuming that the code provided for execution may be untrusted or even malicious. Each execution run is completely ephemeral and stateless.

## 2. Core Capabilities & Security Design

The service's power comes from its multi-layered security model, which strictly defines what code can and cannot do.

### 2.1 Security Layers

-   **Docker Container Isolation**: Every piece of code runs in its own dedicated, single-use Docker container. This container is built from a custom image based on `python:3.11-slim` that includes the libraries listed below. The container is automatically destroyed after execution, ensuring no state persists between runs.
-   **No Network Access**: The container is started with `network_disabled=True`. This provides a complete guarantee that the executed code cannot make any internal or external network calls.
-   **Read-Only Filesystem**: The container's filesystem is mounted as read-only (`read_only=True`). The code cannot write or modify any files within the container.
-   **Strict Resource Limits**: To prevent denial-of-service attacks or resource abuse, each container is capped at **512MB of RAM** and **50% of a single CPU core**.
-   **Interpreter-Level Sandbox**: The Python `exec` function is called with a restricted list of safe built-in functions. This prevents access to dangerous functions (like `open`, `eval`) even within the container, providing a second layer of security.

### 2.2 Available Libraries
The sandbox comes pre-installed with a curated set of popular libraries for data science and symbolic mathematics.

-   **Numpy**: The fundamental package for scientific computing with Python. Used for high-performance multi-dimensional array objects and tools for working with these arrays.
-   **Pandas**: A fast, powerful, and easy-to-use open-source data analysis and manipulation tool. Essential for working with structured data.
-   **Openpyxl**: A Python library to read/write Excel 2010 xlsx/xlsm/xltx/xltm files in memory.
-   **Sympy**: A Python library for symbolic mathematics. It aims to become a full-featured computer algebra system (CAS) while keeping the code as simple as possible in order to be comprehensible and easily extensible.

Python's extensive **Standard Library** is also available (e.g., `math`, `random`, `datetime`, `json`, `re`).

## 3. Usage Scenarios & Examples

### Scenario 1: Advanced Calculations with Numpy
Use `numpy` for complex numerical operations.

**Example Code:**
```python
import numpy as np

# Create two matrices
matrix_a = np.array([[1, 2], [3, 4]])
matrix_b = np.array([[5, 6], [7, 8]])

# Perform matrix multiplication
result = np.dot(matrix_a, matrix_b)

print("Matrix A:\n", matrix_a)
print("Matrix B:\n", matrix_b)
print("Result of multiplication:\n", result)
```
**Expected JSON Output:**
```json
{
  "stdout": "Matrix A:\n [[1 2]\n [3 4]]\nMatrix B:\n [[5 6]\n [7 8]]\nResult of multiplication:\n [[19 22]\n [43 50]]\n",
  "stderr": "",
  "exit_code": 0
}
```

### Scenario 2: Data Manipulation with Pandas
Use `pandas` to create and manipulate a simple DataFrame.

**Example Code:**
```python
import pandas as pd

# Create a sample dataset
data = {
    'Product': ['A', 'B', 'C', 'D'],
    'Sales': [150, 200, 180, 220]
}
df = pd.DataFrame(data)

# Calculate total sales
total_sales = df['Sales'].sum()

print("Sales Data:\n", df)
print("\nTotal Sales:", total_sales)
```
**Expected JSON Output:**
```json
{
  "stdout": "Sales Data:\n   Product  Sales\n0       A    150\n1       B    200\n2       C    180\n3       D    220\n\nTotal Sales: 750\n",
  "stderr": "",
  "exit_code": 0
}
```

## 4. Limitations

It is critical to understand what this service **cannot** do:
-   **No Internet Access**: Cannot make API calls, download files, or access any network resources.
-   **No File I/O**: Cannot read from or write to any files. The `openpyxl` library can only operate on data in memory, not from disk.
-   **No Plotting**: Visualization libraries like `matplotlib` and `seaborn` are not installed to keep the service lightweight and focused on data processing and calculations.
-   **Stateless**: Each execution is independent. Variables or state from one run cannot be used in another.
-   **Memory Constraints**: While the memory limit is 512MB, it is still possible to exhaust this with very large datasets. Libraries like `scikit-learn` or `scipy` have been intentionally excluded as they can be memory-intensive.