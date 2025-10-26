from datetime import timedelta
from fastapi import HTTPException, APIRouter, status, Depends

from core.depends import AsyncDBSession, AuthenticatedUser
from core.auth import verify_password, create_access_token
from core.settings import settings
from schemas.user_schema import UserCreate, UserLogin, AuthUser, Token, UserMeResponse, VotedPollInfo
from crud.user_crud import user_crud as UserCrud
from crud.like_crud import like_crud as LikeCrud
from crud.vote_crud import vote_crud as VoteCrud
from crud.poll_crud import poll_crud as PollCrud
from crud.poll_option_crud import poll_option_crud as PollOptionCrud
from sqlalchemy.orm import joinedload



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
        existing_user = await UserCrud.get_user_by_email(session, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user_dict = user_data.model_dump()
        user = await UserCrud.create_user(session, user_dict)
        
        # Commit the transaction
        await session.commit()
        
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


@router.get("/me", response_model=UserMeResponse)
async def get_current_user_info(
    session: AsyncDBSession,
    current_user: AuthenticatedUser
):
    """Get current user info including liked polls and voted options."""
    try:
        async with session.begin():
            # Fetch liked poll UUIDs
            liked_poll_uuids = await LikeCrud.get_liked_polls_by_user(session, current_user.id)
            
            # Fetch votes with poll and option UUIDs
            votes = await VoteCrud.get_votes_by_user(session, current_user.id)
            
            # Build voted polls with summary data
            voted_polls = []
            for vote_row in votes:
                # Get poll by UUID with options loaded
                from models import Poll, PollOptions
                from sqlalchemy import select
                
                # Load poll with its options eagerly
                from sqlalchemy.orm import selectinload
                poll_result = await session.execute(
                    select(Poll)
                    .options(selectinload(Poll.poll_options))
                    .where(Poll.uuid == vote_row.poll_uuid)
                )
                poll = poll_result.scalars().first()
                
                if poll:
                    # Check if the voted option still exists and is active
                    option_exists_result = await session.execute(
                        select(PollOptions)
                        .where(PollOptions.uuid == vote_row.option_uuid)
                        .where(PollOptions.is_active == True)
                    )
                    voted_option = option_exists_result.scalars().first()
                    
                    # Only include this vote if the option still exists and is active
                    if not voted_option:
                        continue  # Skip this vote as the option was deleted
                    
                    # Get vote counts by option
                    vote_counts = await VoteCrud.get_vote_counts_by_poll(session, poll.id)
                    total_votes = sum(vote_counts.values())
                    
                    # Get all active options for this poll
                    options_result = await session.execute(
                        select(PollOptions)
                        .where(PollOptions.poll_id == poll.id)
                        .where(PollOptions.is_active == True)
                    )
                    poll_options = options_result.scalars().all()
                    
                    # Calculate percentages for each option
                    option_percentages = {}
                    if total_votes > 0:
                        for opt in poll_options:
                            option_vote_count = vote_counts.get(opt.id, 0)
                            percentage = (option_vote_count / total_votes) * 100
                            option_percentages[str(opt.uuid)] = round(percentage, 2)
                    else:
                        for opt in poll_options:
                            option_percentages[str(opt.uuid)] = 0.0
                    
                    voted_polls.append(
                        VotedPollInfo(
                            poll_uuid=vote_row.poll_uuid,
                            option_uuid=vote_row.option_uuid,
                            total_votes=total_votes,
                            summary=option_percentages
                        )
                    )
        
        return UserMeResponse(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            uuid=current_user.uuid,
            created_at=current_user.created_at,
            liked_poll_uuids=liked_poll_uuids,
            voted_polls=voted_polls
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user data: {str(e)}"
        )

