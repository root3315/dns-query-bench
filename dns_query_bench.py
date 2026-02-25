#!/usr/bin/env python3
"""
dns-query-bench: Lightweight DNS query benchmarking and performance testing tool.

Measures response times, success rates, and percentile latencies
across one or more DNS resolvers for a given set of domain names.
"""

import argparse
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime

try:
    import dns.resolver
    import dns.rdatatype
    import dns.exception
except ImportError:
    sys.exit(
        "Error: dnspython is required.\n"
        "Install it with: pip install dnspython"
    )


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class QueryResult:
    """Holds the outcome of a single DNS query."""
    domain: str
    server: str
    record_type: str
    response_time_ms: float
    success: bool
    answer_count: int = 0
    error: str = ""


@dataclass
class ServerStats:
    """Aggregated statistics for one DNS server."""
    server: str
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    response_times: list = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_queries == 0:
            return 0.0
        return (self.successful_queries / self.total_queries) * 100.0

    @property
    def avg_ms(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def min_ms(self) -> float:
        if not self.response_times:
            return 0.0
        return min(self.response_times)

    @property
    def max_ms(self) -> float:
        if not self.response_times:
            return 0.0
        return max(self.response_times)

    @property
    def median_ms(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.median(self.response_times)

    @property
    def p95_ms(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        idx = min(idx, len(sorted_times) - 1)
        return sorted_times[idx]

    @property
    def stddev_ms(self) -> float:
        if len(self.response_times) < 2:
            return 0.0
        return statistics.stdev(self.response_times)


# ---------------------------------------------------------------------------
# Core benchmarking logic
# ---------------------------------------------------------------------------

def resolve_with_server(
    domain: str,
    server: str,
    record_type: str,
    timeout: float,
) -> QueryResult:
    """
    Perform a single DNS query against *server* and return a QueryResult.
    """
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [server]
    resolver.lifetime = timeout
    resolver.timeout = timeout

    start = time.perf_counter()
    try:
        answers = resolver.resolve(domain, record_type)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return QueryResult(
            domain=domain,
            server=server,
            record_type=record_type,
            response_time_ms=round(elapsed_ms, 3),
            success=True,
            answer_count=len(answers),
        )
    except dns.exception.DNSException as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return QueryResult(
            domain=domain,
            server=server,
            record_type=record_type,
            response_time_ms=round(elapsed_ms, 3),
            success=False,
            error=str(exc),
        )


def run_benchmark(
    domains: list[str],
    servers: list[str],
    record_type: str,
    iterations: int,
    timeout: float,
    verbose: bool,
) -> dict[str, ServerStats]:
    """
    Run the full benchmark matrix: every server x every domain x iterations.
    Returns a dict keyed by server IP with aggregated ServerStats.
    """
    stats_map: dict[str, ServerStats] = {}
    for srv in servers:
        stats_map[srv] = ServerStats(server=srv)

    total_queries = len(servers) * len(domains) * iterations
    query_index = 0

    for iteration in range(1, iterations + 1):
        if iterations > 1:
            print(f"\n--- Iteration {iteration}/{iterations} ---")

        for server in servers:
            for domain in domains:
                query_index += 1
                result = resolve_with_server(domain, server, record_type, timeout)
                st = stats_map[server]
                st.total_queries += 1
                if result.success:
                    st.successful_queries += 1
                    st.response_times.append(result.response_time_ms)
                else:
                    st.failed_queries += 1

                if verbose:
                    status = "OK" if result.success else f"FAIL ({result.error})"
                    print(
                        f"  [{query_index}/{total_queries}] "
                        f"{server:15s} | {domain:30s} | "
                        f"{record_type:6s} | {result.response_time_ms:8.3f} ms | {status}"
                    )

    return stats_map


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_results(stats_map: dict[str, ServerStats], record_type: str) -> None:
    """Print a formatted summary table of benchmark results."""
    separator = "=" * 90
    thin_sep = "-" * 90

    print(f"\n{separator}")
    print(f"  DNS Benchmark Results  |  Record Type: {record_type}")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(separator)

    for server, st in stats_map.items():
        print(f"\n  Server: {server}")
        print(thin_sep)
        print(f"    Total queries    : {st.total_queries}")
        print(f"    Successful       : {st.successful_queries}")
        print(f"    Failed           : {st.failed_queries}")
        print(f"    Success rate     : {st.success_rate:.1f}%")
        print(thin_sep)
        print(f"    Response time (ms):")
        print(f"      Min            : {st.min_ms:.3f}")
        print(f"      Max            : {st.max_ms:.3f}")
        print(f"      Avg            : {st.avg_ms:.3f}")
        print(f"      Median         : {st.median_ms:.3f}")
        print(f"      P95            : {st.p95_ms:.3f}")
        print(f"      Std Dev        : {st.stddev_ms:.3f}")

    # Comparison summary
    if len(stats_map) > 1:
        print(f"\n{separator}")
        print("  Comparison Summary")
        print(separator)
        header = f"  {'Server':<15s} | {'Avg (ms)':>10s} | {'P95 (ms)':>10s} | {'Success %':>10s} | {'StdDev':>10s}"
        print(header)
        print(thin_sep)
        for server, st in stats_map.items():
            print(
                f"  {server:<15s} | {st.avg_ms:>10.3f} | {st.p95_ms:>10.3f} "
                f"| {st.success_rate:>9.1f}% | {st.stddev_ms:>10.3f}"
            )
        print(separator)

        fastest = min(stats_map.values(), key=lambda s: s.avg_ms)
        best_success = max(stats_map.values(), key=lambda s: s.success_rate)
        print(
            f"\n  Fastest average  : {fastest.server} ({fastest.avg_ms:.3f} ms)"
        )
        print(
            f"  Best success rate: {best_success.server} ({best_success.success_rate:.1f}%)"
        )
        print(f"{separator}\n")


# ---------------------------------------------------------------------------
# Domain list helpers
# ---------------------------------------------------------------------------

def load_domains_from_file(path: str) -> list[str]:
    """Read domains from a file, one per line. Skip blanks and comments."""
    domains = []
    with open(path, "r") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            domains.append(stripped)
    if not domains:
        print("Warning: no domains loaded from file.", file=sys.stderr)
    return domains


DEFAULT_DOMAINS = [
    "google.com",
    "github.com",
    "wikipedia.org",
    "amazon.com",
    "cloudflare.com",
]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="DNS query benchmarking and performance testing tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s -d google.com github.com\n"
            "  %(prog)s -d google.com -s 8.8.8.8 1.1.1.1 -i 10\n"
            "  %(prog)s -f domains.txt -t AAAA -v\n"
            "  %(prog)s --quick\n"
        ),
    )
    parser.add_argument(
        "-d", "--domains",
        nargs="+",
        default=[],
        help="One or more domain names to query.",
    )
    parser.add_argument(
        "-f", "--domain-file",
        help="File containing domains (one per line).",
    )
    parser.add_argument(
        "-s", "--servers",
        nargs="+",
        default=["8.8.8.8", "1.1.1.1"],
        help="DNS server IPs (default: 8.8.8.8 1.1.1.1).",
    )
    parser.add_argument(
        "-t", "--record-type",
        default="A",
        choices=["A", "AAAA", "MX", "TXT", "NS", "CNAME", "SOA", "PTR"],
        help="DNS record type (default: A).",
    )
    parser.add_argument(
        "-i", "--iterations",
        type=int,
        default=5,
        help="Number of query iterations per server/domain (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=3.0,
        help="Per-query timeout in seconds (default: 3.0).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print every individual query result.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick preset: 3 iterations against 8.8.8.8 and 1.1.1.1.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.quick:
        args.servers = ["8.8.8.8", "1.1.1.1"]
        args.iterations = 3
        args.timeout = 2.0

    # Build domain list
    domains: list[str] = list(args.domains)
    if args.domain_file:
        domains.extend(load_domains_from_file(args.domain_file))
    if not domains:
        domains = list(DEFAULT_DOMAINS)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_domains: list[str] = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            unique_domains.append(d)
    domains = unique_domains

    # Deduplicate servers
    servers = list(dict.fromkeys(args.servers))

    print("DNS Query Benchmark")
    print(f"  Domains    : {len(domains)} ({', '.join(domains)})")
    print(f"  Servers    : {len(servers)} ({', '.join(servers)})")
    print(f"  Record type: {args.record_type}")
    print(f"  Iterations : {args.iterations}")
    print(f"  Timeout    : {args.timeout}s")
    print(f"  Total queries: {len(servers) * len(domains) * args.iterations}")

    start_time = time.perf_counter()

    stats_map = run_benchmark(
        domains=domains,
        servers=servers,
        record_type=args.record_type,
        iterations=args.iterations,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    elapsed_total = time.perf_counter() - start_time
    print(f"\nBenchmark completed in {elapsed_total:.2f}s")

    print_results(stats_map, args.record_type)


if __name__ == "__main__":
    main()
