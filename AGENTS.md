# AGENTS.md - Virtual Identity Generator CLI

## Project Overview
A Python CLI tool for generating virtual identity information using the Faker library.

## Core Stack
- Python 3.8+
- Faker library for data generation
- Click library for CLI interface
- Pydantic for data validation

## Project Structure
```
.
├── src/
│   └── identity_gen/       # Main package
│       ├── __init__.py
│       ├── cli.py          # CLI entry point
│       ├── generator.py    # Identity generation logic
│       ├── models.py       # Data models (Pydantic)
│       └── formatters.py   # Output format handlers
├── tests/                  # Test suite
├── AGENTS.md               # This file
├── README.md               # User documentation
├── pyproject.toml          # Project configuration
└── requirements.txt        # Dependencies
```

## Agent Behavior Guidelines

### Code Conventions
- Use type hints throughout
- Follow PEP 8 style guide
- Maximum line length: 100 characters
- Use docstrings for all public functions/classes
- Prefer composition over inheritance

### CLI Design Patterns
- Use Click decorators for commands
- Support both interactive and non-interactive modes
- Provide meaningful error messages
- Support multiple output formats (JSON, CSV, table)
- Include --help descriptions for all commands

### Testing Requirements
- Write unit tests for generators
- Test CLI commands using Click's test runner
- Mock Faker to ensure reproducible tests
- Maintain >80% code coverage

### Error Handling
- Never suppress exceptions without logging
- Use custom exception classes for domain errors
- Provide user-friendly error messages
- Exit with appropriate status codes

### Anti-Patterns
- NEVER use bare except clauses
- NEVER print directly; use logging or Click's echo
- NEVER hardcode locale strings; use Faker's localization
- NEVER expose sensitive data in error messages
