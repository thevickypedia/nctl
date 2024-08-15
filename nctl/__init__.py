"""Placeholder for packaging."""

import sys

import click

from nctl.ngrok import tunnel  # noqa: F401

version = "0.0.0-a"


@click.command()
@click.argument("start", required=False)
@click.argument("run", required=False)
@click.option("--version", "-V", is_flag=True, help="Prints the version.")
@click.option("--help", "-H", is_flag=True, help="Prints the help section.")
@click.option(
    "--env",
    "-E",
    type=click.Path(exists=True),
    help="Environment configuration filepath.",
)
def commandline(*args, **kwargs) -> None:
    """Starter function to invoke nctl via CLI commands.

    **Flags**
        - ``--version | -V``: Prints the version.
        - ``--help | -H``: Prints the help section.
        - ``--env | -E``: Environment configuration filepath.

    **Commands**
        ``start | run``: Initiates the backup process.
    """
    assert sys.argv[0].lower().endswith("nctl"), "Invalid commandline trigger!!"
    options = {
        "--version | -V": "Prints the version.",
        "--help | -H": "Prints the help section.",
        "--env | -E": "Environment configuration filepath.",
        "start | run": "Initiates the backup process.",
    }
    # weird way to increase spacing to keep all values monotonic
    _longest_key = len(max(options.keys()))
    _pretext = "\n\t* "
    choices = _pretext + _pretext.join(
        f"{k} {'·' * (_longest_key - len(k) + 8)}→ {v}".expandtabs()
        for k, v in options.items()
    )
    if kwargs.get("version"):
        click.echo(f"nctl {version}")
        sys.exit(0)
    if kwargs.get("help"):
        click.echo(
            f"\nUsage: nctl [arbitrary-command]\nOptions (and corresponding behavior):{choices}"
        )
        sys.exit(0)
    trigger = kwargs.get("start") or kwargs.get("run")
    if trigger and trigger.lower() in ("start", "run"):
        # Click doesn't support assigning defaults like traditional dictionaries, so kwargs.get("max", 100) won't work
        tunnel(env_file=kwargs.get("env"))
        sys.exit(0)
    elif trigger:
        click.secho(f"\n{trigger!r} - Invalid command", fg="red")
    else:
        click.secho("\nNo command provided", fg="red")
    click.echo(
        f"Usage: nctl [arbitrary-command]\nOptions (and corresponding behavior):{choices}"
    )
    sys.exit(1)
