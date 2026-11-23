"""Import every model here so Alembic and SQLAlchemy see all tables.

Student 2 and Student 3: add your model imports below.
"""
from app.models.story import Choice, Scene, Story  # noqa: F401
from app.models.investigation import Clue, DiscoveredClue, Suspect  # noqa: F401
from app.models.progress import GameSession, SessionChoice  # noqa: F401
from app.models.user import User  # noqa: F401
