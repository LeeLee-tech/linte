import os
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from matcher import build_matcher


class MatchInput(BaseModel):
    id: str = ""
    time_range: str
    content: str


class MatchRequest(BaseModel):
    my_profile: MatchInput
    candidates: List[MatchInput]


app = FastAPI(title="Linte Matcher Service")
engine = build_matcher()


@app.get("/health")
def health():
    return {"status": "ok", "engine": engine.name}


@app.post("/match")
def match(req: MatchRequest):
    if not req.candidates:
        return {"matches": []}

    try:
        matches = engine.match(
            (req.my_profile.id or "p1", req.my_profile.time_range, req.my_profile.content),
            [(item.id or f"c{i}", item.time_range, item.content) for i, item in enumerate(req.candidates)],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "matches": [
            {
                "id": item[0],
                "time": item[1],
                "content": item[2],
                "score": item[3] if len(item) > 3 else None,
                "level": item[4] if len(item) > 4 else "",
            }
            for item in matches
        ]
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("MATCHER_HOST", "0.0.0.0")
    port = int(os.getenv("MATCHER_PORT", "8010"))
    uvicorn.run(app, host=host, port=port)
