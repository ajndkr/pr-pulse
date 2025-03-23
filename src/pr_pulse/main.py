import typer
from dotenv import load_dotenv

from pr_pulse.commands.gh import app as gh_app

app = typer.Typer(help="CLI tool for GitHub PR operations")
app.add_typer(gh_app)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """CLI Entrypoint"""
    load_dotenv()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
