# from fastapi import FastAPI
# from pydantic import BaseModel

# class User(BaseModel):
#     name:str
#     gender:str
#     age:int
#     id:int

# app = FastAPI()

# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get("/function1/{item_id}")
# def function1(item_id: int):
#     return {
#         "item_id": item_id,
#         "message":"This user has fetched the item with id: {}".format(item_id)}

# @app.get("/method1")
# def method1(name: str,age:int):
#     return {
#         "name":name,
#         "age":age
#     }

# db=[]

# @app.post("/post")
# def post(user:User):
#   db.append(user)
#   return {"message":"User added successfully", "user": user}

# @app.get("/get/{user_id}")
# def get_user(user_id:int):
#     for user in db:
#         if(user.id==user_id):
#             return {"message":"user found","user":user}
#     return {"message":"user not found"}

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.security import hash_password, verify_password
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @app.post("/users", response_model=schemas.UserResponse)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     return crud.create_user(db, user)

@app.get("/users", response_model=list[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

# Signup user endpoint
@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_pw = hash_password(user.password)
    db_user = models.User(
       firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        phone=user.phone,
        dateOfBirth=user.dateOfBirth,
        age=user.age,
        gender=user.gender,
        bloodGroup=user.bloodGroup,
        address=user.address,
        city=user.city,
        state=user.state,
        zipCode=user.zipCode,
        emergencyContactName=user.emergencyContactName,
        emergencyContactPhone=user.emergencyContactPhone,
        password=hashed_pw
    )
    db.add(db_user)
    db.commit()
    return {"message": "User created"}


from fastapi.security import OAuth2PasswordRequestForm

@app.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = crud.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/profile")
def profile(current_user: str = Depends(crud.get_current_user)):
    return {"email": current_user}

