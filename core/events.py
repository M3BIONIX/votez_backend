from sqlalchemy import event, update
from models import PollOptions, Poll


@event.listens_for(PollOptions, 'after_update')
def increment_poll_version_on_option_update(mapper, connection, target):
    """Increment parent Poll version_id when PollOptions is updated."""
    stmt = (
        update(Poll)
        .where(Poll.id == target.poll_id)
        .values(version_id=Poll.version_id + 1)
    )
    connection.execute(stmt)

@event.listens_for(PollOptions, 'after_insert')
def increment_poll_version_on_option_insert(mapper, connection, target):
    """Increment parent Poll version_id when new PollOptions is added."""
    stmt = (
        update(Poll)
        .where(Poll.id == target.poll_id)
        .values(version_id=Poll.version_id + 1)
    )
    connection.execute(stmt)
