import os
os.environ["TRANSFORMERS_VERIFIED_SSL"] = "false"

import glob
import pickle
import faiss
from django.core.management import BaseCommand
from sentence_transformers import SentenceTransformer

MODEL_PATH =  "models/all-MiniLM-L6-v2"

class Command(BaseCommand):
    help = "Index documentation into FAISS"

    def handle(self, *args, **opts):
        print("Starting document indexing...")
        try:
            embedder = SentenceTransformer(MODEL_PATH)
        except Exception as e:
            print(f"Failed to load model: {e}")
            return

        texts, metadatas = [], []
        for path in glob.glob("docs/*.md"):
            content = open(path, encoding="utf-8").read()
            for i, chunk in enumerate(content.split("\n\n")):
                texts.append(chunk)
                metadatas.append({"source": os.path.basename(path), "chunk": i})

        embeddings = embedder.encode(texts, show_progress_bar=True)
        dim = embeddings.shape[1]
        index = faiss.IndexFlatL2(dim)
        index.add(embeddings)

        faiss.write_index(index, "faiss_index.bin")
        with open("doc_texts.pkl", "wb") as f:
            pickle.dump({"texts": texts, "metadatas": metadatas}, f)

        self.stdout.write(self.style.SUCCESS("Indexed docs successfully."))
