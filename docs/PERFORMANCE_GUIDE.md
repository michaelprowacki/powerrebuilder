# PowerRebuilder Performance Guide

## Overview

This guide provides comprehensive performance optimization information for PowerRebuilder, covering benchmarks, configuration, and troubleshooting.

## Performance Architecture

### Key Features
- **Sequential Pipeline**: Extract → Decompile → Parse → Model → Generate
- **Parallel Processing**: Multiple files processed concurrently within each stage
- **Streaming Processing**: Memory-efficient handling of large files
- **Intelligent Caching**: File-based caching with timestamp validation
- **Resource Management**: Configurable limits and throttling

## Performance Benchmarks

### Baseline Performance

| Project Size | Files | Extract | Decompile | Parse | Model | Generate | Total |
|--------------|-------|---------|-----------|-------|-------|----------|-------|
| Small        | <100  | 2s      | 5s        | 3s    | 2s    | 4s       | 16s   |
| Medium       | 1K    | 15s     | 1m        | 30s   | 20s   | 45s      | 2.5m  |
| Large        | 10K   | 2m      | 10m       | 5m    | 3m    | 8m       | 28m   |

*Benchmarks on: Intel i7-9700K, 32GB RAM, NVMe SSD*

### Optimization Impact

| Optimization | Memory Reduction | Speed Improvement | Best For |
|-------------|------------------|-------------------|----------|
| Caching (subsequent runs) | 10% | 60-90% | Iterative development |
| Parallel Processing | 0% | 2-6x | CPU-bound tasks |
| Streaming | 50-80% | 20-40% (large files) | Memory-constrained systems |
| Combined | 40-70% | 3-10x | Production workloads |

## Configuration

### Basic Performance Settings

```bash
# Enable all optimizations
python main.py all input/ output/ --parallel --workers 8 --streaming

# For large projects
python main.py all input/ output/ --parallel --workers 8 --streaming --max-memory 2GB

# For development (faster iteration)
python main.py all input/ output/ --parallel --workers 4
```

### Environment Variables

```bash
# Enable caching
export POWERREBUILDER_CACHE_ENABLED=true
export POWERREBUILDER_CACHE_DIR=~/.powerrebuilder/cache

# Memory limits
export POWERREBUILDER_MAX_MEMORY=2G
export POWERREBUILDER_CHUNK_SIZE=1MB

# Parallel processing
export POWERREBUILDER_MAX_WORKERS=8
```

### Configuration File

Create `config/performance.yaml`:

```yaml
performance:
  # Caching
  cache:
    enabled: true
    ttl: 86400  # 24 hours

  # Parallel processing
  parallel:
    max_workers: 8
    batch_size: 10

  # Memory management
  memory:
    max_heap: 2147483648  # 2GB
    streaming_threshold: 10485760  # 10MB

  # I/O optimization
  io:
    buffer_size: 131072  # 128KB
    async_enabled: true
```

## Performance Optimizations

### 1. Caching System

**When to use**: Development, iterative testing, CI/CD pipelines

```python
# Caching is enabled by default
coordinator = DecompileCoordinator(input_dir, output_dir)
result = coordinator.decompile()
print(f"Cache hit rate: {result.get('cache_hit_rate', 0)}")
```

**Benefits**:
- First run: 0-10% improvement (cache warming)
- Subsequent runs: 60-90% improvement for unchanged files
- Mixed workloads: 20-50% improvement

### 2. Parallel Processing

**When to use**: Multiple files, CPU-bound tasks

```bash
# Automatic optimization based on system resources
python main.py decompile --parallel input/ output/

# Manual worker configuration
python main.py decompile --parallel --workers 6 input/ output/
```

**Guidelines**:
- Workers = CPU cores - 1 for best results
- Reduce workers if memory usage is high
- Use threading for I/O-bound tasks

### 3. Streaming Processing

**When to use**: Large files (>10MB), memory-constrained systems

```bash
# Enable streaming for memory efficiency
python main.py all input/ output/ --streaming --chunk-size 1MB
```

**Benefits**:
- 50-80% memory reduction for large files
- Constant memory usage regardless of file size
- Eliminates out-of-memory errors

## Usage Recommendations

### Project Size Guidelines

#### Small Projects (<100 files)
```bash
# Optimize for speed
python main.py all input/ output/
```

#### Medium Projects (100-1000 files)
```bash
# Balance speed and memory
python main.py all input/ output/ --parallel --workers 4
```

#### Large Projects (1000+ files)
```bash
# Optimize for scalability
python main.py all input/ output/ --parallel --workers 8 --streaming
```

#### Enterprise Projects (10000+ files)
```bash
# Maximum optimization
python main.py all input/ output/ --parallel --workers 16 --streaming --max-memory 4GB
```

## Performance Monitoring

### Real-time Monitoring

```python
from src.common.performance import monitor_performance

with monitor_performance("decompilation") as metrics:
    result = coordinator.decompile()
    metrics.files_processed = result["total_files"]
    metrics.cache_hits = result["cache_hits"]
```

### Performance Metrics

Key metrics to monitor:
- **Throughput**: files/second
- **Memory Usage**: Peak and average MB
- **Cache Hit Rate**: Percentage of cache hits
- **CPU Utilization**: Percentage across cores
- **I/O Wait**: Time spent waiting for disk

### Benchmarking

```bash
# Run comprehensive benchmark
python scripts/performance_benchmark.py input/ --output benchmark_results/

# Quick performance test
python main.py all input/ output/ --benchmark
```

## Troubleshooting

### Common Performance Issues

#### High Memory Usage
**Symptoms**: Process uses excessive memory, system becomes unresponsive

**Solutions**:
```bash
# Enable streaming
python main.py all input/ output/ --streaming

# Reduce parallel workers
python main.py all input/ output/ --workers 2

# Set memory limit
python main.py all input/ output/ --max-memory 1GB
```

#### Slow Processing
**Symptoms**: Processing takes much longer than expected

**Solutions**:
```bash
# Increase parallelism
python main.py all input/ output/ --parallel --workers 8

# Check cache effectiveness
python main.py all input/ output/ --debug-cache

# Enable async I/O
python main.py all input/ output/ --async-io
```

#### Cache Not Working
**Symptoms**: No performance improvement on subsequent runs

**Diagnostics**:
```bash
# Check cache status
ls -la ~/.powerrebuilder/cache

# Enable cache debugging
python main.py all input/ output/ --loglevel DEBUG

# Clear and rebuild cache
rm -rf ~/.powerrebuilder/cache
python main.py all input/ output/
```

### Performance Debugging

```bash
# Enable performance logging
python main.py all input/ output/ --loglevel DEBUG --performance-log

# Generate performance report
python main.py all input/ output/ --performance-report output.html

# Monitor resource usage in real-time
python main.py all input/ output/ --monitor
```

## System Optimization

### Operating System

```bash
# Increase file descriptor limits
ulimit -n 65536

# Optimize kernel parameters for I/O
echo 'vm.dirty_ratio=15' >> /etc/sysctl.conf
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p

# Set CPU governor to performance
cpupower frequency-set -g performance
```

### Hardware Recommendations

#### Minimum Requirements
- CPU: 4 cores, 2.5GHz
- RAM: 8GB
- Storage: 100GB free space
- Disk: SATA SSD

#### Recommended Configuration
- CPU: 8+ cores, 3.0GHz+
- RAM: 16GB+
- Storage: 500GB+ free space
- Disk: NVMe SSD

#### High-Performance Setup
- CPU: 16+ cores, 3.5GHz+
- RAM: 32GB+
- Storage: 1TB+ NVMe SSD
- Network: 10Gbps (for distributed processing)

## Performance Best Practices

### Development Workflow
1. **Start Small**: Test with subset of files first
2. **Use Caching**: Enable caching for iterative development
3. **Monitor Resources**: Watch memory and CPU usage
4. **Profile Bottlenecks**: Use profiling tools to identify issues

### Production Deployment
1. **Benchmark Your Workload**: Test with representative data
2. **Configure Appropriately**: Match settings to your infrastructure
3. **Monitor Performance**: Set up alerts for performance degradation
4. **Plan for Scale**: Consider distributed processing for very large projects

### Optimization Checklist
- ✅ Enable caching for repeated runs
- ✅ Use appropriate worker count for your system
- ✅ Enable streaming for large files or limited memory
- ✅ Set appropriate memory limits
- ✅ Monitor cache hit rates
- ✅ Profile performance bottlenecks
- ✅ Optimize file system and OS settings

## Future Optimizations

### Planned Improvements
- **GPU Acceleration**: For complex P-code analysis
- **Distributed Processing**: Process files across multiple machines
- **Incremental Processing**: Only process changed files
- **Advanced Caching**: Content-based deduplication
- **Machine Learning**: Predictive optimization based on file characteristics

### Contributing Performance Improvements
Performance improvements are welcome! Please:
1. Benchmark before and after changes
2. Include performance test cases
3. Document configuration impacts
4. Consider different workload sizes

## Additional Resources

- [Configuration Reference](../config/README.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Performance Benchmarks](../benchmarks/README.md)
- [System Requirements](./SYSTEM_REQUIREMENTS.md)

---

*Last updated: 2025-01-15*
