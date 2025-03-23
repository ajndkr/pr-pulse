import typer
from dotenv import load_dotenv

from pr_pulse.commands.genai import app as genai_app
from pr_pulse.commands.gh import app as gh_app
from pr_pulse.commands.slack import app as slack_app

app = typer.Typer(help="PR Pulse CLI")
app.add_typer(gh_app)
app.add_typer(genai_app)
app.add_typer(slack_app)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """CLI Entrypoint"""
    load_dotenv()

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
