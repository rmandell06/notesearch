import re

from app.services.supabase_client import supabase_client


def _tokens(text: str) -> set[str]:
    """Lowercased word tokens, length >= 3, punctuation stripped."""
    return set(re.findall(r"\b[a-z]{3,}\b", text.lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _assign_group(note_id: str) -> int:
    return (int(note_id.replace("-", ""), 16) % 4) + 1


class ConnectionsService:
    """Builds a Jaccard token-overlap graph over a user's notes.

    A simple stand-in until cosine similarity over real embeddings replaces
    it — the schema (nodes/links) is what the frontend graph view reads.
    """

    async def build_graph(self, user_id: str, threshold: float = 0.15) -> dict:
        client = await supabase_client.client()
        resp = await (
            client.table("notes")
            .select("id,title,content")
            .eq("user_id", user_id)
            .limit(50)
            .execute()
        )
        notes = resp.data or []
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
                    links.append(
                        {
                            "source": notes[i]["id"],
                            "target": notes[j]["id"],
                            "value": round(score, 3),
                        }
                    )

        return {"nodes": nodes, "links": links}


connections_service = ConnectionsService()
