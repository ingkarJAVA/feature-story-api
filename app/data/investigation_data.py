# In-memory content for the initial Shrek detective story.
# is_guilty is intentionally kept out of public Pydantic responses.
suspects = {
    "prince_charming": {
        "id": "prince_charming",
        "name": "Prince Charming",
        "description": "A prince who believes he deserves the throne.",
        "motive": "King Harold planned to change the line of succession.",
        "alibi": "Claims he remained in the grand hall after dinner.",
        "is_guilty": True,
    },
    "fairy_godmother": {
        "id": "fairy_godmother",
        "name": "Fairy Godmother",
        "description": "A powerful magical figure with influence over the royal family.",
        "motive": "Wanted to preserve her influence over the kingdom.",
        "alibi": "Claims she was in her laboratory.",
        "is_guilty": False,
    },
    "puss_in_boots": {
        "id": "puss_in_boots",
        "name": "Puss in Boots",
        "description": "A skilled swordsman who had a disagreement with the king.",
        "motive": "Had a personal argument with King Harold.",
        "alibi": "Claims he was in the stables.",
        "is_guilty": False,
    },
}

clues = {
    "poisoned_wine_glass": {
        "id": "poisoned_wine_glass",
        "name": "The Wine Glass",
        "description": "A glass with traces of a rare magical substance.",
        "location": "Royal Bedroom",
        "related_scene_id": "scene_2",
        "importance": "high",
    },
    "broken_royal_seal": {
        "id": "broken_royal_seal",
        "name": "Broken Royal Seal",
        "description": "The king's seal is damaged and has an unfamiliar scratch.",
        "location": "Royal Bedroom",
        "related_scene_id": "scene_2",
        "importance": "medium",
    },
    "missing_succession_document": {
        "id": "missing_succession_document",
        "name": "Succession Document",
        "description": "A royal document indicates that Harold planned to change succession.",
        "location": "Royal Library",
        "related_scene_id": "scene_7",
        "importance": "high",
    },
    "secret_passage": {
        "id": "secret_passage",
        "name": "Secret Passage",
        "description": "A concealed passage connects the laboratory area to the royal rooms.",
        "location": "Castle Corridor",
        "related_scene_id": "scene_9",
        "importance": "high",
    },
    "charming_letter": {
        "id": "charming_letter",
        "name": "Charming's Letter",
        "description": "A letter reveals Charming's plan to obtain the crown.",
        "location": "Prince's Chamber",
        "related_scene_id": "scene_10",
        "importance": "high",
    },
    "golden_fabric": {
        "id": "golden_fabric",
        "name": "Golden Fabric",
        "description": "A torn piece of golden fabric is found near the hidden passage.",
        "location": "Secret Passage",
        "related_scene_id": "scene_9",
        "importance": "medium",
    },
}
