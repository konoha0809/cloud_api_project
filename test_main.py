import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database_settings import get_db
from tables import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield 
    Base.metadata.drop_all(bind=engine)

def test_register_user():
    """Test registration of a new user"""
    response = client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "testuser"
    assert "id" in data
    assert data["role"] == "user"


def test_register_existing_user():
    """Test registration with an already existing username"""
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )

    response = client.post(
        "/register",
        json={"username": "testuser", "password": "newpassword"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


def test_login_success():
    """Test successful login and token retrieval"""
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )

    # FastAPI OAuth2PasswordRequestForm expects form-data instead of JSON
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"}
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_create_product_without_auth():
    """Test product creation without authentication (should fail)"""
    response = client.post(
        "/products",
        json={"name": "Laptop", "price": 2500.0}
    )

    assert response.status_code == 401  # Unauthorized


def test_create_product_with_auth():
    """Test successful product creation by an authenticated user"""

    # Register and login
    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )

    login_res = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"}
    )

    token = login_res.json()["access_token"]

    # Create product with token in headers
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/products",
        json={"name": "Laptop", "price": 2500.0},
        headers=headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Laptop"
    assert data["price"] == 2500.0
    assert "id" in data


def test_create_order():
    """
    Integration test:
    registration -> login -> create product -> create order
    """

    client.post(
        "/register",
        json={"username": "testuser", "password": "testpassword"}
    )

    token = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword"}
    ).json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Create product
    prod_response = client.post(
        "/products",
        json={"name": "Mouse", "price": 50.0},
        headers=headers
    )

    product_id = prod_response.json()["id"]

    # Create order
    order_response = client.post(
        "/orders",
        json={"product_id": product_id, "quantity": 2},
        headers=headers
    )

    assert order_response.status_code == 201

    order_data = order_response.json()

    assert order_data["product_id"] == product_id
    assert order_data["quantity"] == 2