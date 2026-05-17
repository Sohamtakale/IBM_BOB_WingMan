# memory.py
import os
import time
import chromadb
from chromadb.utils import embedding_functions
import google.generativeai as genai
import logging
import asyncio

logger = logging.getLogger(__name__)

# Fallback import for config
try:
    from reflex_loop import config
except ImportError:
    import config

class MemoryManager:
    """
    Multimodal Context Memory Manager.
    Acts as the sensory cortex, storing high-dimensional vectors of parsed video, audio, and images.
    """
    def __init__(self):
        logger.info("[MEMORY] Initializing Multimodal ChromaDB...")
        
        # Local chromadb storage
        db_path = os.path.join(os.path.dirname(__file__), "..", "local_memory")
        os.makedirs(db_path, exist_ok=True)
        from chromadb.config import Settings
        
        self.chroma_client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        self.collection = self.chroma_client.get_or_create_collection(
            name="user_context",
            embedding_function=self.embedding_fn
        )
        
        # Ensure Gemini is configured for vision/audio extraction
        api_key = getattr(config, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        else:
            logger.warning("[MEMORY] GEMINI_API_KEY not found. Media ingestion will fail.")

    def save_memory(self, text: str, role: str, metadata: dict = None):
        """Saves text or extracted media context to ChromaDB."""
        if not text.strip() or len(text) < 10: return
        
        doc_id = f"{role}_{os.urandom(4).hex()}"
        meta = {"role": role, "timestamp": str(time.time())}
        if metadata: 
            meta.update(metadata)
            
        self.collection.add(documents=[text], metadatas=[meta], ids=[doc_id])
        logger.debug(f"[MEMORY] Saved context: {text[:50]}...")

    async def _wait_for_file_active(self, uploaded_file):
        """Helper to wait for Google's backend to finish processing a video."""
        logger.info(f"[MEMORY] Waiting for media {uploaded_file.name} to process...")
        while True:
            file_info = genai.get_file(uploaded_file.name)
            if file_info.state.name == 'ACTIVE':
                return file_info
            elif file_info.state.name == 'FAILED':
                raise ValueError("Media processing failed in Gemini backend.")
            await asyncio.sleep(2)

    async def ingest_media(self, file_path: str, media_type: str):
        """Uploads media to Gemini, extracts the context, and saves it."""
        logger.info(f"[MEMORY] Processing {media_type} upload: {file_path}")
        
        loop = asyncio.get_running_loop()
        
        try:
            # 1. Upload to Gemini File API
            media_file = await loop.run_in_executor(None, genai.upload_file, file_path)
            
            # 2. Wait for processing (crucial for video)
            if media_type == "video":
                media_file = await self._wait_for_file_active(media_file)

            # 3. Extract rich context
            model = genai.GenerativeModel('gemini-2.5-flash')
            prompt = (
                "You are the sensory cortex and memory bank for an AI therapist and voice assistant. "
                f"Analyze this {media_type} in extreme detail. "
                "Describe exactly what is happening, the mood, objects, people, their expressions, "
                "and any text or audio events (like spoken words or background noises). "
                "Write it as a highly detailed, factual memory record for the user."
            )
            
            logger.info(f"[MEMORY] Extracting context via Gemini...")
            response = await loop.run_in_executor(None, model.generate_content, [media_file, prompt])
            description = response.text
            
            # 4. Save to vector DB
            self.save_memory(
                text=f"The user uploaded a {media_type}. Sensory extraction: {description}", 
                role="system_memory",
                metadata={"source": "media_upload", "type": media_type}
            )
            
            logger.info(f"[MEMORY] Media memory stored successfully.")
            return description
            
        except Exception as e:
            logger.error(f"[MEMORY] Error processing media: {e}")
        finally:
            # Clean up the local temp file
            try:
                os.remove(file_path)
            except OSError:
                pass

    def retrieve_context(self, current_query: str) -> str:
        """Retrieves top memories matching the current query."""
        if self.collection.count() == 0: 
            return ""
            
        try:
            results = self.collection.query(query_texts=[current_query], n_results=3)
            if results['documents'] and results['documents'][0]:
                merged = " ".join(results['documents'][0])
                if merged.strip():
                    return f"\n[RETRIEVED MULTIMODAL MEMORY]: {merged}"
        except Exception as e:
            logger.error(f"[MEMORY] Retrieval error: {e}")
            
        return ""
