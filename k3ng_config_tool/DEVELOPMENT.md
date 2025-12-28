# K3NG Configuration Tool - Development Guide

## Development Setup

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/X9X0/k3ng_rotator_controller.git
   cd k3ng_rotator_controller/k3ng_config_tool
   ```

2. **Run the launcher (recommended):**
   ```bash
   ./launch.sh          # Linux/macOS
   launch.bat           # Windows
   ```

   The launcher automatically:
   - Clears Python bytecode cache
   - Sets up virtual environment
   - Installs dependencies
   - Creates global commands

### Manual Development Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Avoiding Bytecode Cache Issues

### The Problem

Python caches compiled bytecode in `__pycache__/` directories and `.pyc` files. When you:
- Switch git branches
- Pull changes from remote
- Edit files in a different editor
- Rename/move files

...the cache can become stale, causing import errors like:
```
ImportError: cannot import name 'OldClassName' from 'module'
```

### Solution 1: Use the Launcher (Recommended)

The launcher **automatically clears cache** every time you run it:
```bash
./launch.sh
```

### Solution 2: Manual Cache Clearing

**Quick cleanup script:**
```bash
./clean_cache.sh    # Linux/macOS
clean_cache.bat     # Windows
```

**Manual cleanup:**
```bash
# Remove all cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Solution 3: Disable Bytecode Cache (Development Only)

**Option A: Environment Variable**
```bash
# Linux/macOS - Add to ~/.bashrc or ~/.zshrc
export PYTHONDONTWRITEBYTECODE=1

# Windows - Set permanently
setx PYTHONDONTWRITEBYTECODE 1
```

**Option B: Python Flag**
```bash
# Run Python with -B flag
python3 -B gui_main.py
python3 -B -m pytest
```

**Option C: Modify IDE Settings**

**VSCode** - Add to `.vscode/settings.json`:
```json
{
    "python.envFile": "${workspaceFolder}/.env"
}
```

Create `.env` file:
```
PYTHONDONTWRITEBYTECODE=1
```

**PyCharm** - Settings → Build, Execution, Deployment → Python Debugger → Gevent compatible

### When to Use Each Approach

| Situation | Recommended Approach |
|-----------|---------------------|
| **Starting work** | Run `./launch.sh` (auto-clears cache) |
| **Switching branches** | Run `./clean_cache.sh` |
| **After git pull** | Run `./clean_cache.sh` |
| **Active development** | Set `PYTHONDONTWRITEBYTECODE=1` |
| **Production/Testing** | Allow cache (performance) |
| **CI/CD Pipeline** | Fresh checkout (no cache) |

## Best Practices

### 1. Always Clear Cache When:
- ✅ Switching git branches
- ✅ After pulling remote changes
- ✅ Before running tests
- ✅ When encountering import errors
- ✅ After renaming/moving files

### 2. Use Virtual Environments
```bash
# Always activate venv before working
source venv/bin/activate
```

### 3. Git Workflow
```bash
# Before switching branches
./clean_cache.sh
git checkout feature-branch

# After pulling
git pull origin master
./clean_cache.sh
```

### 4. Running Tests
```bash
# Clear cache before testing
./clean_cache.sh
pytest

# Or use PYTHONDONTWRITEBYTECODE
PYTHONDONTWRITEBYTECODE=1 pytest
```

### 5. IDE Configuration

Add `.env` file (gitignored):
```bash
# Development environment variables
PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=.
```

## Common Issues & Solutions

### Issue: Import Error After Git Pull

**Symptom:**
```
ImportError: cannot import name 'ArduinoBoard' from 'boards.board_database'
```

**Solution:**
```bash
./clean_cache.sh
# or
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Issue: Changes Not Reflected

**Symptom:** Code changes don't seem to take effect

**Solution:**
```bash
# Clear cache and restart
./clean_cache.sh
python3 gui_main.py
```

### Issue: Module Not Found

**Symptom:**
```
ModuleNotFoundError: No module named 'PyQt6'
```

**Solution:**
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Testing

### Unit Tests
```bash
# With cache clearing
./clean_cache.sh && pytest

# Without cache (development)
PYTHONDONTWRITEBYTECODE=1 pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Integration Tests
```bash
# Test GUI without launching
python3 -c "from gui.main_window import MainWindow; print('✓ Import OK')"
```

## Contributing Workflow

1. **Create feature branch:**
   ```bash
   ./clean_cache.sh
   git checkout -b feature/my-feature
   ```

2. **Develop with cache disabled:**
   ```bash
   export PYTHONDONTWRITEBYTECODE=1
   # or
   python3 -B gui_main.py
   ```

3. **Before committing:**
   ```bash
   ./clean_cache.sh
   pytest
   git add .
   git commit -m "..."
   ```

4. **Before switching back:**
   ```bash
   git checkout master
   ./clean_cache.sh
   git pull origin master
   ```

## Performance Considerations

### Cache Enabled (Default)
- ✅ Faster startup times
- ✅ Reduced CPU usage
- ❌ Potential stale import issues

### Cache Disabled (Development)
- ✅ Always fresh imports
- ✅ No stale cache issues
- ❌ Slightly slower startup
- ❌ More disk I/O

**Recommendation:** Disable cache during active development, enable for production/testing.

## Troubleshooting

### Cache Won't Clear

**Windows:**
```cmd
# Close all Python processes
taskkill /F /IM python.exe

# Then run cleanup
clean_cache.bat
```

**Linux/macOS:**
```bash
# Kill Python processes
pkill -9 python3

# Then run cleanup
./clean_cache.sh
```

### Permissions Error

**Linux/macOS:**
```bash
# Make cleanup script executable
chmod +x clean_cache.sh

# Remove cache with sudo if needed
sudo find . -type d -name "__pycache__" -exec rm -rf {} +
```

## Additional Resources

- [Python Documentation - Bytecode Cache](https://docs.python.org/3/tutorial/modules.html#compiled-python-files)
- [PEP 3147 - PYC Repository Directories](https://peps.python.org/pep-3147/)
- [K3NG Project Wiki](https://github.com/k3ng/k3ng_rotator_controller/wiki)

---

**Questions?** Open an issue on GitHub: https://github.com/X9X0/k3ng_rotator_controller/issues
