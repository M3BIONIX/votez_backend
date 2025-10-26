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
                    updated_options = await PollOptionCrud.update_option_by_id(
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
            
            # Get creator UUID
            from models import UserModel
            from sqlalchemy import select
            creator_result = await session.execute(
                select(UserModel).where(UserModel.id == updated_poll.created_by)
            )
            creator = creator_result.scalars().first()

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
                "created_by_uuid": creator.uuid if creator else None,
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
            
            # Prepare options data
            new_options = [
                {
                    "option_name": opt.option_name,
                    "votes": 0,
                    "is_active": True
                }
                for opt in options_data.options
            ]
            
            # Add options to poll
            created_options = await PollOptionCrud.add_options_to_poll(session, existing_poll.id, new_options)
            
            # Flush to ensure options are created in database
            await session.flush()
            
            # Increment poll version
            existing_poll.version_id += 1
            await session.flush()
            
            # Clear cache to ensure fresh data
            session.expunge_all()
            
            # Get updated poll with all options
            updated_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            
            # Get creator UUID
            from models import UserModel
            from sqlalchemy import select
            creator_result = await session.execute(
                select(UserModel).where(UserModel.id == updated_poll.created_by)
            )
            creator = creator_result.scalars().first()
            
            options_list = [
                PollOptionSchema.model_validate(opt).model_dump(mode="json")
                for opt in updated_poll.poll_options
            ]
            
            # Get vote counts for summary
            vote_counts = await VoteCrud.get_vote_counts_by_poll(session, updated_poll.id)
            total_votes = sum(vote_counts.values())
            
            # Calculate percentages for each option
            option_percentages = {}
            if total_votes > 0:
                for opt in updated_poll.poll_options:
                    option_vote_count = vote_counts.get(opt.id, 0)
                    percentage = (option_vote_count / total_votes) * 100
                    option_percentages[str(opt.uuid)] = round(percentage, 2)
            else:
                for opt in updated_poll.poll_options:
                    option_percentages[str(opt.uuid)] = 0.0
            
            response_data = {
                "uuid": updated_poll.uuid,
                "title": updated_poll.title,
                "likes": updated_poll.likes,
                "created_at": updated_poll.created_at,
                "version_id": updated_poll.version_id,
                "created_by_uuid": creator.uuid if creator else None,
                "options": options_list
            }
            
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
                # Get creator UUID
                from sqlalchemy import select
                from models import UserModel
                creator_result = await session.execute(
                    select(UserModel).where(UserModel.id == poll.created_by)
                )
                creator = creator_result.scalars().first()
                
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
                    "created_by_uuid": creator.uuid if creator else None,
                    "options": options_list
                }
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
    """Soft delete options from an existing poll."""
    try:
        async with session.begin():
            # Verify poll exists and user owns it
            existing_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            if not existing_poll:
                raise HTTPException(status_code=404, detail="Poll not found")
            
            if existing_poll.created_by != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You don't have permission to delete options from this poll"
                )
            
            # Verify all option UUIDs belong to this poll
            from sqlalchemy import select
            from models import PollOptions
            
            # Get only active options for this poll
            existing_options_result = await session.execute(
                select(PollOptions)
                .where(PollOptions.poll_id == existing_poll.id)
                .where(PollOptions.is_active == True)
            )
            existing_options = existing_options_result.scalars().all()
            
            valid_option_uuids = [str(opt.uuid) for opt in existing_options]
            requested_uuids = [str(uuid) for uuid in delete_data.option_uuids]
            
            # Check if all requested UUIDs exist for this poll
            for uuid in requested_uuids:
                if uuid not in valid_option_uuids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Option with UUID {uuid} does not belong to this poll or is already deleted"
                    )
            
            # Soft delete the options
            deleted_count = await PollOptionCrud.soft_delete_options_by_uuids(
                session,
                requested_uuids
            )
            
            if deleted_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="No options were deleted"
                )
            
            # Increment poll version
            existing_poll.version_id += 1
            await session.flush()
            
            # Expunge all objects from session to clear cache
            session.expunge_all()
            
            # Get updated poll with remaining options
            updated_poll = await PollCrud.get_poll_by_uuid(session, poll_uuid)
            
            # Get creator UUID
            from models import UserModel
            from sqlalchemy import select
            creator_result = await session.execute(
                select(UserModel).where(UserModel.id == updated_poll.created_by)
            )
            creator = creator_result.scalars().first()
            
            options_list = [
                PollOptionSchema.model_validate(opt).model_dump(mode="json")
                for opt in updated_poll.poll_options
            ]
            
            # Get vote counts for summary
            vote_counts = await VoteCrud.get_vote_counts_by_poll(session, updated_poll.id)
            total_votes = sum(vote_counts.values())
            
            # Calculate percentages for each option
            option_percentages = {}
            if total_votes > 0:
                for opt in updated_poll.poll_options:
                    option_vote_count = vote_counts.get(opt.id, 0)
                    percentage = (option_vote_count / total_votes) * 100
                    option_percentages[str(opt.uuid)] = round(percentage, 2)
            else:
                for opt in updated_poll.poll_options:
                    option_percentages[str(opt.uuid)] = 0.0
            
            response_data = {
                "uuid": updated_poll.uuid,
                "title": updated_poll.title,
                "likes": updated_poll.likes,
                "created_at": updated_poll.created_at,
                "version_id": updated_poll.version_id,
                "created_by_uuid": creator.uuid if creator else None,
                "options": options_list
            }
            
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
            
            # Find the option by UUID and get its ID
            option_found = None
            for opt in existing_poll.poll_options:
                if opt.uuid == vote_data.option_uuid:
                    option_found = opt
                    break
            
            if not option_found:
                raise HTTPException(
                    status_code=404,
                    detail=f"Option {vote_data.option_uuid} not found for this poll"
                )
            
            # Check if user already voted
            existing_vote = await VoteCrud.get_vote(session, current_user.id, existing_poll.id)
            
            if existing_vote:
                # Update vote
                await VoteCrud.delete_vote(session, current_user.id, existing_poll.id)
            
            # Create new vote using option_id
            await VoteCrud.create_vote(
                session,
                current_user.id,
                existing_poll.id,
                option_found.id
            )
            
            await session.flush()
            
            # Reload poll to get fresh option data
            from models import PollOptions
            from sqlalchemy import select
            fresh_options_result = await session.execute(
                select(PollOptions)
                .where(PollOptions.poll_id == existing_poll.id)
                .where(PollOptions.is_active == True)
            )
            fresh_options = fresh_options_result.scalars().all()
            
            # Calculate summary after voting
            vote_counts = await VoteCrud.get_vote_counts_by_poll(session, existing_poll.id)
            total_votes = sum(vote_counts.values())
            
            # Calculate percentages for each option
            option_percentages = {}
            if total_votes > 0:
                for opt in fresh_options:
                    option_vote_count = vote_counts.get(opt.id, 0)
                    percentage = (option_vote_count / total_votes) * 100
                    option_percentages[str(opt.uuid)] = round(percentage, 2)
            else:
                for opt in fresh_options:
                    option_percentages[str(opt.uuid)] = 0.0
            
            # Create summary data
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
            
            # Broadcast vote update with summary to all connected clients
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
