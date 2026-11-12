
# Stores all active and completed player sessions.
sessions: dict[str, dict] = {}

# Used to generate unique session IDs.
_session_counter = 0


def generate_session_id() -> str:
    """Generate a unique ID for a new player session."""
    global _session_counter

    _session_counter += 1
    return f"session_{_session_counter}"


def reset_sessions() -> None:
    """Clear all sessions and reset the ID counter."""
    global _session_counter

    sessions.clear()
    _session_counter = 0
