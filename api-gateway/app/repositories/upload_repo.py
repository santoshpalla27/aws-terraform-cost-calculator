"""
Upload repository.
In-memory storage (database-ready architecture).
"""
from typing import Dict, Optional
from app.models.domain import Upload


class UploadRepository:
    """Repository for upload persistence."""
    
    def __init__(self):
        # In-memory storage (replace with database in production)
        self._uploads: Dict[str, Upload] = {}
    
    async def create(self, upload: Upload) -> Upload:
        """
        Create a new upload record.
        
        Args:
            upload: Upload object to store
            
        Returns:
            Created upload
        """
        self._uploads[upload.upload_id] = upload
        return upload
    
    async def get_by_id(self, upload_id: str) -> Optional[Upload]:
        """
        Get upload by ID.
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            Upload object or None if not found
        """
        return self._uploads.get(upload_id)
    
    async def delete(self, upload_id: str) -> bool:
        """
        Delete an upload.
        
        Args:
            upload_id: Upload identifier
            
        Returns:
            True if deleted, False if not found
        """
        if upload_id in self._uploads:
            del self._uploads[upload_id]
            return True
        return False


# Global repository instance
upload_repository = UploadRepository()
