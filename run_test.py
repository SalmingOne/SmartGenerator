#!/usr/bin/env python3
"""
CLI для запуска нагрузочных тестов

Usage:
    python run_test.py configs/spike.yaml
    python run_test.py configs/degradation.yaml
"""

import argparse
import sys
from src.load_orchestrator import OrchestratorFactory


def main():
    parser = argparse.ArgumentParser(
        description="Run load test with Load Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_test.py configs/spike.yaml
  python run_test.py configs/degradation.yaml
  python run_test.py configs/sla_validation.yaml
        """
    )
    parser.add_argument(
        "config",
        help="Path to YAML config file"
    )

    args = parser.parse_args()

    try:
        # Создать orchestrator из конфига
        print(f"📝 Loading config: {args.config}")
        orchestrator = OrchestratorFactory.from_yaml(args.config)

        print(f"✅ Orchestrator created:")
        print(f"   Adapter:  {orchestrator.adapter.__class__.__name__}")
        print(f"   Strategy: {orchestrator.strategy.__class__.__name__}")
        print()

        # Запустить тест
        print("🚀 Starting test...")
        result = orchestrator.run()

        # Показать результаты
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS")
        print("=" * 60)
        print(f"Duration:         {result.finished_at - result.started_at:.1f}s")
        print(f"Stop reason:      {result.stop_reason.name}")
        print(f"Max stable users: {result.max_stable_users}")
        print(f"Max stable RPS:   {result.max_stable_rps:.1f}")
        print(f"Total steps:      {len(result.history)}")
        print()
        print("History (last 5 steps):")
        for i, metrics in enumerate(result.history[-5:], start=len(result.history) - 4):
            print(
                f"  {i:3d}. Users: {metrics.users:4d} | "
                f"RPS: {metrics.rps:7.1f} | "
                f"P99: {metrics.p99:6.1f}ms | "
                f"Errors: {metrics.error_rate:5.2f}%"
            )
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(130)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Config error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
