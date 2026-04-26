"""
Auth Dependencies — Harness Engineering Security Layer.

Skills Applied:
- auth-implementation-patterns → JWT, session management
- backend-security-coder → OWASP-compliant auth
- api-security-best-practices → Error masking, no info leakage
"""

import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mmt.auth")

# Initialize Supabase Client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user object.

    Security hardening:
    - Internal errors are logged, not returned to client (OWASP A01)
    - Generic error message prevents information disclosure

    TODO: Switch to local JWT verification once JWT_SECRET is available.
          This eliminates the Supabase network round-trip per request.
    """
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        if not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_response.user
    except HTTPException:
        raise
    except Exception as e:
        # Log the real error internally, never expose stack traces
        logger.error("Authentication verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_fpso(user=Depends(get_current_user)):
    """Extract FPSO context from user token to enforce RBAC (Rule 01: Tenant Isolation).
    
    Returns a dict with 'user' and 'fpso_name'.
    """
    fpso_name = None
    if isinstance(user, dict):
        # Mock user during tests
        fpso_name = user.get("fpso_name")
    elif hasattr(user, "user_metadata"):
        # Supabase User object
        fpso_name = user.user_metadata.get("fpso_name")
        
    # In strict mode, we could raise 403 if fpso_name is missing, 
    # but some global admins might not have one. 
    return {
        "user": user,
        "fpso_name": fpso_name
    }
