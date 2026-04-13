"""
Comprehensive Concurrency and Stress Test Suite for FYJC Semantic Support Bot.

This module provides various load testing scenarios to identify:
- Maximum concurrent users before degradation
- Breaking points and failure modes
- Sustained load performance
- Memory and resource leaks

Usage:
    python tests/load_test_concurrency.py [concurrent_users]
    python tests/load_test_concurrency.py --stress
    python tests/load_test_concurrency.py --breaking-point
    python tests/load_test_concurrency.py --sustained
"""

import asyncio
import httpx
import time
import json
import sys
import argparse
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any
import statistics


class LoadTester:
    """Comprehensive load testing for the bot API."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/chat"
        self.results = []
        self.queries = [
            "What is FYJC?",
            "FYJC admission kaise hota hai?",
            "Documents required for FYJC admission?",
            "How to apply online?",
            "What are the quota types?",
            "Minimum marks required?",
            "How to print allotment letter?",
            "Can I cancel admission?",
            "Is online application mandatory?",
            "What is CAP round?",
        ]

    async def send_request(
        self,
        client: httpx.AsyncClient,
        user_id: int,
        query: str = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Send a single chat request and measure performance."""
        if query is None:
            query = self.queries[user_id % len(self.queries)]

        payload = {
            "message": query,
            "history": []
        }

        start = time.time()
        try:
            response = await client.post(
                self.api_url,
                json=payload,
                timeout=timeout
            )
            duration = time.time() - start

            if response.status_code == 200:
                data = response.json()
                return {
                    "user_id": user_id,
                    "success": True,
                    "duration": duration,
                    "status_code": response.status_code,
                    "query": query,
                    "response_length": len(data.get("answer", "")),
                    "detected_lang": data.get("detected_lang", "unknown"),
                    "match_score": data.get("match_score", 0)
                }
            else:
                logger.warning(f"User {user_id} failed with status {response.status_code}")
                return {
                    "user_id": user_id,
                    "success": False,
                    "duration": duration,
                    "status_code": response.status_code,
                    "query": query,
                    "error": f"HTTP {response.status_code}"
                }
        except httpx.TimeoutException as e:
            duration = time.time() - start
            logger.error(f"User {user_id} timeout after {duration:.2f}s")
            return {
                "user_id": user_id,
                "success": False,
                "duration": duration,
                "status_code": 0,
                "query": query,
                "error": "Timeout"
            }
        except Exception as e:
            duration = time.time() - start
            logger.error(f"User {user_id} failed with error: {e}")
            return {
                "user_id": user_id,
                "success": False,
                "duration": duration,
                "status_code": 0,
                "query": query,
                "error": str(e)
            }

    async def run_concurrent_test(
        self,
        concurrent_users: int,
        timeout: float = 30.0,
        test_name: str = ""
    ) -> Dict[str, Any]:
        """Run a concurrent load test with specified number of users."""
        logger.info(f"Starting {test_name} with {concurrent_users} concurrent users...")

        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = [
                self.send_request(client, i, timeout=timeout)
                for i in range(concurrent_users)
            ]

            start_all = time.time()
            results = await asyncio.gather(*tasks)
            total_duration = time.time() - start_all

            # Analyze results
            successful = [r for r in results if r["success"]]
            failed = [r for r in results if not r["success"]]
            durations = [r["duration"] for r in successful]

            # Calculate statistics
            stats = {
                "test_name": test_name,
                "timestamp": datetime.now().isoformat(),
                "concurrent_users": concurrent_users,
                "total_requests": concurrent_users,
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "success_rate": len(successful) / concurrent_users * 100,
                "total_duration": total_duration,
                "throughput": len(successful) / total_duration if total_duration > 0 else 0,
            }

            if durations:
                stats["avg_latency"] = statistics.mean(durations)
                stats["median_latency"] = statistics.median(durations)
                stats["min_latency"] = min(durations)
                stats["max_latency"] = max(durations)
                stats["std_dev_latency"] = statistics.stdev(durations) if len(durations) > 1 else 0
                stats["p95_latency"] = sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else max(durations)
                stats["p99_latency"] = sorted(durations)[int(len(durations) * 0.99)] if len(durations) >= 100 else max(durations)
            else:
                stats["avg_latency"] = stats["median_latency"] = stats["min_latency"] = 0
                stats["max_latency"] = total_duration
                stats["std_dev_latency"] = 0
                stats["p95_latency"] = stats["p99_latency"] = total_duration

            # Error analysis
            error_types = {}
            for r in failed:
                error = r.get("error", f"HTTP {r.get('status_code', 'unknown')}")
                error_types[error] = error_types.get(error, 0) + 1
            stats["error_breakdown"] = error_types

            # Language distribution
            lang_dist = {}
            for r in successful:
                lang = r.get("detected_lang", "unknown")
                lang_dist[lang] = lang_dist.get(lang, 0) + 1
            stats["language_distribution"] = lang_dist

            self.results.append(stats)
            return stats

    async def run_sustained_load_test(
        self,
        users_per_round: int = 10,
        rounds: int = 6,
        delay_between_rounds: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Run sustained load test over time."""
        logger.info(f"Starting sustained load test: {users_per_round} users x {rounds} rounds")

        round_results = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for round_num in range(rounds):
                logger.info(f"Round {round_num + 1}/{rounds}...")

                tasks = [
                    self.send_request(client, round_num * users_per_round + i)
                    for i in range(users_per_round)
                ]

                start = time.time()
                results = await asyncio.gather(*tasks)
                duration = time.time() - start

                successes = sum(1 for r in results if r["success"])
                round_stats = {
                    "round": round_num + 1,
                    "successes": successes,
                    "failures": users_per_round - successes,
                    "duration": duration,
                    "throughput": successes / duration if duration > 0 else 0
                }
                round_results.append(round_stats)

                print(f"  Round {round_num + 1}/{rounds}: {successes}/{users_per_round} successful ({duration:.2f}s)")

                if round_num < rounds - 1:
                    await asyncio.sleep(delay_between_rounds)

        # Aggregate results
        total_successes = sum(r["successes"] for r in round_results)
        total_requests = users_per_round * rounds

        return {
            "test_type": "sustained_load",
            "timestamp": datetime.now().isoformat(),
            "users_per_round": users_per_round,
            "rounds": rounds,
            "total_requests": total_requests,
            "total_successes": total_successes,
            "total_failures": total_requests - total_successes,
            "overall_success_rate": total_successes / total_requests * 100,
            "round_details": round_results
        }

    async def run_ramp_up_test(
        self,
        start_users: int = 10,
        max_users: int = 200,
        step: int = 10
    ) -> List[Dict[str, Any]]:
        """Gradually increase load to find breaking point."""
        logger.info(f"Starting ramp-up test: {start_users} -> {max_users} (step: {step})")

        ramp_results = []

        for users in range(start_users, max_users + 1, step):
            stats = await self.run_concurrent_test(
                concurrent_users=users,
                timeout=30.0,
                test_name=f"Ramp-up {users} users"
            )

            ramp_results.append(stats)

            print(f"\nUsers: {users:3d} | Success: {stats['successful_requests']:3d}/{stats['total_requests']} | "
                  f"Throughput: {stats['throughput']:6.2f} req/s | Avg: {stats['avg_latency']:.2f}s")

            # Stop if success rate drops below 50%
            if stats["success_rate"] < 50:
                print(f"\n⚠️  Breaking point reached at {users} concurrent users!")
                break

        return ramp_results

    def print_results(self, stats: Dict[str, Any]):
        """Pretty print test results."""
        print("\n" + "="*70)
        print(f"  {stats.get('test_name', 'LOAD TEST RESULTS').upper()}")
        print("="*70)
        print(f"  Timestamp:        {stats.get('timestamp', 'N/A')}")
        print(f"  Concurrent Users: {stats.get('concurrent_users', 'N/A')}")
        print("-"*70)
        print(f"  Total Requests:   {stats.get('total_requests', 0)}")
        print(f"  Successful:       {stats.get('successful_requests', 0)}")
        print(f"  Failed:           {stats.get('failed_requests', 0)}")
        print(f"  Success Rate:     {stats.get('success_rate', 0):.1f}%")
        print("-"*70)
        print(f"  Total Duration:   {stats.get('total_duration', 0):.2f}s")
        print(f"  Throughput:       {stats.get('throughput', 0):.2f} req/s")
        print("-"*70)
        print(f"  Avg Latency:      {stats.get('avg_latency', 0):.2f}s")
        print(f"  Median Latency:   {stats.get('median_latency', 0):.2f}s")
        print(f"  Min Latency:      {stats.get('min_latency', 0):.2f}s")
        print(f"  Max Latency:      {stats.get('max_latency', 0):.2f}s")
        print(f"  Std Dev:          {stats.get('std_dev_latency', 0):.2f}s")
        print(f"  P95 Latency:      {stats.get('p95_latency', 0):.2f}s")
        print(f"  P99 Latency:      {stats.get('p99_latency', 0):.2f}s")
        print("-"*70)

        if stats.get("error_breakdown"):
            print("  Error Breakdown:")
            for error, count in stats["error_breakdown"].items():
                print(f"    - {error}: {count}")
            print("-"*70)

        if stats.get("language_distribution"):
            print("  Language Distribution:")
            for lang, count in stats["language_distribution"].items():
                print(f"    - {lang}: {count}")
            print("-"*70)

        print("="*70 + "\n")

    def save_results(self, filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Results saved to {filename}")
        return filename


async def main():
    """Main entry point for load testing."""
    parser = argparse.ArgumentParser(description="FYJC Bot Load Tester")
    parser.add_argument("users", nargs="?", type=int, default=50,
                        help="Number of concurrent users (default: 50)")
    parser.add_argument("--stress", action="store_true",
                        help="Run stress test with 100-200 users")
    parser.add_argument("--breaking-point", action="store_true",
                        help="Find breaking point via ramp-up test")
    parser.add_argument("--sustained", action="store_true",
                        help="Run sustained load test")
    parser.add_argument("--url", type=str, default="http://localhost:8001",
                        help="Base URL of the server")
    parser.add_argument("--save", action="store_true",
                        help="Save results to JSON file")

    args = parser.parse_args()

    tester = LoadTester(base_url=args.url)

    try:
        if args.stress:
            # Run stress tests at different levels
            print("\n🔥 RUNNING STRESS TEST SUITE 🔥\n")

            for users in [50, 100, 150, 200]:
                stats = await tester.run_concurrent_test(
                    concurrent_users=users,
                    timeout=60.0,
                    test_name=f"Stress Test - {users} users"
                )
                tester.print_results(stats)

                if stats["success_rate"] < 50:
                    print(f"\n⚠️  System overloaded at {users} users - stopping stress tests")
                    break

                await asyncio.sleep(5)  # Cooldown between tests

        elif args.breaking_point:
            # Find breaking point
            print("\n🔍 FINDING BREAKING POINT 🔍\n")
            ramp_results = await tester.run_ramp_up_test(
                start_users=10,
                max_users=300,
                step=20
            )

            # Summary
            print("\n" + "="*70)
            print("  BREAKING POINT ANALYSIS SUMMARY")
            print("="*70)

            for stats in ramp_results:
                status = "✓" if stats["success_rate"] >= 90 else "⚠" if stats["success_rate"] >= 50 else "✗"
                print(f"  {status} {stats['concurrent_users']:3d} users: "
                      f"{stats['successful_requests']:3d}/{stats['total_requests']} "
                      f"({stats['success_rate']:5.1f}%) - {stats['throughput']:6.2f} req/s")

            print("="*70)

        elif args.sustained:
            # Sustained load test
            print("\n⏱️  RUNNING SUSTAINED LOAD TEST ⏱️\n")
            sustained_results = await tester.run_sustained_load_test(
                users_per_round=10,
                rounds=6,
                delay_between_rounds=5.0
            )

            print("\n" + "="*70)
            print("  SUSTAINED LOAD TEST RESULTS")
            print("="*70)
            print(f"  Total Requests:     {sustained_results['total_requests']}")
            print(f"  Total Successes:    {sustained_results['total_successes']}")
            print(f"  Total Failures:     {sustained_results['total_failures']}")
            print(f"  Success Rate:       {sustained_results['overall_success_rate']:.1f}%")
            print("-"*70)
            print("  Round Details:")
            for round_detail in sustained_results["round_details"]:
                print(f"    Round {round_detail['round']}: "
                      f"{round_detail['successes']}/{round_detail['successes'] + round_detail['failures']} "
                      f"({round_detail['duration']:.2f}s, {round_detail['throughput']:.2f} req/s)")
            print("="*70)

        else:
            # Single concurrent test
            stats = await tester.run_concurrent_test(
                concurrent_users=args.users,
                timeout=30.0,
                test_name=f"Concurrent Test - {args.users} users"
            )
            tester.print_results(stats)

        # Save results if requested
        if args.save:
            tester.save_results()

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
