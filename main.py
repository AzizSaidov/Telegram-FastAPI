from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine

from blocks import models as blocks_models
from contacts import models as contacts_models
from profiles import models as profiles_models
from users import models as users_models

from routers.blocks_routers import blocks_router
from routers.contacts_routers import contacts_router
from routers.profiles_routers import profiles_router
from routers.users_routers import users_router

Base.metadata.create_all(bind=engine)


app = FastAPI(title="Telegram FastAPI")


app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(users_router)
app.include_router(profiles_router)
app.include_router(contacts_router)
app.include_router(blocks_router)
