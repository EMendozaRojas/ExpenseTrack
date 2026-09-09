from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryDeleteResult, CategoryRead
from app.services.categorizer import uncategorized_category_id

router = APIRouter(prefix="/categories", tags=["categories"])


def _visible_category(db: Session, category_id: int, current_user: User) -> Category | None:
    return (
        db.query(Category)
        .filter(
            Category.id == category_id,
            or_(Category.owner_id.is_(None), Category.owner_id == current_user.id),
        )
        .first()
    )


def _to_read(category: Category, children: list[Category]) -> CategoryRead:
    return CategoryRead(
        id=category.id,
        name=category.name,
        owner_id=category.owner_id,
        parent_id=category.parent_id,
        kind=category.kind,
        icon=category.icon,
        color=category.color,
        is_system=category.is_system,
        is_fixed=category.is_fixed,
        created_at=category.created_at,
        children=[_to_read(child, []) for child in children],
    )


@router.get("/", response_model=list[CategoryRead])
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    kind: str | None = None,
) -> list[CategoryRead]:
    query = db.query(Category).filter(
        or_(Category.owner_id.is_(None), Category.owner_id == current_user.id)
    )
    if kind is not None:
        query = query.filter(Category.kind == kind)
    all_categories = query.order_by(Category.name).all()

    children_by_parent: dict[int, list[Category]] = {}
    for category in all_categories:
        if category.parent_id is not None:
            children_by_parent.setdefault(category.parent_id, []).append(category)

    roots = [c for c in all_categories if c.parent_id is None]
    return [_to_read(root, children_by_parent.get(root.id, [])) for root in roots]


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategoryRead:
    kind: str = payload.kind
    if payload.parent_id is not None:
        parent = _visible_category(db, payload.parent_id, current_user)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Categoría padre no encontrada"
            )
        if parent.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Una subcategoría no puede tener hijas",
            )
        kind = parent.kind

    existing = (
        db.query(Category)
        .filter(
            Category.owner_id == current_user.id,
            Category.parent_id == payload.parent_id,
            Category.name == payload.name,
            Category.kind == kind,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Ya existe una categoría con ese nombre"
        )

    category = Category(
        name=payload.name,
        owner_id=current_user.id,
        parent_id=payload.parent_id,
        kind=kind,
        icon=payload.icon,
        color=payload.color,
        is_system=False,
        is_fixed=payload.is_fixed,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return _to_read(category, [])


@router.delete("/{category_id}", response_model=CategoryDeleteResult)
def delete_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CategoryDeleteResult:
    category = (
        db.query(Category)
        .filter(Category.id == category_id, Category.owner_id == current_user.id)
        .first()
    )
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada"
        )

    new_parent_id = category.parent_id
    subcategories = db.query(Category).filter(Category.parent_id == category.id).all()
    for sub in subcategories:
        sub.parent_id = new_parent_id

    # Las transacciones nunca quedan apuntando a una categoría raíz: se
    # reasignan siempre a "Sin Clasificar" del kind correspondiente, tanto si
    # se borra una subcategoría como si se borra una raíz con movimientos
    # colgando directamente de ella (legado).
    fallback_id = uncategorized_category_id(db, category.kind)
    reassigned_transactions = (
        db.query(Transaction)
        .filter(Transaction.category_id == category.id)
        .update({"category_id": fallback_id}, synchronize_session=False)
    )

    db.delete(category)
    db.commit()

    return CategoryDeleteResult(
        reassigned_transactions=reassigned_transactions,
        reassigned_subcategories=len(subcategories),
    )
