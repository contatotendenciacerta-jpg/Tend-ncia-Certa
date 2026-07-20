import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_admin
from app.models.signal import Signal, SignalSource, SignalStatus
from app.models.signal_target import SignalTarget
from app.models.user import User
from app.schemas.signal import SignalCreate, SignalRead, SignalUpdate

router = APIRouter(prefix="/admin/signals", tags=["admin:signals"])


def _signal_query(db: Session):
    return db.query(Signal).options(joinedload(Signal.targets))


@router.post("", response_model=SignalRead, status_code=status.HTTP_201_CREATED)
def create_signal(
    payload: SignalCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
) -> Signal:
    data = payload.model_dump(exclude={"targets"})
    signal = Signal(**data, status=SignalStatus.PENDING)
    if payload.source == SignalSource.MANUAL:
        signal.created_by_admin_id = current_admin.id
    signal.targets = [SignalTarget(order=t.order, target_price=t.target_price) for t in payload.targets]
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


@router.get("", response_model=list[SignalRead])
def list_signals(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[Signal]:
    return _signal_query(db).order_by(Signal.created_at.desc()).all()


@router.get("/{signal_id}", response_model=SignalRead)
def get_signal(
    signal_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> Signal:
    signal = _signal_query(db).filter(Signal.id == signal_id).first()
    if signal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sinal não encontrado")
    return signal


@router.put("/{signal_id}", response_model=SignalRead)
def update_signal(
    signal_id: uuid.UUID,
    payload: SignalUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Signal:
    signal = _signal_query(db).filter(Signal.id == signal_id).first()
    if signal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sinal não encontrado")

    update_data = payload.model_dump(exclude_unset=True, exclude={"targets"})
    for field, value in update_data.items():
        setattr(signal, field, value)

    if payload.targets is not None:
        signal.targets = [SignalTarget(order=t.order, target_price=t.target_price) for t in payload.targets]

    db.commit()
    db.refresh(signal)
    return signal


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_signal(
    signal_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    signal = db.get(Signal, signal_id)
    if signal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sinal não encontrado")
    db.delete(signal)
    db.commit()
