from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from contacts.schemas import ContactCreateSchema, ContactRead, DetailResponse
from contacts.views import add_contact, delete_contact, get_contacts
from database import get_db
from users.auth import get_current_user
from users.models import User


contacts_router = APIRouter(prefix="/contacts", tags=["Contacts"])


@contacts_router.get("/", response_model=list[ContactRead])
def contacts_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_contacts(db, current_user)


@contacts_router.post("/", response_model=ContactRead, status_code=201)
def create_contact(data: ContactCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return add_contact(data, db, current_user)


@contacts_router.delete("/{contact_id}", response_model=DetailResponse)
def remove_contact(contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_contact(contact_id, db, current_user)
