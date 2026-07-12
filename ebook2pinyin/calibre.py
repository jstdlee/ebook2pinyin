from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from .annotator import AnnotationOptions, PinyinBackend
from .epub import annotate_epub
from .progress import ProgressCallback, Stage, noop_progress


class CalibreNotFoundError(RuntimeError):
    pass


def annotate_via_calibre(
    input_path: Path,
    output_path: Path,
    backend: PinyinBackend,
    options: AnnotationOptions,
    progress: ProgressCallback = noop_progress,
) -> Path:
    ebook_convert = shutil.which("ebook-convert")
    if not ebook_convert:
        raise CalibreNotFoundError(
            "MOBI/AZW3 conversion requires Calibre's ebook-convert on PATH."
        )

    with tempfile.TemporaryDirectory(prefix="ebook2pinyin-") as temp_dir:
        temp = Path(temp_dir)
        intermediate_epub = temp / "input.epub"
        annotated_epub = temp / "annotated.epub"

        progress(Stage("convert", 0, 2, "Converting input to EPUB"))
        _run([ebook_convert, str(input_path), str(intermediate_epub)])
        annotate_epub(intermediate_epub, annotated_epub, backend, options, progress)
        progress(Stage("convert", 2, 2, f"Converting EPUB to {output_path.suffix.upper()[1:]}"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_command = [ebook_convert, str(annotated_epub), str(output_path)]
        if output_path.suffix.lower() == ".mobi":
            _run_mobi_output(output_command, progress)
        else:
            _run(output_command)

    progress(Stage("done", 1, 1, f"Wrote {output_path.name}"))
    return output_path


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{details}")


def _run_mobi_output(base_command: list[str], progress: ProgressCallback) -> None:
    try:
        _run([*base_command, "--mobi-file-type", "both"])
    except RuntimeError:
        progress(Stage("convert", 2, 2, "Hybrid MOBI failed; retrying as KF8-only MOBI"))
        try:
            _run([*base_command, "--mobi-file-type", "new"])
        except RuntimeError:
            progress(Stage("convert", 2, 2, "KF8 MOBI failed; retrying as legacy MOBI"))
            _run([*base_command, "--mobi-file-type", "old"])
