from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.investigation import (
    AccusationRequest, AccusationResponse, ClueCreate, ClueOut,
    ClueUpdate, DiscoverClueRequest, SuspectCreate, SuspectOut, SuspectUpdate
)
from app.services import investigation_service as service
from app.core.authorization import require_session_owner, require_admin

router = APIRouter(prefix="/api", tags=["Investigation"])


@router.get("/suspects", response_model=list[SuspectOut])
def list_suspects(db: Session = Depends(get_db)):
    return service.list_suspects(db)


@router.get("/suspects/{suspect_id}", response_model=SuspectOut)
def get_suspect(suspect_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_suspect(db, suspect_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/suspects", response_model=SuspectOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)],)
def create_suspect(payload: SuspectCreate, db: Session = Depends(get_db)):
    try:
        return service.create_suspect(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/suspects/{suspect_id}", response_model=SuspectOut,    dependencies=[Depends(require_admin)],)
def update_suspect(suspect_id: str, payload: SuspectUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_suspect(db, suspect_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/suspects/{suspect_id}", status_code=status.HTTP_204_NO_CONTENT,    dependencies=[Depends(require_admin)],)
def delete_suspect(suspect_id: str, db: Session = Depends(get_db)):
    try:
        service.delete_suspect(db, suspect_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/clues", response_model=list[ClueOut])
def list_clues(
    importance: str | None = Query(default=None, pattern="^(low|medium|high)$"),
    location: str | None = None,
    db: Session = Depends(get_db),
):
    return service.list_clues(db, importance=importance, location=location)


@router.get("/clues/{clue_id}", response_model=ClueOut)
def get_clue(clue_id: str, db: Session = Depends(get_db)):
    try:
        return service.get_clue(db, clue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/clues", response_model=ClueOut, status_code=status.HTTP_201_CREATED,    dependencies=[Depends(require_admin)],)
def create_clue(payload: ClueCreate, db: Session = Depends(get_db)):
    try:
        return service.create_clue(db, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/clues/{clue_id}", response_model=ClueOut,    dependencies=[Depends(require_admin)],)
def update_clue(clue_id: str, payload: ClueUpdate, db: Session = Depends(get_db)):
    try:
        return service.update_clue(db, clue_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete(
    "/clues/{clue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
def delete_clue(clue_id: str, db: Session = Depends(get_db)):
    try:
        service.delete_clue(db, clue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/investigations/{session_id}/discover",
    response_model=ClueOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_session_owner)],
)
def discover_clue(session_id: str, payload: DiscoverClueRequest, db: Session = Depends(get_db)):
    try:
        return service.discover_clue(db, session_id, payload.clue_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post(
    "/investigations/{session_id}/accuse",
    response_model=AccusationResponse,
    dependencies=[Depends(require_session_owner)],
)
def accuse_suspect(session_id: str, payload: AccusationRequest, db: Session = Depends(get_db)):
    try:
        return service.accuse_suspect(db, session_id, payload.suspect_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
