from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.investigation import (
    AccusationRequest, AccusationResponse, ClueCreate, ClueOut,
    ClueUpdate, DiscoverClueRequest, SuspectCreate, SuspectOut, SuspectUpdate
)
from app.services import investigation_service as service

router = APIRouter(prefix="/api", tags=["Investigation"])


@router.get("/suspects", response_model=list[SuspectOut])
def list_suspects():
    return service.list_suspects()


@router.get("/suspects/{suspect_id}", response_model=SuspectOut)
def get_suspect(suspect_id: str):
    try:
        return service.get_suspect(suspect_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/suspects", response_model=SuspectOut, status_code=status.HTTP_201_CREATED)
def create_suspect(payload: SuspectCreate):
    try:
        return service.create_suspect(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/suspects/{suspect_id}", response_model=SuspectOut)
def update_suspect(suspect_id: str, payload: SuspectUpdate):
    try:
        return service.update_suspect(suspect_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/suspects/{suspect_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_suspect(suspect_id: str):
    try:
        service.delete_suspect(suspect_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/clues", response_model=list[ClueOut])
def list_clues(
    importance: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    location: str | None = None,
):
    return service.list_clues(importance=importance, location=location)


@router.get("/clues/{clue_id}", response_model=ClueOut)
def get_clue(clue_id: str):
    try:
        return service.get_clue(clue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/clues", response_model=ClueOut, status_code=status.HTTP_201_CREATED)
def create_clue(payload: ClueCreate):
    try:
        return service.create_clue(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/clues/{clue_id}", response_model=ClueOut)
def update_clue(clue_id: str, payload: ClueUpdate):
    try:
        return service.update_clue(clue_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/clues/{clue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clue(clue_id: str):
    try:
        service.delete_clue(clue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/investigations/{session_id}/discover",
    response_model=ClueOut,
    status_code=status.HTTP_201_CREATED,
)
def discover_clue(session_id: str, payload: DiscoverClueRequest):
    try:
        return service.discover_clue(session_id, payload.clue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/investigations/{session_id}/accuse",
    response_model=AccusationResponse,
)
def accuse_suspect(session_id: str, payload: AccusationRequest):
    try:
        return service.accuse_suspect(session_id, payload.suspect_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
