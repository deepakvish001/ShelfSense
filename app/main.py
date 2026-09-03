from fastapi import FastAPI

app = FastAPI(title="ShelfSense API", version="0.1.0")


@app.get("/healthz", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
