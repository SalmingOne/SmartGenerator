import click
from .factory import OrchestratorFactory
from .utils import _format_duration


@click.command()
@click.option('-c', '--config', required=True, help='Path to config file')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-d', '--debug', is_flag=True, help='Debug mode', default=False)
def main(config: str, verbose: bool, debug: bool):
    """
    Load Orchestrator - Интеллектуальный фреймворк для нагрузочного тестирования
    """

    # CLI режим
    click.echo("Starting adaptive load test...")

    # TODO: Загрузить конфиг
    orchestrator = OrchestratorFactory.from_yaml(config)

    result = orchestrator.run(debug=debug)

    # TODO: Вывести результаты
    print_results(result, verbose)


def print_results(result, verbose: bool):
    print("Results: ", result)

    print("═══ Test Finished ═══")
    if result:
        print(f"  Stop Reason: {result.stop_reason.name}")
        print(f"  Max Stable Users: {result.max_stable_users}")
        print(f"  Max Stable RPS: {result.max_stable_rps:.1f}")
        if result.started_at and result.finished_at:
            dur = result.finished_at - result.started_at
            print(f"  Duration: {_format_duration(dur)}")
        print(f"  Data Points: {len(result.history)}")
    if verbose:
        for step, res in enumerate(result.history):
            print(f'Step #{step}: {res}')


if __name__ == '__main__':
    main()