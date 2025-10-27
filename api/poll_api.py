from typing import List
from uuid import UUID
from fastapi import HTTPException, APIRouter, Depends

from core.connection_manager import manager
from core.depends import AsyncDBSession, AuthenticatedUser
from schemas.poll_schema import (
    CreatePollRequestSchema,
    PollOptionSchema,
    UpdatePollRequestSchema,
    PollResponseWithVersionId,
    VoteRequestSchema,
    AddPollOptionsRequestSchema,
    DeletePollOptionsRequestSchema,
    LikeResponseSchema,
    VoteResponseSchema,
    PollSummaryData
)
from crud.poll_crud import poll_crud as PollCrud
from crud.poll_option_crud import poll_option_crud as PollOptionCrud
from crud.like_crud import like_crud as LikeCrud
from crud.vote_crud import vote_crud as VoteCrud


router = APIRouter(
    prefix="/poll",
)

@router.post("/", response_model=PollResponseWithVersionId)
async def create_poll(
    session: AsyncDBSession,
    poll: CreatePollRequestSchema,
    current_user: AuthenticatedUser
):
    try:
        if current_user.id is None:
            raise HTTPException(status_code=500, detail="Unable to Get User Data")

        async with session.begin():
            poll_data = {
                "title": poll.title,
                "likes": 0,
                "is_active": True,
                "created_by": current_user.id,
            }
            created_poll = await PollCrud.create_poll(session, poll_data)

            await session.flush()

            options_data = [
                {
                    "poll_id": created_poll.id,
                    "option_name": opt.option_name,
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
                "created_by_uuid": current_user.uuid,
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
async def edit_poll(
    session: AsyncDBSession,
    poll_uuid: UUID,
    poll: UpdatePollRequestSchema,
    current_user: AuthenticatedUser
):
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")

            if existing_poll.created_by != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to edit this poll"
                )

            if existing_poll.version_id != poll.version_id:
                raise HTTPException(status_code=409, detail="Poll version conflict")

            if poll.options is not None:
                option_map = {opt.uuid: {
                    "id": opt.id,
                    "version_id": opt.version_id,
                    "option_name": opt.option_name
                }
                    for opt in existing_poll.poll_options}

                id_to_title_map = {}

                for opt in poll.options:
                    if opt.uuid not in option_map:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Option with UUID {opt.uuid} does not belong to this poll"
                        )

                    if opt.version_id != option_map[opt.uuid].get("version_id"):
                        raise HTTPException(
                            status_code=409,
                            detail=f"Option with UUID {opt.uuid} has version conflict"
                        )

                    # Get option ID
                    option_id = option_map[opt.uuid].get("id")
                    if option_id is None:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Failed to get option with UUID {opt.uuid}"
                        )
                    
                    # Only add to update map if the name has actually changed
                    if opt.option_name != option_map[opt.uuid]["option_name"]:
                        id_to_title_map[option_id] = opt.option_name

                # Only update options if there are actual changes
                if id_to_title_map:
                    await PollOptionCrud.update_option_by_id(
                        session,
                        list(id_to_title_map.keys()),
                        id_to_title_map
                    )
                    existing_poll.version_id += 1
                    await session.flush()

            if poll.title is not None and poll.title != existing_poll.title:
                existing_poll.title = poll.title
                existing_poll.version_id += 1
                await session.flush()

            updated_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            response_data = await PollCrud.build_poll_response_data(session, updated_poll)
            
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


@router.post("/{poll_uuid}/options", response_model=PollResponseWithVersionId)
async def add_options_to_poll(
    session: AsyncDBSession,
    poll_uuid: UUID,
    options_data: AddPollOptionsRequestSchema,
    current_user: AuthenticatedUser
):
    """Add new options to an existing poll."""
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            if existing_poll.created_by != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to add options to this poll"
                )
            
            new_options = [
                {
                    "option_name": opt.option_name,
                    "votes": 0,
                    "is_active": True
                }
                for opt in options_data.options
            ]
            
            await PollOptionCrud.add_options_to_poll(session, existing_poll.id, new_options)
            existing_poll.version_id += 1

            await session.flush()

            updated_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            
            response_data = await PollCrud.build_poll_response_data(session, updated_poll)
            
            total_votes, option_percentages = await VoteCrud.get_vote_percentages(
                session, updated_poll.id, updated_poll.poll_options
            )
            
        validated_response = PollResponseWithVersionId.model_validate(response_data)
        
        await manager.broadcast({
            "type": "poll_options_added",
            "data": {
                **validated_response.model_dump(mode="json"),
                "summary": {
                    "total_votes": total_votes,
                    "option_percentages": option_percentages
                }
            }
        })
        
        return validated_response
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add options to poll: {str(e)}")


@router.get("/", response_model=List[PollResponseWithVersionId])
async def get_all_polls(
    session: AsyncDBSession,
):
    try:
        async with session.begin():
            polls = await PollCrud.get_all_active_polls(session)
            
            response_list = []
            for poll in polls:
                poll_data = await PollCrud.build_poll_response_data(session, poll)
                response_list.append(PollResponseWithVersionId.model_validate(poll_data))
            
            return response_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch polls: {str(e)}")


@router.delete("/{poll_uuid}/options")
async def delete_poll_options(
    session: AsyncDBSession,
    poll_uuid: UUID,
    delete_data: DeletePollOptionsRequestSchema,
    current_user: AuthenticatedUser
):
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            if existing_poll.created_by != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete options from this poll"
                )
            
            # Validate and soft delete the options
            deleted_count = await PollOptionCrud.soft_delete_options_by_uuids_for_poll(
                session,
                existing_poll.id,
                delete_data.option_uuids
            )
            
            if deleted_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No valid options were found to delete. Options may not belong to this poll or are already deleted."
                )
            
            # Increment poll version
            existing_poll.version_id += 1
            await session.flush()
            
            # Expunge all objects from session to clear cache
            session.expunge_all()
            
            # Get updated poll with remaining options
            updated_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            
            # Build response data
            response_data = await PollCrud.build_poll_response_data(session, updated_poll)
            
            # Get vote percentages for summary
            total_votes, option_percentages = await VoteCrud.get_vote_percentages(
                session, updated_poll.id, updated_poll.poll_options
            )
            
        validated_response = PollResponseWithVersionId.model_validate(response_data)
        
        await manager.broadcast({
            "type": "poll_options_deleted",
            "data": {
                **validated_response.model_dump(mode="json"),
                "summary": {
                    "total_votes": total_votes,
                    "option_percentages": option_percentages
                }
            }
        })
        
        return validated_response
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete options: {str(e)}")


@router.delete("/{poll_uuid}")
async def delete_poll(
    session: AsyncDBSession,
    poll_uuid: UUID,
    current_user: AuthenticatedUser
):
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            # Check ownership
            if existing_poll.created_by != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete this poll"
                )
            
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


@router.post("/{poll_uuid}/like", response_model=LikeResponseSchema)
async def toggle_like(
    session: AsyncDBSession,
    poll_uuid: UUID,
    current_user: AuthenticatedUser
):
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            # Get current like state before toggling
            current_like = await LikeCrud.get_active_like(session, current_user.id, existing_poll.id)
            was_liked = current_like is not None
            
            # Toggle the like
            is_liked, like_record = await LikeCrud.toggle_like(session, current_user.id, existing_poll.id)
            
            # Update poll likes count
            if was_liked and not is_liked:
                existing_poll.likes -= 1
            elif not was_liked and is_liked:
                existing_poll.likes += 1
            
            await session.flush()
            
            response = LikeResponseSchema(
                poll_uuid=poll_uuid,
                user_id=current_user.id,
                is_liked=is_liked
            )
            
            # Broadcast like update to all connected clients
            await manager.broadcast({
                "type": "poll_liked" if is_liked else "poll_unliked",
                "data": {
                    "poll_uuid": str(poll_uuid),
                    "likes": existing_poll.likes,
                    "is_liked": is_liked
                }
            })
            
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to toggle like: {str(e)}")


@router.post("/{poll_uuid}/vote", response_model=VoteResponseSchema)
async def vote_on_poll(
    session: AsyncDBSession,
    poll_uuid: UUID,
    vote_data: VoteRequestSchema,
    current_user: AuthenticatedUser
):
    """Vote on a poll option and return summary. Requires authentication."""
    try:
        async with session.begin():
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            option_found = await PollOptionCrud.get_active_option_by_uuid_and_poll_id(
                session,
                str(vote_data.option_uuid),
                existing_poll.id
            )
            
            if not option_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"Option {vote_data.option_uuid} not found for this poll"
                )
            
            await VoteCrud.upsert_vote(
                session,
                current_user.id,
                existing_poll.id,
                option_found.id
            )
            
            await session.flush()
            
            fresh_options = await PollOptionCrud.get_active_options_by_poll_id(
                session,
                existing_poll.id
            )
            
            total_votes, option_percentages = await VoteCrud.get_vote_percentages(
                session, existing_poll.id, fresh_options
            )
            
            summary = PollSummaryData(
                total_votes=total_votes,
                option_percentages=option_percentages
            )
            
            response = VoteResponseSchema(
                message="Vote recorded successfully",
                poll_uuid=poll_uuid,
                option_uuid=vote_data.option_uuid,
                summary=summary
            )
            
            await manager.broadcast({
                "type": "poll_voted",
                "data": {
                    "poll_uuid": str(poll_uuid),
                    "total_votes": total_votes,
                    "summary": {
                        "total_votes": total_votes,
                        "option_percentages": option_percentages
                    }
                }
            })
            
            return response
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to record vote: {str(e)}")
