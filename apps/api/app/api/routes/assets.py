import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.asset import Asset
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate

router = APIRouter(prefix="/admin/assets", tags=["admin:assets"])


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> Asset:
    asset = Asset(**payload.model_dump())
    db.add(asset)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ativo já cadastrado para este mercado") from exc
    db.refresh(asset)
    return asset


@router.get("", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[Asset]:
    return db.query(Asset).order_by(Asset.symbol).all()


@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ativo não encontrado")
    return asset


@router.put("/{asset_id}", response_model=AssetRead)
def update_asset(
    asset_id: uuid.UUID,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ativo não encontrado")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ativo já cadastrado para este mercado") from exc
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ativo não encontrado")
    db.delete(asset)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Ativo possui sinais vinculados") from exc
