import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta

import tables, validation, crud, database_settings


tables.Base.metadata.create_all(bind=database_settings.engine)

app = FastAPI(title="Cloud Commerce API")

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": "Wystąpił błąd serwera. Spróbuj ponownie później."})

@app.get("/products", response_model=list[validation.ProductOut])
def get_all_products(db: Session = Depends(database_settings.get_db)):
    return db.query(tables.Product).all()

@app.delete("/products/{product_id}", status_code=204)
def remove_product(product_id: int, db: Session = Depends(database_settings.get_db)):
    product = db.query(tables.Product).filter(tables.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Deleted successfully"}

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-2026")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database_settings.get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: raise HTTPException(status_code=401)
    except JWTError: raise HTTPException(status_code=401)
    user = crud.get_user_by_username(db, username=username)
    if user is None: raise HTTPException(status_code=401)
    return user

@app.post("/register")
def register(user: validation.UserCreate, db: Session = Depends(database_settings.get_db)):
    if crud.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="User already exists")
    return crud.create_user(db, user)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database_settings.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not crud.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Wrong credentials")
    return {"access_token": create_access_token({"sub": user.username}), "token_type": "bearer"}

@app.post("/products", response_model=validation.ProductOut)
def add_product(product: validation.ProductCreate, db: Session = Depends(database_settings.get_db)):
    return crud.create_product(db, product)

@app.post("/orders")
def make_order(order: validation.OrderCreate, db: Session = Depends(database_settings.get_db), current_user = Depends(get_current_user)):
    return crud.create_order(db, order, current_user.id)