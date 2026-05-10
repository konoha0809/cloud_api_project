# test.py
import crud

def test_password_hashing():
    password = "super-secret-password"
    hashed = crud.pwd_context.hash(password)
    
    assert hashed != password
    
    assert crud.verify_password(password, hashed) == True
    assert crud.verify_password("wrong-password", hashed) == False

print("Wszystkie testy zaliczone! (All tests passed!)")