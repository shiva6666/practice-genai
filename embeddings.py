"""Task 1: make the warehouse real — embed sentences, measure meaning-distance."""
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

# ---- 1. THE NEW MUSCLE: text -> coordinates -------------------------------
def embed_texts(texts: list[str]) -> list[list[float]]:
    """One API call embeds the whole list. Returns one vector per text."""
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
    )
    return [e.values for e in result.embeddings]


# ---- 2. THE RULER: how close do two texts stand? ---------------------------
def cosine_similarity(a: list[float], b: list[float]) -> float:
    """1.0 = same direction (same meaning), 0.0 = unrelated, -1.0 = opposite."""
    dot = sum(x * y for x, y in zip(a, b))        # element-wise multiply, add up
    len_a = sum(x * x for x in a) ** 0.5          # vector "length" (sqrt of squares)
    len_b = sum(x * x for x in b) ** 0.5
    return dot / (len_a * len_b)


# ---- 3. THE VERIFICATION RITUAL --------------------------------------------
sentences = [
    "how do I log in to my account",              # a — the question
    "sign in with your username and password",    # b — same meaning, different words
    "the weather is nice today",                  # c — unrelated
    "quantum computing uses qubits",              # d — unrelated AND different domain
]

# ⚠️ BEFORE RUNNING: write your predicted ranking here.
#    e.g. "I predict sim(a,b) > sim(a,?) > sim(a,?) > sim(a,?)"
#    Then run and see if the numbers obey you.

vectors = embed_texts(sentences)
a, b, c, d = vectors

print(f"sim(a,b) = {cosine_similarity(a, b):.4f}   # login question vs sign-in sentence")
print(f"sim(a,c) = {cosine_similarity(a, c):.4f}   # login question vs weather")
print(f"sim(a,d) = {cosine_similarity(a, d):.4f}   # login question vs quantum")
print(f"sim(c,d) = {cosine_similarity(c, d):.4f}   # weather vs quantum (bonus)")