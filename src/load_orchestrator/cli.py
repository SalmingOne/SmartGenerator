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

    click.echo("Starting adaptive load test...")

    orchestrator = OrchestratorFactory.from_yaml(config)
    result = orchestrator.run(debug=debug)
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