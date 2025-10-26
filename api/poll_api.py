from fastapi import HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from core.connection_manager import manager
from core.depends import AsyncDBSession
from schemas.poll_schema import CreatePollRequestSchema, PollOptionSchema, PollResponseSchema
from crud.poll_crud import poll_crud as PollCrud
from crud.poll_option_crud import poll_option_crud as PollOptionCrud


router = APIRouter(
    prefix="/poll",
)

@router.post("/", response_model=PollResponseSchema)
async def create_poll(session: AsyncDBSession, poll: CreatePollRequestSchema):
    try:
        async with session.begin():
            poll_data = {"title": poll.title, "likes": 0}
            created_poll = await PollCrud.create_poll(session, poll_data)

            options_data = [
                {
                    "poll_id": created_poll.id,
                    "option_name": opt.option_text,
                    "votes": 0
                }
                for opt in poll.options
            ]
            poll_options = await PollOptionCrud.create_options(session, options_data)
            
            # Convert SQLAlchemy objects to dicts for proper validation
            options_list = [
                PollOptionSchema.model_validate(opt).model_dump(mode="json")
                for opt in poll_options
            ]
            
            response_data = {
                "uuid": created_poll.uuid,
                "title": created_poll.title,
                "likes": created_poll.likes,
                "created_at": created_poll.created_at,
                "options": options_list
            }
        validated_response = PollResponseSchema.model_validate(response_data)
        await manager.broadcast({
            "type": "poll_created",
            "data": validated_response.model_dump(mode="json")
        })

        return validated_response

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create poll: {str(e)}")
