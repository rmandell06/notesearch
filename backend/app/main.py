from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, connections, notes, search, voice

app = FastAPI(title="Notes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(connections.router, prefix="/connections", tags=["connections"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
