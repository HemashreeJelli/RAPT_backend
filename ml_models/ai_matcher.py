from sentence_transformers import SentenceTransformer, util

class JobMatcher:
    def __init__(self):
        print("🔄 Loading MiniLM model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded!")

    def get_embedding(self, text: str):
        # Returns embedding tensor
        return self.model.encode(text, convert_to_tensor=True)

    def calculate_score(self, text1: str, text2: str):
        emb1 = self.get_embedding(text1)
        emb2 = self.get_embedding(text2)
        score = util.cos_sim(emb1, emb2).item()
        return round(score * 100, 2)

# Global singleton instance
matcher = JobMatcher()