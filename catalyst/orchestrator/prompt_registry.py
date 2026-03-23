from __future__ import annotations

from pathlib import Path

from catalyst.models.delegation import PromptTemplateMetadata
from catalyst.models.enums import RiskLevel


PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


class PromptRegistry:
    def __init__(self, prompts_dir: Path | None = None) -> None:
        self.prompts_dir = prompts_dir or PROMPTS_DIR

    def list_templates(self) -> list[PromptTemplateMetadata]:
        templates: list[PromptTemplateMetadata] = []
        for path in sorted(self.prompts_dir.glob("*.md")):
            templates.append(self._load_metadata(path))
        return templates

    def get_template(self, template_name: str) -> PromptTemplateMetadata:
        path = self.prompts_dir / f"{template_name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}' not found at {path}")
        return self._load_metadata(path)

    def render(self, template_name: str, variables: dict[str, str]) -> str:
        path = self.prompts_dir / f"{template_name}.md"
        if not path.exists():
            raise FileNotFoundError(f"Prompt template '{template_name}' not found at {path}")
        _, body = self._parse_frontmatter(path.read_text(encoding="utf-8"))
        return body.strip().format(**variables)

    def _load_metadata(self, path: Path) -> PromptTemplateMetadata:
        frontmatter, _ = self._parse_frontmatter(path.read_text(encoding="utf-8"))
        return PromptTemplateMetadata(
            name=frontmatter.get("name", path.stem),
            description=frontmatter.get("description", ""),
            role=frontmatter.get("role", "subagent"),
            recommended_for=frontmatter.get("recommended_for", []),
            tools=frontmatter.get("tools", []),
            risk_level=RiskLevel(frontmatter.get("risk_level", "low")),
            path=str(path),
        )

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        lines = content.splitlines()
        if len(lines) < 3 or lines[0].strip() != "---":
            return {}, content
        frontmatter: dict[str, object] = {}
        current_key: str | None = None
        index = 1
        while index < len(lines):
            line = lines[index]
            if line.strip() == "---":
                body = "\n".join(lines[index + 1 :])
                return frontmatter, body
            if line.startswith("  - ") or line.startswith("- "):
                if current_key is not None:
                    frontmatter.setdefault(current_key, [])
                    frontmatter[current_key].append(line.split("-", 1)[1].strip())
            elif ":" in line:
                key, value = line.split(":", 1)
                current_key = key.strip()
                value = value.strip()
                if value:
                    frontmatter[current_key] = value
                else:
                    frontmatter[current_key] = []
            index += 1
        return {}, content
