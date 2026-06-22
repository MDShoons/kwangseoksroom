import json
from pathlib import Path

import pytest

from authorized_vocal_style_ai.consent import ConsentError, ConsentRecord


def test_consent_blocks_when_false(tmp_path: Path):
    path = tmp_path / "consent.json"
    path.write_text(json.dumps({"all_singers_consented": False, "dataset_is_authorized": False}), encoding="utf-8")
    record = ConsentRecord.from_json(path)
    with pytest.raises(ConsentError):
        record.assert_train_allowed()


def test_consent_allows_when_complete(tmp_path: Path):
    path = tmp_path / "consent.json"
    path.write_text(
        json.dumps(
            {
                "project_name": "x",
                "rights_holder": "owner",
                "vocalist_name_or_alias": "singer",
                "all_singers_consented": True,
                "dataset_is_authorized": True,
                "allowed_use": ["research"],
                "prohibited_use": ["impersonation"],
                "disclosure_text": "AI demo",
                "consent_document_path": "consent.md",
            }
        ),
        encoding="utf-8",
    )
    record = ConsentRecord.from_json(path)
    record.assert_train_allowed()
