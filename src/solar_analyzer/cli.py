"""Command line interface for Solar Analyzer."""

import asyncio
from typing import Annotated

import typer

from solar_analyzer.utils.sample_data import create_sample_data

app = typer.Typer(help="Solar Analyzer CLI tools")


@app.command()
def generate_sample_data():
    """Generate sample solar data for testing."""
    asyncio.run(create_sample_data())


@app.command()
def run(
    host: Annotated[str, typer.Option(help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind to")] = 8000,
    reload: Annotated[bool, typer.Option(help="Enable auto-reload")] = True,
):
    """Run the Solar Analyzer web application."""
    import uvicorn

    uvicorn.run(
        "solar_analyzer.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    app()
