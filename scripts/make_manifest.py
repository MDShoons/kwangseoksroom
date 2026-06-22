from __future__ import annotations

import argparse
import json
from pathlib import Path


def make_manifest(input_dir: str | Path, output_path: str | Path) -> Path:
    input_dir = Path(input_dir)
    files = []
    for path in sorted(input_dir.glob("*.wav")):
        files.append({"path": str(path), "kind": "authorized_vocal_wav"})
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a manifest for authorized WAV files.")
    parser.add_argument("--input", required=True, help="Directory containing authorized WAV files")
    parser.add_argument("--output", required=True, help="Output manifest JSON")
    args = parser.parse_args()
    out = make_manifest(args.input, args.output)
    print(f"Saved manifest: {out}")


if __name__ == "__main__":
    main()
