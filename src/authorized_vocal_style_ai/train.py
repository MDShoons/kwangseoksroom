from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .audio_features import aggregate_features, summarize_wav
from .consent import ConsentRecord
from .model import describe_architecture


def load_manifest(path: str | Path) -> List[Path]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    files = [Path(item["path"]) for item in data.get("files", []) if item.get("path")]
    if not files:
        raise ValueError("Manifest has no files. Run scripts/make_manifest.py first.")
    return files


def train_style_profile(manifest_path: str | Path, consent_path: str | Path, output_path: str | Path) -> Path:
    consent = ConsentRecord.from_json(consent_path)
    consent.assert_train_allowed()

    wav_files = load_manifest(manifest_path)
    summaries = []
    for wav in wav_files:
        summaries.append(summarize_wav(wav))

    profile = {
        "profile_type": "consent_based_vocal_style_summary",
        "notice": "This is not a pretrained real-person clone. It is a feature summary from authorized WAV files.",
        "consent_metadata": consent.to_metadata(),
        "architecture": describe_architecture(),
        "style_features": aggregate_features(summaries),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract an authorized vocal style profile.")
    parser.add_argument("--manifest", required=True, help="Path to data/manifest.json")
    parser.add_argument("--consent", required=True, help="Path to consent.json")
    parser.add_argument("--output", required=True, help="Output JSON style profile")
    args = parser.parse_args()
    out = train_style_profile(args.manifest, args.consent, args.output)
    print(f"Saved style profile: {out}")


if __name__ == "__main__":
    main()
