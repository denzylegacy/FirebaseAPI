# -*- coding: utf-8 -*-

from typing import Dict, Any, Optional, List, Union
from .async_firebase import AsyncFirebase
from app.settings import log


class FirebaseDataService:
    """Service layer for secure data operations with Firebase."""
    
    def __init__(self):
        self.firebase = AsyncFirebase()
    
    async def get_all(self, collection: str) -> List[Dict[str, Any]]:
        """
        Get all items from a collection.
        
        Args:
            collection: Collection name in Firebase
            
        Returns:
            List of items in the collection
        """
        try:
            data = await self.firebase.read(collection)
            if not data:
                return []
                
            # Convert Firebase object format to list
            return [{"id": key, **value} for key, value in data.items()]
        except Exception as e:
            await log.async_error(f"Error getting all items from {collection}: {str(e)}")
            raise
    
    async def get_by_id(self, collection: str, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific item by ID.
        
        Args:
            collection: Collection name in Firebase
            item_id: ID of the item to retrieve
            
        Returns:
            Item data or None if not found
        """
        try:
            data = await self.firebase.read(f"{collection}/{item_id}")
            if data:
                return {"id": item_id, **data}
            return None
        except Exception as e:
            await log.async_error(f"Error getting item {item_id} from {collection}: {str(e)}")
            raise
    
    async def create(self, collection: str, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new item.
        
        Args:
            collection: Collection name in Firebase
            item_id: ID for the new item
            data: Item data to save
            
        Returns:
            Created item data with ID
        """
        try:
            # Make a clean copy of the data without any ID field
            clean_data = {k: v for k, v in data.items() if k != "id"}
            
            # Check if already exists
            existing = await self.get_by_id(collection, item_id)
            if existing:
                raise ValueError(f"Item with ID {item_id} already exists in {collection}")
                
            success = await self.firebase.write(f"{collection}/{item_id}", clean_data)
            if not success:
                raise RuntimeError(f"Failed to create item in {collection}")
                
            return {"id": item_id, **clean_data}
        except Exception as e:
            await log.async_error(f"Error creating item in {collection}: {str(e)}")
            raise
    
    async def update(self, collection: str, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing item.
        
        Args:
            collection: Collection name in Firebase
            item_id: ID of the item to update
            data: New item data
            
        Returns:
            Updated item data with ID
        """
        try:
            # Make a clean copy of the data without any ID field
            clean_data = {k: v for k, v in data.items() if k != "id"}
            
            existing = await self.get_by_id(collection, item_id)
            if not existing:
                raise ValueError(f"Item with ID {item_id} not found in {collection}")
                
            success = await self.firebase.update(f"{collection}/{item_id}", clean_data)
            if not success:
                raise RuntimeError(f"Failed to update item in {collection}")
                
            return {"id": item_id, **clean_data}
        except Exception as e:
            await log.async_error(f"Error updating item in {collection}: {str(e)}")
            raise
    
    async def delete(self, collection: str, item_id: str) -> bool:
        """
        Delete an item.
        
        Args:
            collection: Collection name in Firebase
            item_id: ID of the item to delete
            
        Returns:
            True if successful, raises exception otherwise
        """
        try:
            existing = await self.get_by_id(collection, item_id)
            if not existing:
                raise ValueError(f"Item with ID {item_id} not found in {collection}")
                
            success = await self.firebase.delete(f"{collection}/{item_id}")
            if not success:
                raise RuntimeError(f"Failed to delete item in {collection}")
                
            return True
        except Exception as e:
            await log.async_error(f"Error deleting item in {collection}: {str(e)}")
            raise 