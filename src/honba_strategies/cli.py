"""CLI entry point for honba-strategies SDK."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from honba_strategies import create_strategy, list_categories, list_strategies

app = typer.Typer(
    name="honba-strategies",
    help="Production quantitative strategy SDK for Honba platform",
    add_completion=False,
)

console = Console()


@app.command()
def list(
    category: str = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str = typer.Option(None, "--tag", "-t", help="Filter by tag"),
) -> None:
    """List available strategies."""
    tags = [tag] if tag else None
    names = list_strategies(category=category, tags=tags)

    if not names:
        console.print("[yellow]No strategies found matching criteria[/yellow]")
        return

    table = Table(title="Available Strategies")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="green")

    for name in names:
        # We'd need to get category from registry - simplified for now
        table.add_row(name, category or "all")

    console.print(table)


@app.command()
def categories() -> None:
    """List all strategy categories."""
    cats = list_categories()
    console.print("[bold]Strategy Categories:[/bold]")
    for cat in cats:
        console.print(f"  • {cat}")


@app.command()
def create(
    name: str,
    symbol: str = typer.Option("NIFTY50", "--symbol", "-s"),
    exchange: str = typer.Option("NSE", "--exchange", "-e"),
    **kwargs,
) -> None:
    """Create and inspect a strategy instance."""
    try:
        strategy = create_strategy(name, symbol=symbol, exchange=exchange, **kwargs)
        console.print(f"[green]Created {name} for {symbol}@{exchange}[/green]")
        console.print(f"Strategy: {strategy}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def info(name: str) -> None:
    """Show detailed information about a strategy."""
    from honba_strategies import get_strategy

    try:
        meta = get_strategy(name)
        console.print(f"[bold cyan]{meta.name}[/bold cyan]")
        console.print(f"  Category: {meta.category}")
        console.print(f"  Description: {meta.description}")
        console.print(f"  Tags: {', '.join(meta.tags) if meta.tags else 'none'}")
        console.print(f"  Class: {meta.cls.__module__}.{meta.cls.__name__}")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()