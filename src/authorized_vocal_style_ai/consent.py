from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


class ConsentError(RuntimeError):
    """Raised when the project is not authorized for training or generation."""


@dataclass(frozen=True)
class ConsentRecord:
    project_name: str
    rights_holder: str
    vocalist_name_or_alias: str
    all_singers_consented: bool
    dataset_is_authorized: bool
    allowed_use: List[str]
    prohibited_use: List[str]
    disclosure_text: str
    consent_document_path: str

    @classmethod
    def from_json(cls, path: str | Path) -> "ConsentRecord":
        data: Dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            project_name=str(data.get("project_name", "")),
            rights_holder=str(data.get("rights_holder", "")),
            vocalist_name_or_alias=str(data.get("vocalist_name_or_alias", "")),
            all_singers_consented=bool(data.get("all_singers_consented", False)),
            dataset_is_authorized=bool(data.get("dataset_is_authorized", False)),
            allowed_use=list(data.get("allowed_use", [])),
            prohibited_use=list(data.get("prohibited_use", [])),
            disclosure_text=str(data.get("disclosure_text", "")),
            consent_document_path=str(data.get("consent_document_path", "")),
        )

    def assert_train_allowed(self) -> None:
        missing = []
        if not self.rights_holder:
            missing.append("rights_holder")
        if not self.vocalist_name_or_alias:
            missing.append("vocalist_name_or_alias")
        if not self.all_singers_consented:
            missing.append("all_singers_consented=true")
        if not self.dataset_is_authorized:
            missing.append("dataset_is_authorized=true")
        if not self.disclosure_text:
            missing.append("disclosure_text")
        if missing:
            raise ConsentError(
                "Training/generation is blocked until authorization is documented. "
                f"Missing or false fields: {', '.join(missing)}"
            )

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "rights_holder": self.rights_holder,
            "vocalist_name_or_alias": self.vocalist_name_or_alias,
            "allowed_use": self.allowed_use,
            "disclosure_text": self.disclosure_text,
            "safety_notice": "Consent-based AI synthesized vocal; do not present as an unmodified human performance.",
        }
