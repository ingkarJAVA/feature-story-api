"""In-memory data for the Story & Scenes module.

Everything lives in plain Python dictionaries. There is no database.
The data is reset every time the server restarts.

IDs are stable strings: scene_1, scene_2, ... and choice_1, choice_2, ...
Other students (clues, player progress) can rely on these IDs.
"""

import copy

# ---------------------------------------------------------------------------
# Initial data (never modified directly - we copy it into the live dicts)
# ---------------------------------------------------------------------------

_INITIAL_STORY = {
    "id": "story_1",
    "title": "Shrek: Who Killed the King?",
    "description": (
        "King Harold has been found dead in Far Far Away. Play as Shrek, "
        "explore the kingdom, collect clues and unmask the killer."
    ),
    "genre": "Detective / Fantasy",
    "main_character": "Shrek",
}

_INITIAL_SCENES = [
    {
        "id": "scene_1",
        "title": "An Unexpected Visitor",
        "description": "A royal messenger bursts into the swamp with terrible news: King Harold is dead, and Fiona begs Shrek to find the killer.",
        "location": "Shrek's Swamp",
        "is_ending": False,
    },
    {
        "id": "scene_2",
        "title": "The Crime Scene",
        "description": "The king's bedchamber is silent. A broken goblet lies on the floor and the window is wide open.",
        "location": "King Harold's Bedchamber",
        "is_ending": False,
    },
    {
        "id": "scene_3",
        "title": "The Royal Dinner",
        "description": "Everyone who saw the king last night gathers in the great hall. Each of them seems to be hiding something.",
        "location": "Great Hall",
        "is_ending": False,
    },
    {
        "id": "scene_4",
        "title": "The Cat's Alibi",
        "description": "Puss in Boots swears he was guarding the east tower all night, but his boots are covered in royal garden mud.",
        "location": "East Tower",
        "is_ending": False,
    },
    {
        "id": "scene_5",
        "title": "The Prince's Ambition",
        "description": "Prince Charming speaks too eagerly about the empty throne. He has plenty of reasons to want the king gone.",
        "location": "Throne Room",
        "is_ending": False,
    },
    {
        "id": "scene_6",
        "title": "The Fairy's Secret",
        "description": "The Fairy Godmother nervously hides a small glass vial behind her back when Shrek walks in.",
        "location": "Fairy Godmother's Workshop",
        "is_ending": False,
    },
    {
        "id": "scene_7",
        "title": "The Royal Library",
        "description": "Dusty shelves hold the kingdom's secrets. One book on royal inheritance has been pulled out and left open.",
        "location": "Royal Library",
        "is_ending": False,
    },
    {
        "id": "scene_8",
        "title": "Donkey's Strange Discovery",
        "description": "Donkey sniffs around the garden and finds a torn piece of purple cloth caught on the rose bushes.",
        "location": "Palace Garden",
        "is_ending": False,
    },
    {
        "id": "scene_9",
        "title": "The Secret Passage",
        "description": "Behind a painting, a narrow tunnel leads from the king's chamber to the rest of the castle.",
        "location": "Hidden Tunnel",
        "is_ending": False,
    },
    {
        "id": "scene_10",
        "title": "The Hidden Letter",
        "description": "Tucked inside a hollow book is a letter threatening the king over a dangerous secret.",
        "location": "Royal Library",
        "is_ending": False,
    },
    {
        "id": "scene_11",
        "title": "The Poisoned Potion",
        "description": "Shrek tests the contents of the glass vial. It is a rare poison, and only a few people could have made it.",
        "location": "Fairy Godmother's Workshop",
        "is_ending": False,
    },
    {
        "id": "scene_12",
        "title": "The Final Clue",
        "description": "All the evidence comes together: the torn cloth, the letter and the poison point to one person.",
        "location": "Castle Courtyard",
        "is_ending": False,
    },
    {
        "id": "scene_13",
        "title": "The Royal Confrontation",
        "description": "Shrek gathers the court and names the killer in front of everyone. The room goes deadly quiet.",
        "location": "Great Hall",
        "is_ending": False,
    },
    {
        "id": "scene_14",
        "title": "The Confession",
        "description": "Cornered by the evidence, the killer finally confesses and explains why the king had to die.",
        "location": "Great Hall",
        "is_ending": False,
    },
    {
        "id": "scene_15",
        "title": "The Ending",
        "description": "Justice is served in Far Far Away. Shrek returns to his swamp, and the kingdom can finally mourn in peace.",
        "location": "Shrek's Swamp",
        "is_ending": True,
    },
]

# Each tuple is (scene_id, choice_text, next_scene_id).
# Choice IDs (choice_1, choice_2, ...) are generated from the order below.
_INITIAL_CHOICES = [
    # scene_1
    ("scene_1", "Rush to the castle and inspect the crime scene", "scene_2"),
    ("scene_1", "Head straight to the royal dinner and question the guests", "scene_3"),
    # scene_2
    ("scene_2", "Follow the trail to the royal dinner", "scene_3"),
    ("scene_2", "Search the royal library for answers", "scene_7"),
    ("scene_2", "Let Donkey sniff around the garden below the window", "scene_8"),
    # scene_3
    ("scene_3", "Question Puss in Boots", "scene_4"),
    ("scene_3", "Question Prince Charming", "scene_5"),
    ("scene_3", "Question the Fairy Godmother", "scene_6"),
    # scene_4
    ("scene_4", "Check the royal library for his alibi", "scene_7"),
    ("scene_4", "Go and talk to Prince Charming", "scene_5"),
    # scene_5
    ("scene_5", "Visit the Fairy Godmother", "scene_6"),
    ("scene_5", "Follow the prince's servant into the secret passage", "scene_9"),
    # scene_6
    ("scene_6", "Take the glass vial and test it", "scene_11"),
    ("scene_6", "Leave and study the royal library", "scene_7"),
    # scene_7
    ("scene_7", "Open the hollow book", "scene_10"),
    ("scene_7", "Search for hidden doors behind the shelves", "scene_9"),
    # scene_8
    ("scene_8", "Follow the cloth fibers into the secret passage", "scene_9"),
    ("scene_8", "Go back and question the dinner guests", "scene_3"),
    # scene_9
    ("scene_9", "Follow the tunnel to the hidden letter", "scene_10"),
    ("scene_9", "Follow the strange smell to the workshop", "scene_11"),
    # scene_10
    ("scene_10", "Piece the evidence together", "scene_12"),
    ("scene_10", "Confront the court right away", "scene_13"),
    # scene_11
    ("scene_11", "Take the test results to the courtyard", "scene_12"),
    ("scene_11", "Question the Fairy Godmother again", "scene_6"),
    # scene_12
    ("scene_12", "Call everyone to the Great Hall", "scene_13"),
    ("scene_12", "Look at the hidden letter once more", "scene_10"),
    # scene_13
    ("scene_13", "Present the evidence and demand a confession", "scene_14"),
    ("scene_13", "Take a step back and review the final clue", "scene_12"),
    # scene_14
    ("scene_14", "Hear the confession to the end", "scene_15"),
    ("scene_14", "Ask one more question before ending the case", "scene_13"),
]

# ---------------------------------------------------------------------------
# Live data (this is what the service reads and changes)
# ---------------------------------------------------------------------------

STORY: dict = {}
SCENES: dict = {}    # scene_id  -> scene dict
CHOICES: dict = {}   # choice_id -> choice dict

# Counters used to create new IDs. They only go up, so an ID of a deleted
# scene or choice is never given to a new one.
COUNTERS: dict = {"scene": 0, "choice": 0}


def reset_data() -> None:
    """Put the in-memory data back to its starting state.

    We clear and refill the same dict objects (instead of creating new ones)
    so every module that imported them keeps seeing the current data.
    Tests call this before each test.
    """
    STORY.clear()
    STORY.update(copy.deepcopy(_INITIAL_STORY))

    SCENES.clear()
    for scene in _INITIAL_SCENES:
        SCENES[scene["id"]] = copy.deepcopy(scene)

    CHOICES.clear()
    for number, (scene_id, text, next_scene_id) in enumerate(_INITIAL_CHOICES, start=1):
        choice_id = f"choice_{number}"
        CHOICES[choice_id] = {
            "id": choice_id,
            "scene_id": scene_id,
            "choice_text": text,
            "next_scene_id": next_scene_id,
        }

    COUNTERS["scene"] = len(SCENES)
    COUNTERS["choice"] = len(CHOICES)


reset_data()
