from typing import TypeVar, Generic, Type, Optional, List
from pymongo.collection import Collection
from pymongo.database import Database
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class MongoRepository(Generic[T]):
    def __init__(self, db: Database, collection_name: str, model_class: Type[T]):
        self.collection: Collection = db[collection_name]
        self.model_class = model_class

    def find_one(self, query: dict) -> Optional[T]:
        data = self.collection.find_one(query)
        if data:
            return self.model_class(**data)
        return None

    def find(self, query: dict, limit: int = 0) -> List[T]:
        cursor = self.collection.find(query)
        if limit > 0:
            cursor = cursor.limit(limit)
        return [self.model_class(**doc) for doc in cursor]

    def insert(self, entity: T, session=None) -> str:
        data = entity.model_dump()
        result = self.collection.insert_one(data, session=session)
        return str(result.inserted_id)

    def insert_many(self, entities: List[T], session=None) -> List[str]:
        data = [entity.model_dump() for entity in entities]
        result = self.collection.insert_many(data, session=session)
        return [str(id) for id in result.inserted_ids]

    def update(self, query: dict, entity: T, session=None) -> int:
        data = entity.model_dump()
        result = self.collection.update_one(query, {"$set": data}, session=session)
        return result.modified_count

    def delete(self, query: dict, session=None) -> int:
        result = self.collection.delete_many(query, session=session)
        return result.deleted_count
