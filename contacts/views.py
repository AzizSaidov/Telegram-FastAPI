from fastapi import HTTPException
from sqlalchemy.orm import Session

from blocks.models import BlockedUser
from contacts.models import Contact
from contacts.schemas import ContactCreateSchema
from profiles.models import Profile
from users.models import User


def get_contacts(db: Session, current_user: User):
    return db.query(Contact).filter(Contact.owner_id == current_user.id).all()


def add_contact(data: ContactCreateSchema, db: Session, current_user: User):
    contact_profile = db.query(Profile).filter(Profile.username == data.username).first()

    if contact_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    contact_user = db.query(User).filter(User.id == contact_profile.user_id).first()

    if contact_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if contact_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot add yourself to contacts")

    blocked_by_me = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_user.id,
        BlockedUser.blocked_id == contact_user.id,
    ).first()

    if blocked_by_me:
        raise HTTPException(status_code=400, detail="You blocked this user")

    blocked_me = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == contact_user.id,
        BlockedUser.blocked_id == current_user.id,
    ).first()

    if blocked_me:
        raise HTTPException(status_code=403, detail="You cannot add this user")

    existing_contact = db.query(Contact).filter(
        Contact.owner_id == current_user.id,
        Contact.contact_id == contact_user.id,
    ).first()

    if existing_contact:
        raise HTTPException(status_code=400, detail="Contact already exists")

    new_contact = Contact(
        owner_id=current_user.id,
        contact_id=contact_user.id,
        name=data.name,
    )

    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)

    return new_contact


def delete_contact(contact_id: int, db: Session, current_user: User):
    contact = db.query(Contact).filter(
        Contact.id == contact_id,
        Contact.owner_id == current_user.id,
    ).first()

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()

    return {"detail": "Contact deleted successfully"}
