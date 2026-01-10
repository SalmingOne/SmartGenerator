#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Orchestrator
"""

from src.load_orchestrator import OrchestratorFactory


def main():
    # Создать оркестратор напрямую из YAML
    # Фабрика автоматически создаст adapter и strategy
    orchestrator = OrchestratorFactory.from_yaml('configs/sla.yaml')

    print(f"✅ Orchestrator created from config:")
    print(f"   Adapter: {orchestrator.adapter.__class__.__name__}")
    print(f"   Strategy: {orchestrator.strategy.__class__.__name__}")
    print()

    # Запустить тест
    print("🚀 Starting test...")
    try:
        result = orchestrator.run()
        print("\n" + "="*50)
        print("📊 TEST RESULTS")
        print("="*50)
        print(f"Max stable users: {result.max_stable_users}")
        print(f"Max stable RPS:   {result.max_stable_rps:.1f}")
        print(f"Duration:         {result.finished_at - result.started_at:.1f}s")
        print(f"Stop reason:      {result.stop_reason.name}")
        print(f"Total steps:      {len(result.history)}")
        print(f'{result.history}')
        print("="*50)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        orchestrator.stop()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()