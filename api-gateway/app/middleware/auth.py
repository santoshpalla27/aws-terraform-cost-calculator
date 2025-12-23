"""
Authentication middleware.
Supports JWT and OIDC (pluggable).
"""
from typing import Optional
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.utils.security import SecurityUtils
from app.utils.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """Authentication middleware for JWT/OIDC."""
    
    def __init__(self):
        self.enabled = settings.auth_enabled
        self.security_utils = SecurityUtils(
            secret_key=settings.jwt_secret,
            algorithm=settings.jwt_algorithm
        )
    
    async def __call__(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials]):
        """
        Verify authentication for protected endpoints.
        
        Args:
            request: FastAPI request object
            credentials: HTTP Bearer credentials
            
        Raises:
            HTTPException: If authentication fails
        """
        # Skip auth if disabled
        if not self.enabled:
            request.state.user_id = "anonymous"
            return
        
        # Skip health endpoints
        if request.url.path.startswith('/health'):
            return
        
        # Require authentication
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token
        try:
            payload = self.security_utils.verify_token(credentials.credentials)
            
            # Extract user information
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Store user context in request state
            request.state.user_id = user_id
            request.state.token_payload = payload
            
            logger.info(f"Authenticated user: {user_id}")
        
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e


# Dependency for protected endpoints
async def get_current_user(request: Request) -> str:
    """
    Get current authenticated user from request state.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    # Return anonymous if auth is disabled
    if not settings.auth_enabled:
        return "anonymous"
    
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return request.state.user_id
