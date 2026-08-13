from __future__ import annotations

from collections.abc import Sequence

from lx_dtypes.models.interface.DataLoader import DataLoader

REQUIRED_PACKAGED_REPORT_TEMPLATES = (
    "upper_gi_quality_2025",
    "colonoscopy_training_basic",
)


def verify_packaged_report_templates(
    template_names: Sequence[str] = REQUIRED_PACKAGED_REPORT_TEMPLATES,
) -> list[str]:
    if len(template_names) < 2:
        raise ValueError("At least two packaged report templates must be verified.")

    knowledge_base = DataLoader().load_knowledge_base("report_template_examples")
    verified: list[str] = []
    for template_name in template_names:
        payload = knowledge_base.export_report_template(template_name)
        readiness = payload.get("readiness")
        if not isinstance(readiness, dict):
            raise RuntimeError(
                f"Packaged report template '{template_name}' has no readiness payload."
            )
        if readiness.get("lifecycle_status") != "published":
            raise RuntimeError(
                f"Packaged report template '{template_name}' is not published."
            )
        if readiness.get("can_publish") is not True:
            raise RuntimeError(
                f"Packaged report template '{template_name}' is not production-ready."
            )
        german_name = payload.get("name_de")
        if not isinstance(german_name, str) or not german_name.strip():
            raise RuntimeError(
                f"Packaged report template '{template_name}' has no German title."
            )
        sections = payload.get("report_sections")
        if not isinstance(sections, list) or not sections:
            raise RuntimeError(
                f"Packaged report template '{template_name}' has no report sections."
            )
        if any(
            not isinstance(section, dict)
            or not isinstance(section.get("title_de"), str)
            or not section["title_de"].strip()
            for section in sections
        ):
            raise RuntimeError(
                f"Packaged report template '{template_name}' has an unlabeled German section."
            )
        verified.append(template_name)
    return verified


def main() -> int:
    verified = verify_packaged_report_templates()
    print("Verified packaged report templates: " + ", ".join(verified))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
