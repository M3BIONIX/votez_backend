from datetime import timedelta
from fastapi import HTTPException, APIRouter, status, Depends

from core.depends import AsyncDBSession, AuthenticatedUser
from core.auth import verify_password, create_access_token
from core.settings import settings
from schemas.user_schema import UserCreate, UserLogin, AuthUser, Token
from crud.user_crud import user_crud as UserCrud



router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/register", response_model=AuthUser, status_code=status.HTTP_201_CREATED)
async def register(
    session: AsyncDBSession,
    user_data: UserCreate
):
    try:
        async with session.begin():
            existing_user = await UserCrud.get_user_by_email(session, user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Create new user
            user_dict = user_data.model_dump()
            user = await UserCrud.create_user(session, user_dict)
            
            return AuthUser(
                id=user.id,
                name=user.name,
                email=user.email,
                uuid=user.uuid,
                created_at=user.created_at
            )
    
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    session: AsyncDBSession,
    credentials: UserLogin
):
    """Authenticate user and return access token."""
    try:
        async with session.begin():
            user = await UserCrud.get_user_by_email(session, credentials.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if not verify_password(credentials.password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": str(user.uuid)},
                expires_delta=access_token_expires
            )
            
            return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate user: {str(e)}"
        )


@router.get("/me", response_model=AuthUser)
async def get_current_user_info(current_user: AuthenticatedUser):
    return AuthUser(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        uuid=current_user.uuid,
        created_at=current_user.created_at
    )

