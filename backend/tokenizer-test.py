import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel


class MockTokenizer:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2")

    def __call__(self, list_of_texts, padding=True, return_tensors="pt"):
        return self.tokenizer(list_of_texts, padding=padding, truncation=True, return_tensors=return_tensors)


class EmbeddingModel:
    def __init__(self):
        self.model = AutoModel.from_pretrained(
            "sentence-transformers/all-MiniLM-L6-v2")
        self.model.eval()

    def get_embeddings(self, token_ids, attention_mask):
        with torch.no_grad():
            model_output = self.model(
                input_ids=token_ids, attention_mask=attention_mask)

        all_token_embeddings = model_output.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).float()
        sum_of_embeddings = (all_token_embeddings * mask_expanded).sum(1)
        number_of_tokens = mask_expanded.sum(1)
        mean_pooled_embedding = sum_of_embeddings / number_of_tokens

        normalized_embedding = torch.nn.functional.normalize(
            mean_pooled_embedding, p=2, dim=1)
        return normalized_embedding


def split_text_into_chunks(text, words_per_chunk=100):
    all_words = text.split()
    chunks = [" ".join(all_words[start:start + words_per_chunk])
              for start in range(0, len(all_words), words_per_chunk)]
    return chunks


class EmbeddingService:
    def __init__(self):
        self.tokenizer = MockTokenizer()
        self.embedding_model = EmbeddingModel()

    def embed_list_of_chunks(self, list_of_chunks):
        tokenized_chunks = self.tokenizer(list_of_chunks)
        embeddings = self.embedding_model.get_embeddings(
            tokenized_chunks["input_ids"],
            tokenized_chunks["attention_mask"]
        )
        return embeddings.tolist()


class VectorStore:
    def __init__(self):
        self.stored_notes = {}

    def add_note(self, note_id, list_of_chunks, list_of_embeddings):
        self.stored_notes[note_id] = list(
            zip(list_of_chunks, list_of_embeddings))

    def find_similar_notes(self, query_embedding, number_of_results=3):
        query_vector = np.array(query_embedding)
        all_chunk_scores = []

        for note_id, chunks_and_embeddings in self.stored_notes.items():
            for chunk_text, chunk_embedding in chunks_and_embeddings:
                similarity_score = float(
                    np.dot(query_vector, np.array(chunk_embedding)))
                all_chunk_scores.append(
                    (similarity_score, note_id, chunk_text))

        all_chunk_scores.sort(reverse=True)
        return all_chunk_scores[:number_of_results]


def find_note_connections(vector_store, similarity_threshold=0.5, number_of_least_related=3):
    all_note_pairs = []
    list_of_notes = list(vector_store.stored_notes.items())

    for i, (note_id_a, chunks_a) in enumerate(list_of_notes):
        for note_id_b, chunks_b in list_of_notes[i + 1:]:
            average_embedding_a = np.mean(
                [embedding for _, embedding in chunks_a], axis=0)
            average_embedding_b = np.mean(
                [embedding for _, embedding in chunks_b], axis=0)
            similarity_between_notes = float(
                np.dot(average_embedding_a, average_embedding_b))
            all_note_pairs.append(
                (similarity_between_notes, note_id_a, note_id_b))

    all_note_pairs.sort(reverse=True)
    highly_connected_pairs = [
        (score, a, b) for score, a, b in all_note_pairs if score >= similarity_threshold]
    least_connected_pairs = list(
        reversed(all_note_pairs[-number_of_least_related:]))

    return highly_connected_pairs, least_connected_pairs


if __name__ == "__main__":
    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    notes = {
        "illini_1": "The top-seeded and top-ranked 1989 Illini were upset 83-81 in the Final Four on a last second basket by Michigan's Sean Higgins, ending the school's deepest run in the tournament at that time. Illinois had beaten the Wolverines by 12 and 16 points in two previous meetings that season.",
        "illini_2": "Weber's second year at Illinois, the 2004-05 season, will be remembered as one of the greatest in Fighting Illini history, finishing 37-2 as the National Runner-Up in the NCAA tournament. The Illini reeled off 29 straight wins to start the year.",
        "illini_3": "Down 15 points with around 4 minutes left, the Illini rallied with a run led by Luther Head and Deron Williams. The game was sent into overtime and the Illini pulled off a one-point win to advance to the 2005 Final Four in St. Louis.",
        "illini_4": "Deron Williams (No. 3, Utah Jazz) and Luther Head (No. 24, Houston Rockets) were taken in the first round of the 2005 NBA draft. Utah's selection of Williams at No. 3 overall in the 2005 lottery made him the highest-drafted player in Illinois history.",
        "illini_5": "The 2020-21 Illini went 16-4 in the B1G conference but had a worse record than Michigan (14-3), and therefore did not earn even a share of the title. Illinois had beaten Michigan by 23 without leading scorer Ayo Dosunmu in Ann Arbor.",
        "illini_6": "Gene Bartow would later sign a five-year contract to replace Schmidt in 1974, but he left after one season in which the Illini finished last place in the conference to replace John Wooden at UCLA.",
        "illini_7": "The Illini finished 1942-43 season with a 17-1 (12-0) record, winning their second-straight Big Ten title. Despite being ranked No. 1 in the nation, they opted not to play in the 1943 NCAA tournament after three of their five starters were called to duty in World War II.",
        "random_1": "Sourdough starter needs to be fed equal parts flour and water by weight every 24 hours. If you forget for a few days it gets a gray liquid on top called hooch, which just means it's hungry. Pour it off and feed it again.",
        "random_2": "The mitochondria produce ATP through oxidative phosphorylation across the inner membrane. Each glucose molecule nets about 30-32 ATP depending on the efficiency of the shuttle systems used.",
        "random_3": "Flight MH370 disappeared on March 8, 2014 with 239 people on board. Debris confirmed it crashed into the southern Indian Ocean but the main wreckage has never been found.",
        "random_4": "To change a bike tire: remove the wheel, deflate completely, use tire levers to pop one bead off the rim, pull out the tube, find the puncture, patch or replace, reseat the tire by hand, inflate slowly and check it doesn't bulge.",
        "random_5": "The Roman Colosseum could hold between 50,000 and 80,000 spectators. It was completed in 80 AD under Emperor Titus and featured a retractable awning called the velarium to shade the crowd.",
    }

    for note_id, note_text in notes.items():
        chunks = split_text_into_chunks(note_text)
        embeddings = embedding_service.embed_list_of_chunks(chunks)
        vector_store.add_note(note_id, chunks, embeddings)

    search_queries = [
        "illinois close losses in big moments",
        "illinois NBA draft picks",
        "food and cooking",
    ]

    for query_text in search_queries:
        print(f"\nquery: {query_text}")
        query_embedding = embedding_service.embed_list_of_chunks([query_text])[
            0]
        search_results = vector_store.find_similar_notes(
            query_embedding, number_of_results=3)
        for similarity_score, note_id, chunk_text in search_results:
            print(f"  [{similarity_score:.3f}] {note_id}: {chunk_text[:80]}")

    highly_connected, least_connected = find_note_connections(vector_store)

    print("\nconnections (threshold=0.5):")
    for similarity_score, note_id_a, note_id_b in highly_connected:
        print(f"  [{similarity_score:.3f}] {note_id_a} <-> {note_id_b}")

    print("\nleast related:")
    for similarity_score, note_id_a, note_id_b in least_connected:
        print(f"  [{similarity_score:.3f}] {note_id_a} <-> {note_id_b}")
