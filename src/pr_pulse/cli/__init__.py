import typer
from dotenv import load_dotenv

from .commands import analyze, get, share

app = typer.Typer(
    help="PR Pulse: A command-line tool for analyzing GitHub pull requests",
    add_completion=False,
)
app.add_typer(get.app, name="get", help="Fetch and view PR data from GitHub")
app.add_typer(
    analyze.app, name="analyze", help="Analyze PR data and generate Pulse insights"
)
app.add_typer(share.app, name="share", help="Share Pulse reports")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """CLI Entrypoint"""
    load_dotenv()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
