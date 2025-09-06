# Python Sandbox Service: User & Developer Guide

## 1. Overview

The Python Sandbox Service provides a secure and isolated environment to execute arbitrary snippets of Python code. It is designed primarily as a tool for AI models, enabling them to perform calculations, run algorithms, and manipulate data without exposing the host system to any security risks.

The core design philosophy is **"security-first"**. Every component of the service is built to minimize risk, assuming that the code provided for execution may be untrusted or even malicious. Each execution run is completely ephemeral and stateless.

## 2. Core Capabilities & Security Design

The service's power comes from its multi-layered security model, which strictly defines what code can and cannot do.

### 2.1 Security Layers

-   **Docker Container Isolation**: Every piece of code runs in its own dedicated, single-use Docker container based on the `python:3.11-slim` image. The container is automatically destroyed after execution, ensuring no state persists between runs.
-   **No Network Access**: The container is started with `network_disabled=True`. This provides a complete guarantee that the executed code cannot make any internal or external network calls.
-   **Read-Only Filesystem**: The container's filesystem is mounted as read-only (`read_only=True`). The code cannot write or modify any files within the container.
-   **Strict Resource Limits**: To prevent denial-of-service attacks or resource abuse, each container is capped at **256MB of RAM** and **50% of a single CPU core**.
-   **Restricted Python Built-ins**: This is the innermost security layer. Before the user's code is executed, the Python runtime itself is modified to only allow a small, safe subset of built-in functions. Dangerous functions that could be used to bypass security (like `open`, `import`, `eval`) are removed.

### 2.2 Available Libraries & Functions

#### Permitted Built-in Functions
The following is an exhaustive list of the Python `__builtins__` that are available to the code:
`print`, `len`, `range`, `str`, `int`, `float`, `bool`, `list`, `dict`, `set`, `tuple`, `max`, `min`, `sum`, `abs`, `round`.

Any attempt to use a built-in function not on this list will result in an error.

#### Python Standard Library
Most modules from the Python 3.11 Standard Library that do **not** perform networking or filesystem operations are available. Because the `import` statement is disabled in the main execution scope, these modules can only be used if they are imported *within* the provided code snippet itself.

**Examples of usable standard libraries:**
- `math` for advanced mathematical calculations.
- `random` for generating random numbers.
- `datetime` for time and date manipulation.
- `re` for regular expression-based text processing.
- `json` for working with JSON data structures.
- `collections` for advanced data structures.

#### Third-Party Libraries
**None.** The base Docker image (`python:3.11-slim`) is minimal and does not include any third-party libraries like `numpy`, `pandas`, `requests`, etc.

## 3. Usage Scenarios & Examples

This service excels at tasks that are purely computational or algorithmic.

### Scenario 1: Advanced Calculator
Use the service to solve complex mathematical expressions or problems that go beyond basic arithmetic.

**Example Code:**
```python
import math

# Calculate the hypotenuse of a right triangle
a = 15
b = 20
c = math.sqrt(a**2 + b**2)
print(f"The hypotenuse is: {c}")

# Calculate factorial
print(f"Factorial of 6 is: {math.factorial(6)}")
```

### Scenario 2: Data Manipulation and Algorithmic Tasks
Perform operations like sorting, filtering, or transforming data structures.

**Example Code:**
```python
# Sort a list of dictionaries by a specific key
data = [
    {'name': 'Alice', 'age': 30},
    {'name': 'Bob', 'age': 25},
    {'name': 'Charlie', 'age': 35}
]
sorted_data = sorted(data, key=lambda x: x['age'])
print(sorted_data)
```

### Scenario 3: Text Processing
Use regular expressions or string methods to parse and analyze text.

**Example Code:**
```python
import re

text = "The quick brown fox jumps over the lazy dog. The fox is happy."
# Find all occurrences of the word "fox"
matches = re.findall(r'fox', text)
print(f"Found 'fox' {len(matches)} times.")
```

## 4. Limitations

It is critical to understand what this service **cannot** do:
-   **No Internet Access**: Cannot make API calls, download files, or access any network resources.
-   **No File I/O**: Cannot read from or write to any files.
-   **No Third-Party Libraries**: Cannot use popular libraries like `numpy`, `pandas`, `matplotlib`, `requests`, etc.
-   **Stateless**: Each execution is independent. Variables or state from one run cannot be used in another.

## 5. Future Expansion & Potential

The current service provides a powerful but minimal foundation. It can be extended in several ways to unlock new capabilities:

1.  **Adding Third-Party Libraries**:
    -   **How**: Create a new `Dockerfile` that inherits from `python:3.11-slim` and adds a `RUN pip install ...` command to include trusted, popular libraries like `numpy`, `pandas` (for data analysis), or `sympy` (for symbolic mathematics).
    -   **Impact**: This would dramatically increase the service's utility for data science and mathematical tasks, turning it into a true "Code Interpreter".

2.  **Enabling Plotting & Charting**:
    -   **How**: Install a library like `matplotlib` into a custom Docker image. Configure it to use a non-interactive backend (e.g., `agg`). The code could then generate a plot, save it to an in-memory buffer (e.g., `io.BytesIO`), and the service could return the image as a base64-encoded string in the JSON output.
    -   **Impact**: Allows the AI model to visualize data, creating charts and graphs based on calculations.

3.  **Introducing Stateful Sessions**:
    -   **How**: This is a more complex architectural change. It would involve modifying the service to manage persistent container sessions for each user. A request would include a `session_id`, and the service would route the code to the corresponding running container. A timeout mechanism would be needed to terminate inactive sessions.
    -   **Impact**: Would allow for iterative work, where a model could define a variable in one call and use it in the next, mimicking a true Jupyter Notebook experience. This would require careful security consideration to prevent state-related vulnerabilities.

4.  **Controlled File System Access**:
    -   **How**: For each execution, create and mount a temporary, isolated directory (`tmpfs`) into the container. The code would be allowed to read and write files *only* within this temporary workspace. The service could then be extended to optionally return specified output files (e.g., a generated CSV) as part of the response.
    -   **Impact**: Enables more complex data processing tasks where intermediate files are needed, or where the final output is a file rather than just text.