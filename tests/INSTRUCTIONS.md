# Unit Test Instructions for MoonFishHypeBot

This directory contains individual unit test scripts for each function in `main.py`.

## How to Run Tests

1. **Activate your virtual environment** (if not already):
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`

2. **Run all tests in the directory:**

   ```bash
   python -m unittest discover -s tests
   ```

3. **Run a specific test file:**

   ```bash
   python -m unittest tests/test_load_keywords_file.py
   ```

   (Replace with any test file name as needed)

## Adding New Tests

- Create a new file in this directory named `test_<function_name>.py`.
- Use the `unittest` framework for consistency.
- Each test file should contain tests for a single function from `main.py`.

## Best Practices

- Keep tests focused and independent.
- Use descriptive test method names.
- Validate both expected and edge-case behavior.
- Update the README file if you add new test files or change the test structure.

---

For questions or issues, see the main project README or open an issue on GitHub.
