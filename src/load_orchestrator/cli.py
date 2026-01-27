import click
from .factory import OrchestratorFactory


@click.command()
@click.option('-c', '--config', required=True, help='Path to config file')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
def main(config: str, verbose: bool):
    """
    Load Orchestrator - Интеллектуальный фреймворк для нагрузочного тестирования
    """

    # CLI режим
    click.echo("Starting adaptive load test...")

    # TODO: Загрузить конфиг
    orchestrator = OrchestratorFactory.from_yaml(config)

    result = orchestrator.run()

    # TODO: Вывести результаты
    print_results(result, verbose)


def print_results(result, verbose: bool):
    """
    TODO: Вывести результаты теста в консоль

    Формат:
    ==================================================
    RESULTS
    ==================================================
    Max stable users: 150
    Max stable RPS:   220.5
    Duration:        6m 32s
    Stop reason:      DEGRADATION
    ==================================================

    Если verbose=True, показать всю историю шагов
    """
    print("Results: ", result)


if __name__ == '__main__':
    main()