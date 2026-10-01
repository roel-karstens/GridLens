import jwt
import logging
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Dev mode: skip authentication (set via environment variable)
DEV_SKIP_AUTH = os.getenv("DEV_SKIP_AUTH", "false").lower() == "true"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """
    Extract and verify JWT token from request.

    Returns:
        user_id (str): The user ID from the token's 'sub' claim.

    Raises:
        HTTPException: 401 Unauthorized if token is invalid or missing.
    """
    # Dev mode: skip authentication
    if DEV_SKIP_AUTH:
        logger.warning("⚠️  DEV_SKIP_AUTH enabled - authentication bypassed")
        return "dev-user-123"

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        token = credentials.credentials
        # Decode without signature verification for now
        # In production, verify with Supabase public key
        payload = jwt.decode(
            token,
            key="",  # Key is ignored when verify_signature is False
            algorithms=["HS256", "RS256"],  # Try both algorithms (Supabase uses RS256)
            options={"verify_signature": False},
        )
        user_id: str | None = payload.get("sub")

        if not user_id:
            logger.warning("Token decoded but no 'sub' claim found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        logger.info(f"✅ Auth successful for user: {user_id}")
        return user_id
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
