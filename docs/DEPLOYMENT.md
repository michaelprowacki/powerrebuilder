# Deployment Guide

## Overview
This guide covers deployment and usage of the PowerBuilder decompiler.

## Prerequisites
- Python 3.11 or higher
- UV package manager
- PowerBuilder PBD/PBL files to decompile

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-repo/powerbuilder-decompiler.git
   cd powerbuilder-decompiler
   ```

2. **Set up environment**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **Install dependencies**
   ```bash
   uv pip install -r requirements.txt
   ```

## Configuration

### Data Directory Setup
The decompiler uses a structured data directory:
```
data/
├── input/
│   └── pbd_files/      # Place your PBD/PBL files here
├── output/
│   └── current/        # Decompiled output will appear here
└── test_data/
    └── fixtures/       # Test files
```

### Environment Variables
- `PB_PARSER_ERROR_RECOVERY`: Enable error recovery (default: true)
- `PB_PARSER_TYPE`: Parser type - "earley" or "lalr" (default: earley)
- `PB_PARSER_MAX_ERRORS`: Maximum errors to collect (default: 500)

## Usage

### Basic Usage
```bash
python main.py data/input/pbd_files/your_file.pbd
```

### Batch Processing
```bash
python main.py data/input/pbd_files/
```

### With Options
```bash
# Enable debug output
python main.py --debug data/input/pbd_files/your_file.pbd

# Specify output directory
python main.py --output data/output/custom/ data/input/pbd_files/

# Skip specific stages
python main.py --skip-parse data/input/pbd_files/
```

## Output Structure
Decompiled files are organized as follows:
```
data/output/current/
├── extracted/          # Raw extracted objects
├── decompiled/         # Decompiled source code
├── parsed/             # AST representations
├── model/              # Model layer objects
└── logs/               # Processing logs
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're in the virtual environment
   - Run `uv pip install -e .` to install in development mode

2. **Parser Errors**
   - Try switching parser type: `export PB_PARSER_TYPE=lalr`
   - Enable error recovery: `export PB_PARSER_ERROR_RECOVERY=true`

3. **Memory Issues**
   - Process files individually instead of batch
   - Increase Python heap size if needed

### Debug Mode
Enable detailed logging:
```bash
python main.py --log-level DEBUG data/input/pbd_files/
```

## Performance Tuning

### Parallel Processing
The decompiler supports parallel processing:
```bash
python main.py --workers 4 data/input/pbd_files/
```

### Memory Optimization
For large files:
```bash
python main.py --low-memory data/input/pbd_files/large_file.pbd
```

## Docker Deployment

### Build Image
```bash
docker build -t pb-decompiler .
```

### Run Container
```bash
docker run -v $(pwd)/data:/app/data pb-decompiler data/input/pbd_files/
```

## API Server

### Start Server
```bash
uvicorn api.main:app --reload
```

### API Endpoints
- `POST /decompile` - Upload and decompile a file
- `GET /status/{job_id}` - Check decompilation status
- `GET /download/{job_id}` - Download results

See [API Guide](API.md) for detailed API documentation.
