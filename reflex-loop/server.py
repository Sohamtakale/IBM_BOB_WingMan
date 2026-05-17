# server.py
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import logging

try:
    from reflex_loop.memory import MemoryManager
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from memory import MemoryManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("server")

app = FastAPI(title="eFLEX LOOP Context Server")

# Allow CORS for local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate memory manager globally
memory = MemoryManager()

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI Server Started. Ready for media uploads.")

@app.post("/upload-context")
async def upload_context(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Receives an image, video, or audio file from the frontend."""
    
    # Save the file temporarily
    temp_dir = os.path.join(os.path.dirname(__file__), "..", "temp_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Determine type based on mime type
        media_type = "document"
        if file.content_type:
            if file.content_type.startswith("video"):
                media_type = "video"
            elif file.content_type.startswith("audio"):
                media_type = "audio"
            elif file.content_type.startswith("image"):
                media_type = "image"
        
        logger.info(f"Received upload: {file.filename} of type {media_type}")

        # Process the heavy ML extraction in the background so the API returns instantly
        background_tasks.add_task(memory.ingest_media, file_path, media_type)
        
        return {"status": "success", "message": f"Processing {media_type} in the background. The agent will remember this momentarily."}
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
