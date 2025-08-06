# Contributing to sovabids

Thank you for your interest in contributing to sovabids! This document provides guidelines for contributing to the project.

## Prerequisites

- Python 3.8+
- Git
- Basic knowledge of EEG data processing and BIDS specification
- Understanding of MNE-Python and MNE-BIDS

## Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/sovabids.git
   cd sovabids
   ```
3. **Create a development environment**:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. **Run tests** to ensure everything works:
   ```bash
   python -m pytest tests/ -v
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `test/improve-coverage`

### Commit Messages

Follow conventional commit format:

```
type(scope): brief description

Longer description if needed

- Bullet points for details
- Reference issues: fixes #123
```

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_bids.py -v

# Run with coverage
python -m pytest tests/ --cov=sovabids --cov-report=html
```

## Documentation


### Building Documentation

```bash
cd docs
make html
```

## Pull Request Process

### Before Submitting

1. **Run tests**: Ensure all tests pass
2. **Update documentation**: Update relevant docs
3. **Add tests**: Include tests for new functionality

### PR Checklist

- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] Commit messages follow conventional format
- [ ] Branch name is descriptive

### PR Description Template

```markdown
## Summary
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Test improvement

## Testing
- [ ] Existing tests pass
- [ ] New tests added

## Documentation
- [ ] Docstrings updated
- [ ] User documentation updated
- [ ] Examples provided

## Related Issues
Fixes #issue_number
```
