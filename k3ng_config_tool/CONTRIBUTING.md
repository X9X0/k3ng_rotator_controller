# Contributing to K3NG Configuration Tool

Thank you for your interest in contributing to the K3NG Configuration Tool! This document provides guidelines and best practices for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Issue Guidelines](#issue-guidelines)

---

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- K3NG rotator controller knowledge (helpful but not required)
- Basic understanding of PyQt6 (for GUI contributions)

### Areas for Contribution

We welcome contributions in:

1. **Bug Fixes**: Fix issues reported in GitHub issues
2. **Features**: Add new functionality (discuss first!)
3. **Documentation**: Improve user guide, code comments, examples
4. **Testing**: Add unit tests, integration tests, hardware tests
5. **Board Support**: Add new Arduino board definitions
6. **Validation Rules**: Improve dependency validation
7. **UI/UX**: Enhance graphical interface
8. **Performance**: Optimize parsing, rendering, serial communication

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub first, then:
git clone https://github.com/YOUR_USERNAME/k3ng_rotator_controller.git
cd k3ng_rotator_controller/k3ng_config_tool
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If it exists
```

### 4. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

---

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use issue template** (if available)
3. **Provide details**:
   - Tool version
   - Operating system
   - Python version
   - Steps to reproduce
   - Expected vs. actual behavior
   - Error messages/stack traces
   - Configuration files (if relevant)

**Example:**
```
Title: Parser fails on rotator_features.h with nested #ifdef

Description:
When parsing rotator_features.h with nested #ifdef blocks, the parser
crashes with AttributeError.

Environment:
- Tool version: 1.0.0
- OS: Ubuntu 22.04
- Python: 3.10.12

Steps to reproduce:
1. Open project with nested #ifdef in rotator_features.h
2. Click "Parse Configuration"
3. See error

Error:
AttributeError: 'NoneType' object has no attribute 'value'

Attached: rotator_features.h (excerpt)
```

### Suggesting Features

1. **Open an issue** with "Feature Request" label
2. **Describe the use case**: Why is this needed?
3. **Propose implementation**: How should it work?
4. **Consider alternatives**: Other approaches?
5. **Wait for discussion**: Maintainers will discuss feasibility

**Example:**
```
Title: Add support for QMC6310 magnetometer

Description:
The QMC6310 is a newer 3-axis magnetometer that's pin-compatible
with the HMC5883L. Adding support would benefit users upgrading hardware.

Use Case:
Users with QMC6310 sensors want to use the calibration wizard.

Proposed Implementation:
1. Add FEATURE_AZ_POSITION_QMC6310 to feature parser
2. Update calibration wizard to support QMC6310 commands
3. Add board compatibility notes

Alternatives:
- Use existing HMC5883L commands (may not work)
- Wait for K3NG firmware to add support first (better approach)
```

---

## Coding Standards

### Python Style

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters max
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Use double quotes for strings
- **Imports**: Alphabetical, grouped (standard, third-party, local)

```python
# Good
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QWidget

from ..parsers.feature_parser import FeatureParser


class ValidationPanel(QWidget):
    """Validation panel widget displaying validation results"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._init_ui()
```

### Type Hints

Use type hints for all function signatures:

```python
def parse_features(file_path: str) -> FeatureConfig:
    """Parse feature configuration from file"""
    ...

def validate(
    active_features: Set[str],
    active_options: Set[str]
) -> ValidationResult:
    """Validate configuration"""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def add_calibration_point(
    self,
    reference_azimuth: float,
    reference_elevation: float
) -> CalibrationPoint:
    """
    Add calibration point with manual reference values

    Args:
        reference_azimuth: True azimuth in degrees (0-360)
        reference_elevation: True elevation in degrees (0-180)

    Returns:
        CalibrationPoint with measured values

    Raises:
        ValueError: If max calibration points exceeded
        RuntimeError: If serial port not connected
    """
    ...
```

### Code Organization

- **One class per file** (with rare exceptions)
- **Constants at top** of file
- **Private methods** prefixed with underscore
- **Logical grouping** of related methods

```python
class FeatureParser:
    """Parser for FEATURE_* defines"""

    # Constants
    FEATURE_PREFIX = "FEATURE_"
    OPTION_PREFIX = "OPTION_"

    def __init__(self, file_path: str):
        """Initialize parser"""
        ...

    # Public methods
    def parse(self) -> FeatureConfig:
        """Parse configuration"""
        ...

    def get_active_features(self) -> Set[str]:
        """Get active features"""
        ...

    # Private methods
    def _parse_define(self, line: str) -> Optional[DefineNode]:
        """Parse single #define line"""
        ...

    def _create_categories(self) -> List[FeatureCategory]:
        """Create feature categories"""
        ...
```

### Error Handling

- **Be specific**: Catch specific exceptions, not `Exception`
- **Provide context**: Include helpful error messages
- **Log errors**: Use logging module (not print)
- **Fail gracefully**: Don't crash on recoverable errors

```python
# Good
try:
    with open(file_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    logging.error(f"Configuration file not found: {file_path}")
    raise ConfigurationError(f"File not found: {file_path}")
except PermissionError:
    logging.error(f"Permission denied reading: {file_path}")
    raise ConfigurationError(f"Permission denied: {file_path}")

# Bad
try:
    content = open(file_path).read()
except:
    print("Error!")
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest testing/tests/motor_tests.py

# With coverage
pytest --cov=. --cov-report=html

# Verbose
pytest -v
```

### Writing Tests

Create tests in `testing/tests/`:

```python
"""
K3NG Configuration Tool - Feature Parser Tests
"""

import pytest
from parsers.feature_parser import FeatureParser, FeatureConfig


class TestFeatureParser:
    """Test feature parser functionality"""

    def test_parse_active_feature(self):
        """Test parsing active feature"""
        parser = FeatureParser("test_data/features.h")
        config = parser.parse()

        assert "FEATURE_YAESU_EMULATION" in config.active_features

    def test_parse_commented_feature(self):
        """Test parsing commented (disabled) feature"""
        parser = FeatureParser("test_data/features.h")
        config = parser.parse()

        assert "FEATURE_EASYCOM_EMULATION" not in config.active_features
        assert "FEATURE_EASYCOM_EMULATION" in config.features

    def test_invalid_file_raises_error(self):
        """Test that invalid file raises appropriate error"""
        with pytest.raises(FileNotFoundError):
            parser = FeatureParser("nonexistent.h")
            parser.parse()
```

### Test Coverage

- **Aim for 80%+ coverage**
- **Test edge cases**: Empty files, invalid input, boundary conditions
- **Test error handling**: Ensure exceptions are raised correctly
- **Mock external dependencies**: Serial ports, file system

---

## Pull Request Process

### Before Submitting

1. **Run tests**: Ensure all tests pass
2. **Check style**: Run linter (`flake8` or `pylint`)
3. **Update documentation**: User guide, docstrings, README
4. **Test manually**: Verify functionality works as expected
5. **Rebase on master**: Ensure clean merge

```bash
# Run tests
pytest

# Check style
flake8 .

# Update from master
git fetch upstream
git rebase upstream/master

# Push to your fork
git push origin feature/your-feature-name
```

### Pull Request Template

```markdown
## Description

Brief description of changes

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Tested manually with K3NG controller

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex/hard-to-understand areas
- [ ] Updated documentation (README, USER_GUIDE, docstrings)
- [ ] No new warnings
- [ ] Added tests that prove fix/feature works
- [ ] New and existing unit tests pass locally

## Related Issues

Fixes #123
Related to #456

## Screenshots (if UI changes)

[Add screenshots here]
```

### Review Process

1. **Automated checks**: Tests, linters run automatically
2. **Code review**: Maintainer reviews code
3. **Feedback**: Address review comments
4. **Approval**: Maintainer approves
5. **Merge**: Squash and merge to master

---

## Issue Guidelines

### Labels

- **bug**: Something isn't working
- **enhancement**: New feature or request
- **documentation**: Documentation improvements
- **good first issue**: Good for newcomers
- **help wanted**: Extra attention needed
- **question**: Further information requested

### Issue Lifecycle

1. **Open**: Issue created
2. **Triage**: Maintainer reviews and labels
3. **Discussion**: Community discusses solution
4. **Implementation**: Someone works on fix
5. **PR Submitted**: Pull request created
6. **Review**: Code review process
7. **Merged**: Fixed in master
8. **Closed**: Issue resolved

---

## Development Tips

### Project Structure

```
k3ng_config_tool/
├── core/           # Keep business logic here
├── parsers/        # Add new parsers for .h files
├── validators/     # Add validation rules
├── generators/     # Add templates for code gen
├── gui/            # Add Qt widgets/dialogs
│   ├── widgets/    # Reusable widgets
│   └── dialogs/    # Modal dialogs
└── testing/        # Add test suites
    ├── tests/      # Hardware tests
    └── calibration/# Calibration modules
```

### Common Tasks

**Adding a new feature:**
1. Add to `parsers/feature_parser.py` FEATURE_CATEGORIES
2. Add validation rules in `data/validation_rules/dependencies.yaml`
3. Update template in `generators/templates/rotator_features.h.j2`
4. Add GUI widget/checkbox if needed
5. Add tests

**Adding a new Arduino board:**
1. Create JSON file in `data/board_definitions/`
2. Add pin capabilities (digital, analog, PWM, interrupts)
3. Test pin validation with new board
4. Add to documentation

**Adding a new test:**
1. Create test class in `testing/tests/`
2. Inherit from `BaseTest` or `SerialTest`
3. Implement `run_test()` method
4. Add to test registry in `testing/test_engine.py`

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# PyQt debugging
export QT_DEBUG_PLUGINS=1  # Linux/Mac
set QT_DEBUG_PLUGINS=1     # Windows

# Serial communication debugging
# Set timeout=None to wait indefinitely
serial.timeout = None
```

---

## Questions?

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bugs and feature requests
- **Email**: k3ng.rotator@gmail.com

---

## Attribution

Contributors will be acknowledged in:
- README.md Contributors section
- Commit history
- Release notes

Thank you for contributing! 🎉

---

**Happy Coding!**

🤖 *Generated with [Claude Code](https://claude.com/claude-code)*
