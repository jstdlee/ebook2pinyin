from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
import tempfile
from threading import Thread

import gradio as gr

from .annotator import AnnotationOptions
from .converter import convert_book, default_output_path
from .progress import Stage


def build_app() -> gr.Blocks:
    with gr.Blocks(title="mobi-pinyin") as demo:
        gr.Markdown("# mobi-pinyin")
        with gr.Row():
            input_file = gr.File(label="Chinese book/document", file_types=[".epub", ".pdf", ".azw3", ".mobi"])
            output_file = gr.File(label="Annotated output")
        with gr.Row():
            ruby_size = gr.Slider(0.8, 1.6, value=1.0, step=0.05, label="Base text size")
            rt_size = gr.Slider(0.25, 0.9, value=0.5, step=0.05, label="Pinyin size")
            line_height = gr.Slider(1.2, 3.0, value=1.9, step=0.1, label="Line height")
        style = gr.Dropdown(["tone", "tone2", "tone3", "plain"], value="tone", label="Pinyin style")
        convert_button = gr.Button("Convert", variant="primary")
        status = gr.Textbox(label="Progress", interactive=False, lines=8)

        convert_button.click(
            _convert_upload,
            inputs=[input_file, ruby_size, rt_size, line_height, style],
            outputs=[output_file, status],
        )
    demo.queue()
    return demo


def _convert_upload(file_obj, ruby_size: float, rt_size: float, line_height: float, style: str):
    if file_obj is None:
        yield None, "Please upload a file."
        return

    source = Path(getattr(file_obj, "name", file_obj))
    log: list[str] = []
    events: Queue[tuple[str, Stage | Path | Exception]] = Queue()

    def report(stage: Stage) -> None:
        events.put(("stage", stage))

    output_dir = Path(tempfile.mkdtemp(prefix="mobi-pinyin-web-"))
    output_path = output_dir / default_output_path(source).name

    def worker() -> None:
        try:
            result = convert_book(
                source,
                output_path,
                options=AnnotationOptions(
                    ruby_size=ruby_size,
                    rt_size=rt_size,
                    line_height=line_height,
                    style=style,
                ),
                progress=report,
            )
        except Exception as exc:
            events.put(("error", exc))
        else:
            events.put(("result", result))

    Thread(target=worker, daemon=True).start()
    yield None, "[queued] Starting conversion"

    while True:
        try:
            kind, payload = events.get(timeout=0.2)
        except Empty:
            continue

        if kind == "stage" and isinstance(payload, Stage):
            log.append(_format_stage(payload))
            yield None, "\n".join(log)
        elif kind == "error" and isinstance(payload, Exception):
            log.append(f"[error] {payload}")
            yield None, "\n".join(log)
            return
        elif kind == "result" and isinstance(payload, Path):
            yield str(payload), "\n".join(log)
            return


def _format_stage(stage: Stage) -> str:
    if stage.total > 1:
        return f"[{stage.name}] {stage.current}/{stage.total} {stage.message}"
    return f"[{stage.name}] {stage.message}"
