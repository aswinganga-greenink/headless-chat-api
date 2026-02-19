from typing import Protocol, BinaryIO

class StorageProvider(Protocol):
    """
    Interface for file storage operations.
    Supports Local Filesystem, S3, Azure Blob, etc.
    """

    async def upload(self, file: BinaryIO, filename: str, content_type: str) -> str:
        """
        Uploads a file and returns the storage key (or URL).
        
        Args:
            file: The file-like object.
            filename: Original filename.
            content_type: MIME type of the file.
            
        Returns:
            str: A unique key or path to retrieve the file.
        """
        ...

    async def download(self, key: str) -> BinaryIO:
        """
        Retrieves a file by its key.
        """
        ...

    async def delete(self, key: str) -> bool:
        """
        Deletes a file by its key.
        """
        ...
