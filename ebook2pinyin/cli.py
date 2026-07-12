from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from .annotator import AnnotationOptions
from .converter import convert_book, default_output_path
from .progress import Stage


app = typer.Typer(help="Add pinyin annotations to Chinese ebooks/documents.")


@app.command()
def convert(
    input_path: Path = typer.Argument(..., exists=True, readable=True, help="EPUB, PDF, AZW3, or MOBI file."),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path."),
    ruby_size: float = typer.Option(1.0, help="Base ruby text size in em for EPUB/MOBI/AZW3."),
    rt_size: float = typer.Option(0.5, help="Pinyin annotation size ratio."),
    line_height: float = typer.Option(1.9, help="Ruby line-height in em."),
    style: str = typer.Option("tone", help="Pinyin style: tone, tone2, tone3, or plain."),
    overwrite: bool = typer.Option(False, "--overwrite", "-f", help="Overwrite existing output."),
) -> None:
    destination = output or default_output_path(input_path)
    if destination and destination.exists() and not overwrite:
        raise typer.BadParameter(f"Output already exists: {destination}. Use --overwrite to replace it.")

    def report(stage: Stage) -> None:
        if stage.total > 1:
            typer.echo(f"[{stage.name}] {stage.current}/{stage.total} {stage.message}")
        else:
            typer.echo(f"[{stage.name}] {stage.message}")

    result = convert_book(
        input_path,
        destination,
        options=AnnotationOptions(ruby_size=ruby_size, rt_size=rt_size, line_height=line_height, style=style),
        progress=report,
    )
    typer.echo(f"Done: {result}")


@app.command()
def web(
    host: str = typer.Option("127.0.0.1", help="Server host."),
    port: int = typer.Option(7860, help="Server port."),
    share: bool = typer.Option(False, help="Create a public Gradio share link."),
) -> None:
    from .web import build_app

    build_app().launch(server_name=host, server_port=port, share=share)


if __name__ == "__main__":
    app()
