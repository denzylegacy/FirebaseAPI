# -*- coding: utf-8 -*-

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from typing import List, Optional
import uuid

from app.services.firebase_client.data_service import FirebaseDataService
from app.api.models.schemas import GenericItem, GenericItemCreate, GenericItemUpdate
from app.api.security.jwt import get_current_active_user
from app.settings import log

router = APIRouter()
data_service = FirebaseDataService()


@router.get("/{collection}", response_model=List[GenericItem])
async def get_all_items(
    collection: str = Path(..., description="Collection name in Firebase"),
    current_user = Depends(get_current_active_user)
):
    """
    Get all items from a collection
    
    Args:
        collection: Name of the collection in Firebase
        
    Returns:
        List of items in the collection
    """
    try:
        items = await data_service.get_all(collection)
        return items
    except Exception as e:
        await log.async_error(f"Error getting items from {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


@router.get("/{collection}/{item_id}", response_model=GenericItem)
async def get_item(
    collection: str = Path(..., description="Collection name in Firebase"),
    item_id: str = Path(..., description="ID of the item to retrieve"),
    current_user = Depends(get_current_active_user)
):
    """
    Get a specific item by ID
    
    Args:
        collection: Name of the collection in Firebase
        item_id: ID of the item to retrieve
        
    Returns:
        Item data
    """
    try:
        item = await data_service.get_by_id(collection, item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")
        return item
    except HTTPException:
        raise
    except Exception as e:
        await log.async_error(f"Error getting item {item_id} from {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


@router.post("/{collection}", response_model=GenericItem)
async def create_item(
    item: GenericItemCreate,
    collection: str = Path(..., description="Collection name in Firebase"),
    current_user = Depends(get_current_active_user)
):
    """
    Create a new item in a collection
    
    Args:
        collection: Name of the collection in Firebase
        item: Item data to create
        
    Returns:
        Created item data
    """
    try:
        # Generate ID if not provided
        item_id = item.id if item.id else str(uuid.uuid4())
        
        created_item = await data_service.create(collection, item_id, item.dict(exclude={"id"}))
        return created_item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log.async_error(f"Error creating item in {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@router.put("/{collection}/{item_id}", response_model=GenericItem)
async def update_item(
    item: GenericItemUpdate,
    collection: str = Path(..., description="Collection name in Firebase"),
    item_id: str = Path(..., description="ID of the item to update"),
    current_user = Depends(get_current_active_user)
):
    """
    Update an existing item
    
    Args:
        collection: Name of the collection in Firebase
        item_id: ID of the item to update
        item: Item data to update
        
    Returns:
        Updated item data
    """
    try:
        # Only include fields that are set (not None)
        update_data = {k: v for k, v in item.dict().items() if v is not None}
        
        updated_item = await data_service.update(collection, item_id, update_data)
        return updated_item
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await log.async_error(f"Error updating item {item_id} in {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")


@router.delete("/{collection}/{item_id}", response_model=dict)
async def delete_item(
    collection: str = Path(..., description="Collection name in Firebase"),
    item_id: str = Path(..., description="ID of the item to delete"),
    current_user = Depends(get_current_active_user)
):
    """
    Delete an item
    
    Args:
        collection: Name of the collection in Firebase
        item_id: ID of the item to delete
        
    Returns:
        Success message
    """
    try:
        await data_service.delete(collection, item_id)
        return {"message": f"Item {item_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await log.async_error(f"Error deleting item {item_id} from {collection}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}") 