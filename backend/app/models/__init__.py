"""Database models package."""

from app.models.project import Base, Project
from app.models.electricity import ElectricityObservation

__all__ = ["Base", "Project", "ElectricityObservation"]

