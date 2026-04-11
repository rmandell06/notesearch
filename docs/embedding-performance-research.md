embedding model performance research

looked at our embedding-model-test.py and found some bottlenecks. heres what i learned about speeding things up


BATCHING

right now we process chunks one at a time which is slow
- gpu loves parallel work, feeding it one thing at a time wastes cycles
- should batch multiple chunks together before calling the model
- sweet spot is usually 32-64 chunks per batch depending on memory
- saw 3-5x speedup in some benchmarks when batching properly


MODEL LOADING

the model loads fresh every time which takes forever
- all-MiniLM-L6-v2 is small but still ~90MB to load
- should load once at startup and reuse the same instance
- could also look into onnx runtime for faster inference
- onnx can be 2x faster than pytorch for inference only


CHUNKING IMPROVEMENTS

current chunking just splits by word count
- no overlap means we might cut off important context
- should add 10-20% overlap between chunks
- also might want to chunk by sentences instead of raw words
- langchain has a RecursiveCharacterTextSplitter thats supposed to be good


CACHING

were re-embedding the same text over and over
- should cache embeddings in the db after first computation
- only re-embed if the note content actually changes
- for search queries could use an LRU cache for common searches


VECTOR SEARCH

the linear scan through all vectors is O(n) which wont scale
- for small amounts of notes its fine but will get slow
- look into FAISS or Annoy for approximate nearest neighbor
- cloudflare vectorize should handle this for us in prod
- can also reduce embedding dimensions with PCA if needed


QUANTIZATION

could make the model smaller/faster with quantization
- int8 quantization cuts memory in half with minimal accuracy loss
- pytorch has built in quantization tools
- trade off accuracy for speed, need to test if its worth it


NEXT STEPS
- add batching to embed_list_of_chunks first, easiest win
- cache embeddings in supabase
- test onnx conversion
