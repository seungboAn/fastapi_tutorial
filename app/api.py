from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@app.post("/upload-image/")
async def upload_image(file: UploadFile = File(...)):
    # 간단한 예시: 파일 이름 반환
    return {"filename": file.filename}

# 추가 API 엔드포인트 (필요에 따라 구현)
# - 이미지 업로드 및 저장
# - 얼굴 Segmentation (구현 생략)
# - 동물 캐릭터 합성 (구현 생략)
# - 생성 이력 저장 및 조회