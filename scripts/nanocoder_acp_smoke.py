#!/usr/bin/env python3
"""Run the bounded initialize-only NanoCoder ACP intake smoke test."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.nanocoder_acp import NanocoderAcpClient  # noqa: E402


async def run(binary: Path, repository: Path, provider: str, model: str, base_url: str) -> None:
    with tempfile.TemporaryDirectory(prefix="ucore-nanocoder-smoke-") as state:
        client = NanocoderAcpClient(
            [
                str(binary),
                "--provider",
                provider,
                "--model",
                model,
                "--mode",
                "plan",
                "--acp",
            ],
            repository=repository,
            repositories_root=repository.parent,
            udos_home=Path(state),
            dev_mode=True,
            request_timeout=20,
        )
        client.configure_local_provider(name=provider, model=model, base_url=base_url)
        try:
            try:
                result = await client.initialize()
            except Exception as exc:
                print(
                    json.dumps(
                        {"ok": False, "error": str(exc), "stderr": client.stderr_tail},
                        sort_keys=True,
                    )
                )
                raise
            else:
                print(json.dumps({"ok": True, "initialize": result}, sort_keys=True))
        finally:
            await client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--provider", default="ollama")
    parser.add_argument("--model", default="mistral:7b")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    args = parser.parse_args()
    asyncio.run(
        run(
            args.binary.resolve(strict=True),
            args.repository.resolve(strict=True),
            args.provider,
            args.model,
            args.base_url,
        )
    )


if __name__ == "__main__":
    main()
