# -*- coding: utf-8 -*-

import os
import json
import asyncio
import firebase_admin
from typing import Dict, Any, Optional, Union, AsyncGenerator
from contextlib import asynccontextmanager
from firebase_admin import credentials, db
from firebase_admin.exceptions import FirebaseError

from app.settings import log, CONFIG


class AsyncFirebase:
    """Asynchronous class to manage connections and operations with Firebase Realtime Database."""

    _instance = None
    _initialized = False
    key_file = CONFIG.FIREBASE.FIREBASE_CERT_FILE_PATH

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern to prevent multiple Firebase initializations."""
        if cls._instance is None:
            cls._instance = super(AsyncFirebase, cls).__new__(cls)
        return cls._instance

    def __init__(
            self,
            firebase_api_key: Union[Dict[str, Any], str] = CONFIG.FIREBASE.FIREBASE_API_KEY,
    ) -> None:
        """
        Initialize AsyncFirebase client.
        
        Args:
            firebase_api_key: Firebase API key as dict or JSON string
        """
        # only initialized once (part of singleton pattern)
        if not AsyncFirebase._initialized:
            self.firebase_api_key = firebase_api_key
            self.cred: Optional[credentials.Certificate] = None
            self._loop = asyncio.get_event_loop()
            
    async def _initialize_firebase(self):
        """Initialize Firebase app if not already initialized"""
        if not firebase_admin._apps and not self._initialized:
            try:
                if self.cred is None:
                    await self._load_credentials()
                
                if self.cred is None:
                    await log.async_error("Failed to load Firebase credentials")
                    raise ValueError("Firebase credentials could not be loaded")
                
                await log.async_info(f"Initializing Firebase with URL: {CONFIG.FIREBASE.FIREBASE_URL}")
                firebase_admin.initialize_app(self.cred, {
                    'databaseURL': CONFIG.FIREBASE.FIREBASE_URL
                })
                self._initialized = True
                await log.async_info("Firebase app initialized successfully")
            except Exception as e:
                await log.async_error(f"Error initializing Firebase: {e}")
                import traceback
                await log.async_error(traceback.format_exc())
                raise
                
    async def _load_credentials(self):
        """Load Firebase credentials from API key or key file"""
        try:
            if self.firebase_api_key and CONFIG.ENVIRONMENT != "localhost":
                if isinstance(self.firebase_api_key, str):
                    self.cred = credentials.Certificate(json.loads(self.firebase_api_key))
                else:
                    self.cred = credentials.Certificate(self.firebase_api_key)
            elif self.key_file:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(current_dir, '..', '..', '..', self.key_file)
                
                if not os.path.exists(file_path):
                    file_path = os.path.abspath(self.key_file)
                
                if not os.path.exists(file_path):
                    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
                    file_path = os.path.join(workspace_root, self.key_file)
                
                await log.async_info(f"Loading Firebase credentials from: {file_path}")
                
                if not os.path.exists(file_path):
                    await log.async_error(f"Firebase credentials file not found at: {file_path}")
                    raise FileNotFoundError(f"Firebase credentials file not found: {self.key_file}")
                
                self.cred = credentials.Certificate(file_path)
            else:
                await log.async_error("No Firebase credentials provided")
                raise ValueError("Firebase credentials are required")
        except Exception as e:
            await log.async_error(f"Error loading Firebase credentials: {e}")
            raise

    @asynccontextmanager
    async def get_reference(self, reference_path: str) -> AsyncGenerator[db.Reference, None]:
        """
        Async context manager for safely accessing Firebase references.
        
        Args:
            reference_path: Path to the Firebase reference
            
        Yields:
            Firebase DB reference for the specified path
            
        Raises:
            FirebaseError: If connection fails
        """
        try:
            # Initialize Firebase if not already initialized
            await self._initialize_firebase()

            ref = await asyncio.to_thread(db.reference, reference_path)
            yield ref

        except (FirebaseError, ValueError, json.JSONDecodeError) as e:
            await log.async_error(f"Firebase error for path '{reference_path}': {str(e)}")
            raise

    async def read(self, path: str) -> Dict[str, Any]:
        """
        Read data from Firebase
        
        Args:
            path: Path to read from
            
        Returns:
            Data at the specified path
        """
        try:
            await log.async_info(f"Reading from Firebase path: {path}")
            
            async with self.get_reference(path) as ref:
                data = await asyncio.to_thread(ref.get)
                
                if data is None:
                    await log.async_info(f"No data found at path: {path}")
                    return {}
                return data
        except Exception as e:
            await log.async_error(f"Error reading from Firebase: {str(e)}")
            return {}

    async def write(self, reference_path: str, data: Dict[str, Any]) -> bool:
        """
        Write data to Firebase reference path.
        
        Args:
            reference_path: Path to the Firebase reference
            data: Data to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.get_reference(reference_path) as ref:
                await asyncio.to_thread(ref.set, data)
                await log.async_info(f"Successfully wrote data to '{reference_path}'")
                return True
        except Exception as e:
            await log.async_error(f"Error writing to Firebase path '{reference_path}': {str(e)}")
            return False

    async def update(self, reference_path: str, data: Dict[str, Any]) -> bool:
        """
        Update data at Firebase reference path.
        
        Args:
            reference_path: Path to the Firebase reference
            data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.get_reference(reference_path) as ref:
                await asyncio.to_thread(ref.update, data)
                await log.async_info(f"Successfully updated data at '{reference_path}'")
                return True
        except Exception as e:
            await log.async_error(f"Error updating Firebase path '{reference_path}': {str(e)}")
            return False

    async def delete(self, reference_path: str) -> bool:
        """
        Delete data at Firebase reference path.
        
        Args:
            reference_path: Path to the Firebase reference
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with self.get_reference(reference_path) as ref:
                await asyncio.to_thread(ref.delete)
                await log.async_info(f"Successfully deleted data at '{reference_path}'")
                return True
        except Exception as e:
            await log.async_error(f"Error deleting Firebase path '{reference_path}': {str(e)}")
            return False

    async def ensure_default_entry(self, reference_path: str, default_data: Dict[str, Any]) -> bool:
        """
        Ensures a reference path exists with default data if it doesn't already exist.
        
        Args:
            reference_path: Path to check/create
            default_data: Default data to write if path doesn't exist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = await self.read(reference_path)
            if not data:
                success = await self.write(reference_path, default_data)
                if success:
                    await log.async_info(f"Created default entry at '{reference_path}'")
                return success
            else:
                await log.async_info(f"Default entry at '{reference_path}' already exists")
                return True
        except Exception as e:
            await log.async_error(f"Error ensuring default entry at '{reference_path}': {str(e)}")
            return False

    async def delete_exchange(self, exchange_id):
        """
        Delete an exchange from Firebase
        
        Args:
            exchange_id (str): The ID of the exchange to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reference_path = f"exchanges/{exchange_id}"
            success = await self.delete(reference_path)

            if success:
                await log.async_info(f"Successfully deleted exchange '{exchange_id}'")

            return success
        except Exception as e:
            await log.async_error(f"Error deleting exchange: {str(e)}")
            return False

    async def initialize(self):
        """Initialize Firebase app"""
        await self._initialize_firebase()
        await log.async_info("Firebase initialized successfully")

    async def test_connection(self):
        """Test the Firebase connection"""
        try:
            await self._initialize_firebase()
            async with self.get_reference("/") as ref:
                data = await asyncio.to_thread(ref.get)
                await log.async_info(f"Firebase connection test successful. Root data: {data}")
                return True
        except Exception as e:
            await log.async_error(f"Firebase connection test failed: {str(e)}")
            return False


async def test_async_firebase():
    """Test the AsyncFirebase implementation."""
    async_firebase = AsyncFirebase()

    # default entry creation
    await async_firebase.ensure_default_entry(
        "root", {"successful_connection_phrase": "Hello, world!"}
    )

    # read data
    # data = await async_firebase.read("root")
    # await log.async_info(f"Read data: {data}")

    # update data
    # await async_firebase.update("root", {"timestamp": asyncio.get_event_loop().time()})

    # updated_data = await async_firebase.read("root")
    # await log.async_info(f"Updated data: {updated_data}")


if __name__ == "__main__":
    asyncio.run(test_async_firebase())
