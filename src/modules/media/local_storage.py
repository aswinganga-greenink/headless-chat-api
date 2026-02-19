import os
import aiofiles
import uuid
from typing import BinaryIO
from src.core.storage_interfaces import StorageProvider

class LocalFileStorage(StorageProvider):
    """
    Stores uploaded files in a local directory.
    Useful for development or single-node deployments.
    """
    
    def __init__(self, base_path: str = "media_uploads"):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    async def upload(self, file: BinaryIO, filename: str, content_type: str) -> str:
        """
        Saves the file to the local disk.
        Returns the filename (key).
        """
        # Generate a unique filename to prevent collisions
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(self.base_path, unique_name)
        
        # Use aiofiles for non-blocking I/O
        async with aiofiles.open(file_path, 'wb') as out_file:
            # If file is uploadfile it has .read(), if bytes it is just bytes
            # Handling generic BinaryIO might need reading chunks
            content = await file.read() 
            await out_file.write(content)
            
        return unique_name

    async def download(self, key: str) -> str:
        """
        For local storage, we just return the absolute path for `FileResponse` to handle,
        rather than reading bytes into memory.
        Protocol typings might need adjustment if we return path vs bytes.
        """
        file_path = os.path.join(self.base_path, key)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {key} not found")
        return file_path

    async def delete(self, key: str) -> bool:
        """
        Deletes the file from disk.
        """
        file_path = os.path.join(self.base_path, key)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
