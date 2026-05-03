import re
import math
import logging
from app.services.supabase_client import supabase_client

logger = logging.getLogger(__name__)


def _tokens(text: str) -> set[str]:
    """Return lowercased word tokens, stripping punctuation."""
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def _assign_group(note_id: str) -> int:
    return (int(note_id.replace("-", ""), 16) % 4) + 1


class ConnectionsService:
    """Builds a word-overlap similarity graph over notes.

    Will be upgraded to cosine similarity once the custom Encoder
    from Embedding.py is trained and integrated.
    """

    def build_graph(self, user_id: str, threshold: float = 0.15) -> dict:
        notes = supabase_client.list_notes(user_id, limit=50)
        if not notes:
            return {"nodes": [], "links": []}

        token_sets = [_tokens(n.get("content", "")) for n in notes]

        nodes = [
            {"id": n["id"], "title": n["title"], "group": _assign_group(n["id"])}
            for n in notes
        ]

        links = []
        for i in range(len(notes)):
            for j in range(i + 1, len(notes)):
                score = _jaccard(token_sets[i], token_sets[j])
                if score >= threshold:
                    links.append({
                        "source": notes[i]["id"],
                        "target": notes[j]["id"],
                        "value": round(score, 3),
                    })

        return {"nodes": nodes, "links": links}


connections_service = ConnectionsService()
