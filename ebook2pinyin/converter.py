from __future__ import annotations

from pathlib import Path

from .annotator import AnnotationOptions, PyPinyinBackend
from .calibre import annotate_via_calibre
from .epub import annotate_epub
from .metadata import default_output_path_for_book
from .pdf import annotate_pdf, pdf_to_epub
from .progress import ProgressCallback, noop_progress


SUPPORTED_EXTENSIONS = {".epub", ".pdf", ".azw3", ".mobi"}


def convert_book(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    options: AnnotationOptions | None = None,
    progress: ProgressCallback = noop_progress,
) -> Path:
    source = Path(input_path)
    if not source.exists():
        raise FileNotFoundError(source)
    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported input format '{suffix}'. Supported formats: {supported}.")

    destination = Path(output_path) if output_path else default_output_path(source)
    destination_suffix = destination.suffix.lower()
    if suffix == ".pdf":
        valid_outputs = {".epub", ".pdf"}
        if destination_suffix not in valid_outputs:
            valid = ", ".join(sorted(valid_outputs))
            raise ValueError(f"PDF output format must be one of: {valid}; got '{destination.suffix}'.")
    elif destination_suffix != suffix:
        raise ValueError(
            f"Output format must match input format ({suffix}); got '{destination.suffix}'."
        )
    options = options or AnnotationOptions()
    backend = PyPinyinBackend(style=options.style)

    if suffix == ".epub":
        return annotate_epub(source, destination, backend, options, progress)
    if suffix == ".pdf":
        if destination_suffix == ".epub":
            return pdf_to_epub(source, destination, backend, options, progress)
        return annotate_pdf(source, destination, backend, options, progress)
    return annotate_via_calibre(source, destination, backend, options, progress)


def default_output_path(source: Path) -> Path:
    return default_output_path_for_book(source)
