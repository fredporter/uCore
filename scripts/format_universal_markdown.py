"""Validate Markdown intake metadata and write a normalized preview to stdout."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.markdown_import_pipeline import check_intake_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path)
    args = parser.parse_args()
    try:
        raw = args.document.read_bytes().decode("utf-8-sig")
        markdown = raw.replace("\r\n", "\n").replace("\r", "\n")
        if markdown and not markdown.endswith("\n"):
            markdown += "\n"
        status, issues = check_intake_markdown(markdown)
        if status == "invalid":
            raise ValueError("; ".join(issues))
    except (OSError, ValueError) as error:
        parser.exit(1, f"Markdown preview failed: {error}\n")
    sys.stdout.buffer.write(markdown.encode("utf-8"))


if __name__ == "__main__":
    main()
