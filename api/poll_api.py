from typing import List
from uuid import UUID

from fastapi import HTTPException, APIRouter

from core.connection_manager import manager
from core.depends import AsyncDBSession
from schemas.poll_schema import (
    CreatePollRequestSchema,
    PollOptionSchema,
    PollResponseSchema,
    UpdatePollRequestSchema, PollResponseWithVersionId
)
from crud.poll_crud import poll_crud as PollCrud
from crud.poll_option_crud import poll_option_crud as PollOptionCrud


router = APIRouter(
    prefix="/poll",
)

@router.post("/", response_model=PollResponseWithVersionId)
async def create_poll(session: AsyncDBSession, poll: CreatePollRequestSchema):
    try:
        async with session.begin():
            poll_data = {"title": poll.title, "likes": 0, "is_active": True}
            created_poll = await PollCrud.create_poll(session, poll_data)

            options_data = [
                {
                    "poll_id": created_poll.id,
                    "option_name": opt.option_text,
                    "votes": 0,
                    "is_active": True
                }
                for opt in poll.options
            ]
            poll_options = await PollOptionCrud.create_options(session, options_data)
            
            options_list = [
                PollOptionSchema.model_validate(opt).model_dump(mode="json")
                for opt in poll_options
            ]
            
            response_data = {
                "uuid": created_poll.uuid,
                "title": created_poll.title,
                "likes": created_poll.likes,
                "created_at": created_poll.created_at,
                "version_id": created_poll.version_id,
                "options": options_list
            }
        validated_response = PollResponseWithVersionId.model_validate(response_data)
        await manager.broadcast({
            "type": "poll_created",
            "data": validated_response.model_dump(mode="json")
        })

        return validated_response

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create poll: {str(e)}")

@router.put("/{poll_uuid}", response_model=PollResponseWithVersionId)
async def edit_poll(session: AsyncDBSession, poll_uuid: UUID, poll: UpdatePollRequestSchema):
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")

            if existing_poll.version_id != poll.version_id:
                raise HTTPException(status_code=409, detail="Poll version conflict")


            updated_options_map = {}
            if poll.options is not None:
                uuid_to_id_map = {opt.uuid: opt.id for opt in existing_poll.poll_options}

                uuid_to_version_id_map = {opt.uuid: opt.version_id for opt in existing_poll.poll_options}

                existing_option_uuids = set(uuid_to_id_map.keys())
                id_to_title_map = {}

                for opt in poll.options:
                    if opt.uuid not in existing_option_uuids:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Option with UUID {opt.uuid} does not belong to this poll"
                        )

                    if opt.version_id != uuid_to_version_id_map[opt.uuid]:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Option with UUID {opt.uuid} has version conflict"
                        )

                    option_id = uuid_to_id_map[opt.uuid]
                    id_to_title_map[option_id] = opt.option_text

                # Update options using ORM (triggers events)
                updated_options = await PollOptionCrud.update_option_by_id(
                    session,
                    list(id_to_title_map.keys()),
                    id_to_title_map
                )
                existing_poll.version_id +=1
                await session.flush()
                updated_options_map = {opt.id: opt for opt in updated_options}

            if poll.title is not None:
                existing_poll.title = poll.title
                existing_poll.version_id += 1
                await session.flush()

            updated_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)


            options_list = [
                PollOptionSchema.model_validate(opt).model_dump(mode="json")
                for opt in updated_poll.poll_options
            ]
            
            response_data = {
                "uuid": updated_poll.uuid,
                "title": updated_poll.title,
                "likes": updated_poll.likes,
                "created_at": updated_poll.created_at,
                "version_id": updated_poll.version_id,
                "options": options_list
            }
            
        validated_response = PollResponseWithVersionId.model_validate(response_data)
        
        await manager.broadcast({
            "type": "poll_updated",
            "data": validated_response.model_dump(mode="json")
        })
        
        return validated_response
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update poll: {str(e)}")

@router.get("/", response_model=List[PollResponseWithVersionId])
async def get_all_polls(session: AsyncDBSession):
    """
    Get all active polls with their active options.
    """
    try:
        async with session.begin():
            polls = await PollCrud.get_all_active_polls(session)
            
            response_list = []
            for poll in polls:
                options_list = [
                    PollOptionSchema.model_validate(opt).model_dump(mode="json")
                    for opt in poll.poll_options
                ]
                
                poll_data = {
                    "uuid": poll.uuid,
                    "title": poll.title,
                    "likes": poll.likes,
                    "created_at": poll.created_at,
                    "version_id": poll.version_id,
                    "options": options_list
                }
                response_list.append(PollResponseWithVersionId.model_validate(poll_data))
            
            return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch polls: {str(e)}")

@router.delete("/{poll_uuid}")
async def delete_poll(session: AsyncDBSession, poll_uuid: UUID):
    """
    Soft delete a poll by setting is_active to False for both the poll and its options.
    """
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            await PollOptionCrud.soft_delete_options_by_poll_id(session, existing_poll.id)
            await PollCrud.soft_delete_poll(session, existing_poll.id)
            
        await manager.broadcast({
            "type": "poll_deleted",
            "data": {"uuid": str(poll_uuid)}
        })
        
        return {"message": "Poll deleted successfully", "uuid": poll_uuid}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete poll: {str(e)}")
