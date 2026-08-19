import click
from .factory import OrchestratorFactory
from .utils import _format_duration
import shlex


@click.command()
@click.option('-c', '--config', required=True, help='Path to config file')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-d', '--debug', is_flag=True, help='Debug mode', default=False)
@click.option(
    '--locust-arg',
    'locust_args',
    multiple=True,
    help='Pass argument to locust (can be used multiple times). Example: --locust-arg="--headless" --locust-arg="--users=100"'
)
@click.option(
    '--locust-args',
    'locust_args_raw',
    help='Raw string of locust arguments. Example: "--headless --users 100 --run-time 5m"'
)
@click.argument('locust_extra', nargs=-1)
def main(
        config: str,
        verbose: bool,
        debug: bool,
        locust_args: tuple[str, ...],
        locust_args_raw: str | None,
        locust_extra: tuple[str, ...]
):
    """
    Load Orchestrator - Интеллектуальный фреймворк для нагрузочного тестирования

    Examples:
        load-orchestrator -c config.yaml
        load-orchestrator -c config.yaml --locust-arg="--headless" --locust-arg="--users=100"
        load-orchestrator -c config.yaml --locust-args="--headless --users 100 --run-time 5m"
        load-orchestrator -c config.yaml -- --headless --users 100
    """

    # Собираем все locust аргументы
    collected_args = list(locust_args)

    if locust_args_raw:
        collected_args.extend(shlex.split(locust_args_raw))

    collected_args.extend(locust_extra)

    # CLI режим
    click.echo("Starting adaptive load test...")

    if collected_args:
        click.echo(f"Locust args: {collected_args}")

    orchestrator = OrchestratorFactory.from_yaml(config)

    # Передаём аргументы в оркестратор
    result = orchestrator.run(
        debug=debug,
        locust_args=collected_args if collected_args else None
    )

    print_results(result, verbose)


def print_results(result, verbose: bool):
    click.echo("\n═══════════════════════════════")
    click.echo("         Test Finished         ")
    click.echo("═══════════════════════════════")
    if result:
        click.echo(f"  Stop Reason   : {result.stop_reason.name}")
        click.echo(f"  Max Users     : {result.max_stable_users}")
        click.echo(f"  Max RPS       : {result.max_stable_rps:.1f}")
        if result.started_at and result.finished_at:
            dur = result.finished_at - result.started_at
            click.echo(f"  Duration      : {_format_duration(dur)}")
        click.echo(f"  Data Points   : {len(result.history)}")
    click.echo("═══════════════════════════════\n")
    if verbose and result:
        click.echo("History:")
        for step, res in enumerate(result.history):
            click.echo(f"  #{step:03d}: users={res.users} rps={res.rps:.1f} p95={res.p95:.0f}ms err={res.error_rate:.1f}%")


if __name__ == '__main__':
    main()