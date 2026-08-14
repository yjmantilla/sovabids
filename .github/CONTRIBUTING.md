# Contributing to sovabids

Thank you for your interest in contributing to sovabids! This document provides guidelines for contributing to the project.

## Prerequisites

- Python 3.9+
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
   pip install -e ".[dev]"
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

## Reporting Issues

Found a bug or unexpected behavior? Please open an issue on the
[issue tracker](https://github.com/yjmantilla/sovabids/issues). A quick search of existing issues first can
save time in case it is already reported.

To help us reproduce and fix it quickly, include:

- The sovabids version (`pip show sovabids`) and how you installed it (pip, `.[dev]`, or from source).
- Your operating system and Python version.
- Which interface you were using (Python API, CLI, TUI, JSON-RPC, or web GUI).
- A minimal rules file (or the relevant snippet) and the exact command or code you ran.
- The full error message / traceback.
- What you expected to happen versus what actually happened.

## Seeking Support

For usage questions and general "how do I…?" help (as opposed to bug reports), please use
[GitHub Discussions](https://github.com/yjmantilla/sovabids/discussions) so the answers stay searchable for
everyone. You can also email the maintainer at <yjmantilla@gmail.com>.

If you are new to sovabids, the
[Quickstart guide](https://sovabids.readthedocs.io/en/latest/quickstart.html) is the fastest way to get
going.

## Code of Conduct

This project is released with a
[Code of Conduct](https://github.com/yjmantilla/sovabids/blob/main/.github/CODE_OF_CONDUCT.md). By
participating, you are expected to uphold it. Please report unacceptable behavior to <yjmantilla@gmail.com>.
