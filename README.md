# Cloud Commerce API

A simple REST API for an e-commerce platform built with FastAPI.  
The project includes authentication, user management (Admin CRUD), a product catalog, and an order management system.

---

## Technologies

- **Framework:** FastAPI
- **Database:** SQLAlchemy (SQLite by default)
- **Security:** JWT (`python-jose`), Passlib (`bcrypt`)
- **Validation:** Pydantic V2
- **Testing:** Pytest

---

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root directory:

```env
DATABASE_URL=sqlite:///./ecommerce.db
SECRET_KEY=your_super_secret_key
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Run the Server

```bash
uvicorn main:app --reload
```

After запуску, API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

---

## Features

- JWT authentication
- Password hashing with bcrypt
- Role-based access control (User / Admin)
- CRUD operations for products
- Order creation system
- Validation using Pydantic
- RESTful API architecture
- Interactive Swagger documentation

---

## Testing

Run unit tests with:

```bash
pytest
```

---

## Project Structure

```text
project/
│
├── main.py                 # Entry point, routes, exception handling
├── crud.py                 # Database business logic
├── tables.py               # SQLAlchemy models
├── validation.py           # Pydantic schemas
├── database_settings.py    # Database configuration
├── requirements.txt        # Project dependencies
├── .env                    # Environment variables
└── tests/                  # Unit tests
```

---

## API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```
