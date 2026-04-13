"""Pipeline ownership tracking — assign owners/teams to pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Owner:
    """Represents a single owner (person or team) for a pipeline."""

    name: str
    email: Optional[str] = None
    team: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "team": self.team,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Owner":
        return cls(
            name=data["name"],
            email=data.get("email"),
            team=data.get("team"),
        )

    def __repr__(self) -> str:
        parts = [self.name]
        if self.team:
            parts.append(f"team={self.team}")
        if self.email:
            parts.append(self.email)
        return f"Owner({', '.join(parts)})"


class OwnershipRegistry:
    """Maps pipeline names to their owners."""

    def __init__(self) -> None:
        self._owners: Dict[str, List[Owner]] = {}

    def assign(self, pipeline_name: str, owner: Owner) -> None:
        """Assign an owner to a pipeline (allows multiple owners)."""
        self._owners.setdefault(pipeline_name, [])
        for existing in self._owners[pipeline_name]:
            if existing.name == owner.name:
                raise ValueError(
                    f"Owner '{owner.name}' already assigned to '{pipeline_name}'."
                )
        self._owners[pipeline_name].append(owner)

    def unassign(self, pipeline_name: str, owner_name: str) -> None:
        """Remove a named owner from a pipeline."""
        owners = self._owners.get(pipeline_name, [])
        self._owners[pipeline_name] = [
            o for o in owners if o.name != owner_name
        ]

    def get(self, pipeline_name: str) -> List[Owner]:
        """Return all owners for a pipeline."""
        return list(self._owners.get(pipeline_name, []))

    def by_team(self, team: str) -> Dict[str, List[Owner]]:
        """Return a mapping of pipeline -> owners filtered by team."""
        result: Dict[str, List[Owner]] = {}
        for pipeline, owners in self._owners.items():
            matched = [o for o in owners if o.team == team]
            if matched:
                result[pipeline] = matched
        return result

    def all_pipelines(self) -> List[str]:
        """Return all pipeline names that have at least one owner."""
        return [p for p, owners in self._owners.items() if owners]

    def to_dicts(self) -> List[dict]:
        """Serialise the full registry to a list of records."""
        records = []
        for pipeline, owners in self._owners.items():
            for owner in owners:
                records.append({"pipeline": pipeline, **owner.to_dict()})
        return records
