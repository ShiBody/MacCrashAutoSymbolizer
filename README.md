# MacCrashAutoSymbolizer

A powerful tool for automatically symbolizing macOS crash logs and stack traces. This tool can process various crash log formats (.ips, .diag, .spin, .crash files and raw text) and automatically download the required symbol files to provide detailed, human-readable crash analysis.

## Features

- 🔍 **Auto Symbol Download**: Automatically downloads debug symbols (dSYM files) from remote repositories
- 📊 **Multiple Format Support**: Supports .ips, .diag, .spin, .crash files and raw crash stack text
- 🏗️ **Multi-Architecture**: Supports both x86_64 (Intel) and arm64 (Apple Silicon) architectures
- ⚡ **Async Processing**: High-performance async processing for large crash logs
- 🧹 **Smart Cleanup**: Automatically manages symbol file storage with cleanup of old downloads
- 🌐 **Modern Web Interface**: Professional FastAPI-based web interface with GitHub Primer design
- 🌍 **Multi-Language**: Supports Chinese and English with automatic language switching
- 📱 **Responsive Design**: Mobile-friendly interface that works on all devices
- 📦 **Easy Installation**: Available as a Python package via pip
- 🐳 **Docker Support**: Containerized deployment option

## Installation

### Install from PyPI (Recommended)

```bash
pip install maccrashautosymbolizer
```

### Install from Source

```bash
git clone https://github.com/ShiBody/MacCrashAutoSymbolizer.git
cd MacCrashAutoSymbolizer
pip install -e .
```

### Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## Quick Start

### Command Line Usage

```python
from MacAutoSymbolizer import Symbolizer, Arch

# Create symbolizer instance
symbolizer = Symbolizer()

# Symbolize crash stack (string content)
crash_stack = """
46  imageName                           0x0000000104ce3ed0 imageName + 1261264
47  imageName                           0x0000000104cdfa78 imageName + 1243768
48  imageName                           0x0000000104ce3f74 imageName + 1261428

Binary Images:
       0x104bb0000 -        0x104e0ffff com.cisco.webex.imageName (1.0) <47466b6a-5ff7-3ae0-bf60-30a0b1345e13> /Applications/Webex.app/Contents/PlugIns/CiscoSparkPlugin.bundle/Contents/Frameworks/imageName.framework/Versions/A/imageName
"""

result = symbolizer.symbolize(crash_stack, "45.10.0.32891", Arch.arm)

# Print symbolized results
for block in result:
    print(f'\n{"-" * 50}\n')
    for line in block:
        print(line)
```

### Web Interface Usage

#### Start the Web Server

```bash
# Navigate to webPage directory
cd webPage

# Install web dependencies (if not already installed)
pip install fastapi uvicorn jinja2 python-multipart

# Start the web server
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Then open `http://localhost:8000` in your browser.

#### Web Interface Features

- **🎨 GitHub-Style Interface**: Modern, professional design with GitHub Primer components
- **🌍 Language Support**: Toggle between Chinese and English with one click
- **📝 Dual Input Methods**: 
  - Direct text input for crash stack content
  - File upload for .ips, .diag, .spin files
- **⚙️ Configuration Options**:
  - Version number input with validation
  - Architecture selection (ARM64/x86_64)
  - NDI mode toggle
- **📊 Real-time Processing**: Live log output and progress tracking
- **📱 Mobile Responsive**: Works perfectly on desktop, tablet, and mobile devices

### File Processing

```python
from MacAutoSymbolizer import Symbolizer, Arch

symbolizer = Symbolizer()

# Process .ips file
result = symbolizer.symbolize('crash_files/example.ips', "45.10.0.32891", Arch.arm)

# Process .diag file  
result = symbolizer.symbolize('crash_files/example.diag', "45.10.0.32870", Arch.arm)

# Process .spin file
result = symbolizer.symbolize('crash_files/example.spin', "45.10.0.32891", Arch.osx)

# Process .crash file
result = symbolizer.symbolize('crash_files/example.crash', "45.10.0.32891", Arch.arm)
```

## API Reference

### Symbolizer Class

The main class for crash log symbolization.

```python
class Symbolizer:
    def __init__(self, result_processor: Callable | None = None):
        """
        Initialize the symbolizer.
        
        Args:
            result_processor: Optional custom result processor function
        """
```

#### Methods

##### `symbolize(content_or_path, version, arch, isBackup=False)`

Symbolize crash logs with automatic symbol download.

**Parameters:**
- `content_or_path` (str): Crash stack content (string) or file path to crash log
- `version` (str): App version (e.g., "45.10.0.32891")  
- `arch` (Arch): Target architecture - `Arch.arm` (arm64) or `Arch.osx` (x86_64)
- `isBackup` (bool, optional): Use backup symbol repository if primary fails

**Returns:**
- `List[List[ScannedLine]]`: List of symbolized crash thread blocks

##### `download_symbols(version, arch, isBackup=False)`

Download symbol files for a specific version and architecture.

**Parameters:**
- `version` (str): App version to download symbols for
- `arch` (Arch): Target architecture
- `isBackup` (bool, optional): Use backup repository

**Returns:**
- `Tuple[bool, str | None]`: Success status and download directory path

### Arch Enum

Defines supported architectures:

```python
class Arch(str, Enum):
    osx = 'x86_64'    # Intel Macs
    arm = 'arm64'     # Apple Silicon Macs
```

## Configuration

### Environment Variables

Set these environment variables for authenticated symbol downloads:

```bash
export DOWNLOAD_USER="your_username"
export DOWNLOAD_PASSWORD="your_access_token"
```

### Config File

Create a `config.ini` file in your project root:

```ini
[symbols]
base_url = https://your-symbol-server.com
timeout = 600
max_retries = 5

[storage]
cleanup_old_downloads = true
max_folders = 10

[web]
host = 0.0.0.0
port = 8000
debug = false
```

## Advanced Usage

### Custom Result Processing

```python
def custom_processor(result):
    # Custom processing logic
    return processed_result

symbolizer = Symbolizer(result_processor=custom_processor)
```

### Batch Processing

```python
import os
from MacAutoSymbolizer import Symbolizer, Arch

symbolizer = Symbolizer()
crash_files_dir = "crash_logs"

for filename in os.listdir(crash_files_dir):
    if filename.endswith(('.ips', '.diag', '.spin', '.crash')):
        filepath = os.path.join(crash_files_dir, filename)
        print(f"Processing {filename}...")
        
        result = symbolizer.symbolize(filepath, "45.10.0.32891", Arch.arm)
        
        # Save symbolized output
        output_file = f"symbolized_{filename}.txt"
        with open(output_file, 'w') as f:
            for block in result:
                for line in block:
                    f.write(str(line) + '\n')
                f.write('\n' + '-'*50 + '\n\n')
```

### Web API Integration

The web interface provides RESTful APIs for integration:

```python
import requests

# Upload file for symbolization
files = {'crash_file': open('crash.ips', 'rb')}
data = {
    'version': '45.10.0.32891',
    'arch': 'arm64',
    'isNDI': False
}

response = requests.post('http://localhost:8000/symbolize', files=files, data=data)
result = response.json()

if result['success']:
    print("Symbolized output:", result['output'])
    print("Processing logs:", result['logs'])
else:
    print("Error:", result['error'])
```

## Project Structure

```
MacCrashAutoSymbolizer/
├── MacAutoSymbolizer/          # Main package
│   ├── src/                    # Core modules
│   │   ├── symbolizer.py       # Main symbolizer class
│   │   ├── scanner.py          # Crash log parsing
│   │   ├── advanced_downloader.py  # Symbol downloading
│   │   ├── utilities.py        # Helper functions
│   │   ├── ips_converter.py    # IPS file processing
│   │   ├── diag_converter.py   # DIAG file processing
│   │   └── subprocess_cmd.py   # System command interface
│   ├── tests/                  # Unit tests
│   └── tools/                  # Binary tools (atos, plcrashutil)
├── webPage/                    # Web interface
│   ├── app.py                  # FastAPI application
│   ├── templates/              # HTML templates
│   ├── static/                 # CSS, JS assets
│   └── requirements.txt        # Web dependencies
├── examples/                   # Usage examples
│   ├── crash_files/            # Sample crash files
│   └── *.py                    # Example scripts
├── download_symbols/           # Downloaded symbol files
├── dist/                       # Built packages
├── upload_release.sh          # Release script
└── docker-compose.yml         # Docker configuration
```

## Examples

The `examples/` directory contains various usage examples:

- `example.py` - Basic symbolization example
- `advanced_downloader_example.py` - Advanced download configuration
- `ips_convert_example.py` - IPS file processing
- `ips_converter_new_example.py` - Enhanced IPS processing
- `scanner_example.py` - Custom scanning logic

### Sample Crash Files

The project includes sample crash files for testing:
- `example.ips` - iOS/macOS crash report
- `example.diag` - Diagnostic file
- `example.spin` - Spin dump file
- `Webex-*.ips` - Real-world Webex crash examples

## Development

### Building from Source

```bash
# Clone the repository
git clone https://github.com/ShiBody/MacCrashAutoSymbolizer.git
cd MacCrashAutoSymbolizer

# Install in development mode
pip install -e .

# Run tests
python -m pytest MacAutoSymbolizer/tests/

# Run web interface in development mode
cd webPage
uvicorn app:app --reload
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test modules
python -m pytest MacAutoSymbolizer/tests/test_downloader.py

# Run with coverage
python -m pytest --cov=MacAutoSymbolizer
```

### Docker Development

```bash
# Build Docker image
docker build -t maccrash-symbolizer .

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f
```

## Release Process

This project includes an automated release script for publishing to GitHub releases.

### Prerequisites

1. **Install GitHub CLI**:
   ```bash
   brew install gh
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

### Creating a Release

1. **Build the package**:
   ```bash
   python -m build
   ```

2. **Run the release script**:
   ```bash
   ./upload_release.sh
   ```

The script will:
- Auto-detect version from built packages (currently v3.0.0)
- Create a new GitHub release (or upload to existing)
- Upload wheel and source distribution files
- Provide release URL

### Manual Release Options

You can also specify version manually:
```bash
./upload_release.sh --version 3.0.1
```

Or view help:
```bash
./upload_release.sh --help
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

### Development Guidelines

- Follow Python PEP 8 style guidelines
- Add tests for new functionality
- Update documentation for API changes
- Ensure web interface is responsive and accessible
- Test with both x86_64 and arm64 architectures

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📋 **Issues**: [GitHub Issues](https://github.com/ShiBody/MacCrashAutoSymbolizer/issues)
- 📖 **Documentation**: Check the `examples/` directory for more usage examples
- 💬 **Discussions**: [GitHub Discussions](https://github.com/ShiBody/MacCrashAutoSymbolizer/discussions)
- 🌐 **Web Demo**: Access the web interface at `http://localhost:8000` after installation

## Changelog

### v3.0.0
- ✨ Complete rewrite with async processing
- 🌐 Added modern FastAPI web interface with GitHub Primer design
- 🌍 Multi-language support (Chinese/English)
- 📱 Responsive design for all devices
- ⚡ Improved symbol download performance with chunked downloads
- 🔧 Enhanced multi-format support (.ips, .diag, .spin)
- 🐳 Docker containerization support
- 🧹 Automated cleanup of old symbol downloads
- 📊 Real-time processing logs and progress tracking
- 🚀 Automated release process with GitHub integration
