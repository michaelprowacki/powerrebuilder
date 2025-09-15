# PowerBuilder File Inventory Report

## Summary

- **Total PBD/PBL files found**: 1,450 files
- **Locations**:
  - Test fixtures: `/tests/fixtures/pbd_files/`
  - Reference examples: `/reference/pb_code_examples/`
- **PowerBuilder versions represented**: 6.0 through 22.0

## Test Fixture

### Available Test File
- **File**: `/tests/fixtures/pbd_files/dcm_email.pbd`
- **Size**: 38K
- **Status**: Ready for immediate testing

## PowerBuilder Version Distribution

| Version | File Count |
|---------|------------|
| PowerBuilder 22.0/2022 | 170 |
| PowerBuilder 21.0/2021 | 200 |
| PowerBuilder 2019/19.0 | 161 |
| PowerBuilder 2017/17.0 | 137 |
| PowerBuilder 15.0 | 69 |
| PowerBuilder 12.6 | 68 |
| PowerBuilder 12.5 | 68 |
| PowerBuilder 12.1 | 38 |
| PowerBuilder 12.0 | 106 |
| PowerBuilder 11.5 | 72 |
| PowerBuilder 11.2 | 36 |
| PowerBuilder 11.0 | 108 |
| PowerBuilder 10.5 | 44 |
| PowerBuilder 10.0 | 38 |
| PowerBuilder 9.0 | 92 |
| PowerBuilder 8.0 | 90 |
| PowerBuilder 7.0 | 126 |
| PowerBuilder 6.5 | 67 |
| PowerBuilder 6.0 | 64 |

## Recommended Files for Pipeline Testing

### Small Files (Good for Initial Testing)
1. **PowerBuilder 6.0/6.5 Proxy Files**
   - `/reference/pb_code_examples/PowerBuilder 6.0/PWRS/PB6/Examples/distrib/distexam/srvrprox.pbd` (5.6K)
   - `/reference/pb_code_examples/PowerBuilder 6.0/PWRS/PB6/Examples/distrib/distexam/clntprox.pbd` (9K)

2. **Tutorial Files (Various Versions)**
   - `/reference/pb_code_examples/PowerBuilder 8.0/Sybase/PowerBuilder 8.0/Tutorial/tutor_pb.pbl` (65K)
   - `/reference/pb_code_examples/PowerBuilder 11.5/Sybase/PowerBuilder 11.5/Tutorial/Solutions/tutor_pb.pbl` (109K)

3. **Web Services Examples (Modern Structure)**
   - `/reference/pb_code_examples/PowerBuilder 12.0/Sybase/PowerBuilder 12.0/Code Examples/Web Services/proxies.pbd` (104K)
   - `/reference/pb_code_examples/PowerBuilder 12.0/Sybase/PowerBuilder 12.0/Code Examples/Web Services/ws.pbd` (159K)
   - `/reference/pb_code_examples/PowerBuilder 12.0/Sybase/PowerBuilder 12.0/Code Examples/Web Services/tabpages.pbd` (269K)

### Medium Files (Good for Comprehensive Testing)
1. **TransTlk Application Files**
   - `/reference/pb_code_examples/PowerBuilder 10.0/Sybase/PowerBuilder 10.0/TransTlk/DBMAINT.PBD` (632K)
   - `/reference/pb_code_examples/PowerBuilder 10.0/Sybase/PowerBuilder 10.0/TransTlk/ENDUSER.PBD` (686K)
   - `/reference/pb_code_examples/PowerBuilder 10.0/Sybase/PowerBuilder 10.0/TransTlk/PTTDWSRV.PBD` (824K)

### Large Files (Stress Testing)
1. **Example Applications**
   - `/reference/pb_code_examples/PowerBuilder 11.0/Sybase/PowerBuilder 11.0/Code Examples/Example App/pbexamfe.pbl` (2.4M)
   - `/reference/pb_code_examples/PowerBuilder 11.0/Sybase/PowerBuilder 11.0/Code Examples/Example App/pbexammn.pbl` (2.3M)
   - `/reference/pb_code_examples/PowerBuilder 11.0/Sybase/PowerBuilder 11.0/Code Examples/Example App/pbexamd1.pbl` (2.2M)

## Common File Types

### Most Common PBD Files
- TransTlk modules: DBMAINT.PBD, ENDUSER.PBD, PTT.PBD, PTTAPSRV.PBD, etc.
- Web Services: proxies.pbd, tabpages.pbd, ws.pbd
- Benchmarks: pbexbm.pbd

### Most Common PBL Files
- Example App modules: pbexam*.pbl series
- Tutorial files: tutor_pb.pbl, pbtutor.pbl
- Demo applications: pbdemos.pbl
- Web services: proxies.pbl, tabpages.pbl, ws.pbl

## Testing Strategy Recommendations

1. **Start with Test Fixture**
   - Use `/tests/fixtures/pbd_files/dcm_email.pbd` for initial pipeline validation

2. **Version Coverage Testing**
   - Test at least one file from each major version (6.0, 8.0, 10.0, 11.0, 12.0, 15.0, 17.0, 19.0, 21.0, 22.0)

3. **Size-Based Testing**
   - Small files (< 100K): Quick validation
   - Medium files (100K - 1M): Standard testing
   - Large files (> 1M): Performance testing

4. **Application Type Testing**
   - Tutorial applications (simpler structure)
   - TransTlk (complex business application)
   - Web Services (modern features)
   - Example Apps (comprehensive features)

## Pipeline Test Commands

```bash
# Test with the fixture file
python main.py extract tests/fixtures/pbd_files/dcm_email.pbd output/test_fixture

# Test with a small tutorial file
python main.py extract "reference/pb_code_examples/PowerBuilder 8.0/Sybase/PowerBuilder 8.0/Tutorial/tutor_pb.pbl" output/tutorial

# Test with web services example
python main.py extract "reference/pb_code_examples/PowerBuilder 12.0/Sybase/PowerBuilder 12.0/Code Examples/Web Services/ws.pbd" output/webservices

# Full pipeline test
python main.py all "reference/pb_code_examples/PowerBuilder 12.0/Sybase/PowerBuilder 12.0/Code Examples/Web Services" output/full_pipeline
```
