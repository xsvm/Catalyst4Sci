from __future__ import annotations

from pathlib import Path

from catalyst.models.enums import RiskLevel
from catalyst.models.skill import SkillMetadata


BUILTIN_SKILLS_DIR = Path(__file__).parent


class SkillRegistry:
    def __init__(self, builtin_dir: Path | None = None, external_dir: Path | None = None) -> None:
        roots: list[Path] = []
        if external_dir is not None:
            roots.append(external_dir)
        roots.append(builtin_dir or BUILTIN_SKILLS_DIR)
        self.skill_roots = roots

    def roots(self) -> list[Path]:
        return self.skill_roots

    def list_skills(self) -> list[SkillMetadata]:
        skills: list[SkillMetadata] = []
        seen_names: set[str] = set()
        for root in self.roots():
            if not root.exists():
                continue
            for skill_file in sorted(root.glob("*/SKILL.md")):
                metadata = self._load_metadata(skill_file)
                if metadata.name in seen_names:
                    continue
                seen_names.add(metadata.name)
                skills.append(metadata)
        return skills

    def get_skill(self, skill_name: str) -> SkillMetadata:
        for root in self.roots():
            skill_file = root / skill_name / "SKILL.md"
            if skill_file.exists():
                return self._load_metadata(skill_file)
        raise FileNotFoundError(f"Skill '{skill_name}' not found in configured skill roots")

    def load_skill_body(self, skill_name: str) -> str:
        for root in self.roots():
            skill_file = root / skill_name / "SKILL.md"
            if skill_file.exists():
                _, body = self._parse_frontmatter(skill_file.read_text(encoding="utf-8"))
                return body.strip()
        raise FileNotFoundError(f"Skill '{skill_name}' not found in configured skill roots")

    def catalog_lines(self) -> list[str]:
        return [
            f"- {skill.name}: {skill.description} | category={skill.category} | recommended_for={', '.join(skill.recommended_for) or 'none'}"
            for skill in self.list_skills()
        ]

    def _load_metadata(self, path: Path) -> SkillMetadata:
        frontmatter, _ = self._parse_frontmatter(path.read_text(encoding="utf-8"))
        return SkillMetadata(
            name=frontmatter.get("name", path.parent.name),
            description=frontmatter.get("description", ""),
            category=frontmatter.get("category", "general"),
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
