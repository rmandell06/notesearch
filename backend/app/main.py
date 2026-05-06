from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth, connections, notes, search, voice

app = FastAPI(title="Notes API")

# CORS allow-list. Vercel preview URLs use a regex so feature-branch
# deploys at https://notesearch-three-<hash>-rmandell06.vercel.app keep
# working without a backend redeploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://notesearch-three.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_origin_regex=r"https://notesearch-three-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError):
    return JSONResponse(status_code=501, content={"detail": "Not implemented"})


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(notes.router, prefix="/notes", tags=["notes"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(connections.router, prefix="/connections", tags=["connections"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
