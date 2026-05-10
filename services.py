from sqlalchemy.orm import Session
from fastapi import HTTPException
from passlib.context import CryptContext
import crud, validation

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def verify_password(plain_password, hashed_password):
        return pwd_context.verify(plain_password, hashed_password)

class UserService:
    @staticmethod
    def register(db: Session, data: validation.UserCreate):
        if crud.get_user_by_username(db, data.username):
            raise HTTPException(status_code=400, detail="Użytkownik już istnieje")
        hashed_password = pwd_context.hash(data.password)
        return crud.create_user(db, data.username, hashed_password)

    @staticmethod
    def get_all(db: Session):
        return crud.get_all_users(db)

    @staticmethod
    def get_by_id(db: Session, user_id: int):
        user = crud.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"Użytkownik o ID {user_id} nie istnieje")
        return user

    @staticmethod
    def update(db: Session, user_id: int, data: validation.UserUpdate, current_admin_id: int):
        user = UserService.get_by_id(db, user_id)
        
        # Logika: Admin nie może odebrać sobie uprawnień
        if user_id == current_admin_id and data.role == "user":
            raise HTTPException(status_code=400, detail="Nie możesz odebrać sobie roli administratora")
        
        updated_fields = data.model_dump(exclude_none=True)
        if not updated_fields:
            raise HTTPException(status_code=400, detail="Nie podano żadnych danych do aktualizacji")
        
        if "password" in updated_fields:
            updated_fields["hashed_password"] = pwd_context.hash(updated_fields.pop("password"))
        
        if "username" in updated_fields:
            existing = crud.get_user_by_username(db, updated_fields["username"])
            if existing and existing.id != user_id:
                raise HTTPException(status_code=400, detail="Nazwa użytkownika jest już zajęta")
        
        for field, value in updated_fields.items():
            setattr(user, field, value)
            
        return crud.update_user(db, user)

    @staticmethod
    def delete(db: Session, user_id: int, current_admin_id: int):
        if user_id == current_admin_id:
            raise HTTPException(status_code=400, detail="Nie możesz usunąć własnego konta")
        user = UserService.get_by_id(db, user_id)
        crud.delete_user(db, user)


class ProductService:
    @staticmethod
    def get_all(db: Session):
        return crud.get_all_products(db)

    @staticmethod
    def get_by_id(db: Session, product_id: int):
        product = crud.get_product(db, product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Produkt o ID {product_id} nie istnieje")
        return product

    @staticmethod
    def create(db: Session, data: validation.ProductCreate):
        return crud.create_product(db, data.name, data.price)

    @staticmethod
    def update(db: Session, product_id: int, data: validation.ProductUpdate):
        product = ProductService.get_by_id(db, product_id)
        updated_fields = data.model_dump(exclude_none=True)
        if not updated_fields:
            raise HTTPException(status_code=400, detail="Nie podano żadnych danych do aktualizacji")
        
        for field, value in updated_fields.items():
            setattr(product, field, value)
        return crud.update_product(db, product)

    @staticmethod
    def delete(db: Session, product_id: int):
        product = ProductService.get_by_id(db, product_id)
        crud.delete_product(db, product)


class OrderService:
    @staticmethod
    def create(db: Session, data: validation.OrderCreate, user_id: int):
        ProductService.get_by_id(db, data.product_id) # Sprawdza czy produkt istnieje
        return crud.create_order(db, data.product_id, data.quantity, user_id)

    @staticmethod
    def update(db: Session, order_id: int, data: validation.OrderUpdate, user_id: int):
        order = crud.get_order(db, order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Zamówienie o ID {order_id} nie istnieje")
        order.quantity = data.quantity
        return crud.update_order(db, order)

    @staticmethod
    def delete(db: Session, order_id: int, user_id: int):
        order = crud.get_order(db, order_id, user_id)
        if not order:
            raise HTTPException(status_code=404, detail=f"Zamówienie o ID {order_id} nie istnieje")
        crud.delete_order(db, order)