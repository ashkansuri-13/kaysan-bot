# Contributing to Kaysan AI Bot

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Style](#code-style)
- [Testing](#testing)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help newcomers feel welcome

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.12+
- Git
- pip or poetry

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/kaysan-bot.git
cd kaysan-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Run the bot
python run.py
```

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Use the Bug Report template
3. Include steps to reproduce
4. Include your environment details

### Suggesting Features

1. Check existing issues first
2. Use the Feature Request template
3. Explain the use case clearly

### Code Contributions

1. Look for issues labeled `good first issue`
2. Ask to be assigned to an issue
3. Follow the coding standards
4. Write tests for new features
5. Update documentation if needed

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow code style guidelines
   - Write or update tests
   - Update documentation if needed

3. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature description"
   ```

   Commit message format:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation changes
   - `test:` adding tests
   - `refactor:` code refactoring
   - `chore:` maintenance tasks

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Fill out the PR template
   - Link related issues
   - Describe your changes clearly

## Code Style

### Python

- Follow PEP 8
- Use type hints where possible
- Keep functions focused and small
- Write docstrings for public functions

### Example

```python
async def process_message(message: Message) -> str:
    """Process incoming message and generate response.
    
    Args:
        message: The incoming Telegram message
        
    Returns:
        Generated response text
    """
    # Implementation here
    pass
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bot --cov-report=html

# Run specific test file
pytest tests/test_chat.py -v

# Run specific test
pytest tests/test_chat.py::test_function_name -v
```

### Writing Tests

- Test file naming: `test_<module>.py`
- Test function naming: `test_<function_name>_<scenario>`
- Use pytest fixtures for shared setup
- Mock external API calls

## Issue Guidelines

### Good First Issues

Look for issues labeled `good first issue`. These are:
- Well-defined problems
- Suitable for newcomers
- Documented with clear instructions

### Labels

- `bug` - Something is broken
- `enhancement` - New feature request
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements
- `hacktoberfest` - Hacktoberfest eligible

## Questions?

If you have questions:
1. Check existing documentation
2. Search existing issues
3. Open a new issue with the `question` label

Thank you for contributing!
