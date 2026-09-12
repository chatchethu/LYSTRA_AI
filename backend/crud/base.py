from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.base import Base
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID, user_id: Optional[UUID] = None) -> Optional[ModelType]:
        query = select(self.model).filter(self.model.id == id)
        if user_id and hasattr(self.model, "user_id"):
            query = query.filter(self.model.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100, filters: dict = None) -> List[ModelType]:
        query = select(self.model)
        if filters:
            for k, v in filters.items():
                query = query.filter(getattr(self.model, k) == v)
        result = await db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        obj_data = {c.name: getattr(db_obj, c.name) for c in db_obj.__table__.columns}
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID, user_id: Optional[UUID] = None) -> bool:
        obj = await self.get(db, id=id, user_id=user_id)
        if obj:
            await db.delete(obj)
            await db.commit()
            return True
        return False

    async def count(self, db: AsyncSession, *, filters: dict = None) -> int:
        query = select(func.count(self.model.id))
        if filters:
            for k, v in filters.items():
                query = query.filter(getattr(self.model, k) == v)
        result = await db.execute(query)
        return result.scalar_one()
