# dns-query-bench

Lightweight DNS query benchmarking and performance testing tool.

Measures response times, success rates, and percentile latencies across one or more DNS resolvers for a given set of domain names.

## Features

- Query multiple DNS servers simultaneously
- Support for A, AAAA, MX, TXT, NS, CNAME, SOA, and PTR record types
- Configurable iterations and timeouts
- Statistical output: min, max, avg, median, P95, standard deviation
- Per-query verbose logging
- Domain list file support
- Quick preset mode for fast comparisons

## Requirements

- Python 3.9+
- dnspython

## Installation

```bash
pip install -r requirements.txt
```

Or install the dependency directly:

```bash
pip install dnspython
```

## Usage

### Basic

Benchmark default domains against Google (8.8.8.8) and Cloudflare (1.1.1.1):

```bash
python dns_query_bench.py
```

### Quick mode

Run 3 iterations against the two most popular public resolvers:

```bash
python dns_query_bench.py --quick
```

### Specific domains and servers

```bash
python dns_query_bench.py -d google.com github.com example.com -s 8.8.8.8 9.9.9.9 -i 10
```

### Different record type

```bash
python dns_query_bench.py -d google.com -t AAAA -v
```

### Load domains from file

```bash
python dns_query_bench.py -f domains.txt -s 1.1.1.1
```

The file should contain one domain per line. Lines starting with `#` are treated as comments and blank lines are skipped.

### Custom timeout

```bash
python dns_query_bench.py -d example.com --timeout 5.0
```

## CLI Reference

```
usage: dns_query_bench.py [-h] [-d D [D ...]] [-f DOMAIN_FILE] [-s S [S ...]]
                          [-t {A,AAAA,MX,TXT,NS,CNAME,SOA,PTR}] [-i ITERATIONS]
                          [--timeout TIMEOUT] [-v] [--quick]

DNS query benchmarking and performance testing tool.

options:
  -h, --help            show this help message and exit
  -d, --domains         One or more domain names to query
  -f, --domain-file     File containing domains (one per line)
  -s, --servers         DNS server IPs (default: 8.8.8.8 1.1.1.1)
  -t, --record-type     DNS record type (default: A)
  -i, --iterations      Number of query iterations per server/domain (default: 5)
  --timeout             Per-query timeout in seconds (default: 3.0)
  -v, --verbose         Print every individual query result
  --quick               Quick preset: 3 iterations against 8.8.8.8 and 1.1.1.1
```

## Output

The tool prints:

1. **Configuration summary** at startup
2. **Per-iteration progress** when `--verbose` is used
3. **Per-server statistics** including total queries, success/failure counts, success rate, and response time metrics
4. **Comparison table** ranking all tested servers by average latency, P95 latency, success rate, and standard deviation

## Example Output

```
DNS Query Benchmark
  Domains    : 5 (google.com, github.com, wikipedia.org, amazon.com, cloudflare.com)
  Servers    : 2 (8.8.8.8, 1.1.1.1)
  Record type: A
  Iterations : 5
  Timeout    : 3.0s
  Total queries: 50

Benchmark completed in 2.34s

==========================================================================================
  DNS Benchmark Results  |  Record Type: A
  Generated: 2026-04-15 10:30:00
==========================================================================================

  Server: 8.8.8.8
------------------------------------------------------------------------------------------
    Total queries    : 25
    Successful       : 25
    Failed           : 0
    Success rate     : 100.0%
------------------------------------------------------------------------------------------
    Response time (ms):
      Min            : 1.234
      Max            : 12.567
      Avg            : 3.456
      Median         : 3.120
      P95            : 8.901
      Std Dev        : 2.100

  Server: 1.1.1.1
------------------------------------------------------------------------------------------
    Total queries    : 25
    Successful       : 25
    Failed           : 0
    Success rate     : 100.0%
------------------------------------------------------------------------------------------
    Response time (ms):
      Min            : 0.987
      Max            : 10.234
      Avg            : 2.890
      Median         : 2.650
      P95            : 7.456
      Std Dev        : 1.800

==========================================================================================
  Comparison Summary
==========================================================================================
  Server          |    Avg (ms) |   P95 (ms) |  Success % |     StdDev
------------------------------------------------------------------------------------------
  8.8.8.8         |      3.456 |      8.901 |     100.0% |      2.100
  1.1.1.1         |      2.890 |      7.456 |     100.0% |      1.800
==========================================================================================

  Fastest average  : 1.1.1.1 (2.890 ms)
  Best success rate: 8.8.8.8 (100.0%)
==========================================================================================
```

## License

MIT
