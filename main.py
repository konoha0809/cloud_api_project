from fastapi import FastAPI
import tables
import database_settings
from exceptions import setup_exception_handlers
from routers import router

tables.Base.metadata.create_all(bind=database_settings.engine)

app = FastAPI(title="Cloud Commerce API")

setup_exception_handlers(app)

app.include_router(router)