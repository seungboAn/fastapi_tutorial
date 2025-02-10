## FastAPI, PostgreSQL, Docker를 활용한 백엔드 개발 튜토리얼 (초보자용)

이 튜토리얼은 백엔드 개발 경험이 없는 분들을 대상으로, FastAPI, PostgreSQL, 그리고 Docker를 사용하여 간단한 CRUD (Create, Read, Update, Delete) API를 구축하는 과정을 단계별로 안내합니다. Velog 가이드에서 제시된 내용을 바탕으로 실습 과정을 자세히 설명합니다.
이 튜토리얼은 Docker를 중심으로 가상환경을 설정합니다. 따라서 uv를 활용한 가상환경 설정은 제외됩니다.

**목표:**

*   FastAPI를 사용하여 RESTful API를 구축합니다.
*   PostgreSQL 데이터베이스와 연동합니다.
*   Docker, Docker Compose를 활용하여 개발환경을 구축합니다.
*   Pydantic을 사용하여 데이터 유효성 검사를 수행합니다.
*   SQLAlchemy Core를 사용하여 데이터베이스 쿼리를 작성합니다.
*   테스트 코드를 작성합니다.
*   API 문서를 자동으로 생성합니다.

**사전 준비:**

*   Python 3.9 이상 설치
*   Docker 설치 및 실행
*   코드 편집기 (VS Code, PyCharm 등)

**프로젝트 구조:**

```
fastapi-postgresql-tutorial/      # 프로젝트 루트 디렉토리
├── app/                          # 애플리케이션 코드 디렉토리 (Velog 가이드와 일치)
│   ├── __init__.py
│   ├── api.py                    # API 엔드포인트 정의
│   ├── database.py               # 데이터베이스 연결 및 모델 정의
│   ├── models.py                 # 데이터베이스 테이블 모델 정의
│   ├── schemas.py                # Pydantic 스키마 정의
├── Dockerfile                   # Docker 이미지 설정
├── docker-compose.yml             # Docker Compose 설정
└── requirements.txt              # Python 의존성 목록
```

---

**1단계: 프로젝트 설정 및 Docker 환경 구축**

1.  프로젝트 디렉토리를 생성합니다.

    ```bash
    mkdir fastapi-postgresql-tutorial
    cd fastapi-postgresql-tutorial
    ```

2.  Docker 관련 파일을 생성합니다.

    *   **Dockerfile:**

        ```dockerfile
        FROM python:3.9-slim-buster

        WORKDIR /app

        COPY requirements.txt .

        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
        ```

    *   **docker-compose.yml:**

        ```yaml
        version: "3.8"
        services:
          web:
            build: .
            ports:
              - "8000:8000"
            depends_on:
              - db
            environment:
              DATABASE_URL: postgresql://fastapi:fastapi@db:5432/fastapi
          db:
            image: postgres:15
            environment:
              POSTGRES_USER: fastapi
              POSTGRES_PASSWORD: fastapi
              POSTGRES_DB: fastapi
            volumes:
              - db_data:/var/lib/postgresql/data

        volumes:
          db_data:
        ```

    *   **requirements.txt:** FastAPI 및 관련 의존성 명시 (uv pip 관련 설정은 velog 글에 없으므로 생략)

        ```
        fastapi==0.95.0
        uvicorn[standard]==0.21.1
        SQLAlchemy==2.0.0
        psycopg2-binary==2.9.6
        python-dotenv==1.0.0
        ```

3. Docker 이미지를 빌드하고 컨테이너를 실행합니다.
   ```bash
   docker-compose up --build
   ```

**2단계: 데이터베이스 연결 설정 (`app/database.py`)**

```python
# app/database.py
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_engine(DATABASE_URL)

metadata = MetaData()

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**3단계: 데이터베이스 모델 정의 (`app/models.py`)**

```python
# app/models.py
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.sql.sqltypes import DateTime
from app.database import Base
from sqlalchemy.sql.expression import text
from sqlalchemy import func

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**4단계: Pydantic 스키마 정의 (`app/schemas.py`)**

```python
# app/schemas.py
from typing import Optional
from pydantic import BaseModel

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class Item(ItemBase):
    id: int
    created_at: str # For simplicity, let's keep this as a string

    class Config:
        orm_mode = True
```

**5단계: API 엔드포인트 정의 (`app/api.py`)**

```python
# app/api.py
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/items/", response_model=schemas.Item)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/items/{item_id}", response_model=schemas.Item)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(models.Item).offset(skip).limit(limit).all()
    return items

@app.put("/items/{item_id}", response_model=schemas.Item)
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()

    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")

    for var, value in vars(item).items():
        if value is not None:
            setattr(db_item, var, value)

    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"ok": True}
```

**6단계: FastAPI 애플리케이션 설정 (`app/main.py`)**

```python
# app/main.py
from fastapi import FastAPI
from app import api
from app.database import engine, metadata
models.Base.metadata.create_all(bind=engine) #Database table create

app = FastAPI()

app.include_router(api.app)
```

**7단계: `main.py` 수정**
docker에서 실행할 수 있도록, 다음 코드로 수정합니다.
```python
from fastapi import FastAPI
from app import api
from app.database import engine, metadata
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=engine) #Database table create

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.app)
```

**8단계: .env 파일을 생성하고 환경변수를 설정**

```
DATABASE_URL=postgresql://fastapi:fastapi@db:5432/fastapi
```

**9단계: API 테스트**

1.  `docker-compose up --build` 명령어로 애플리케이션을 실행합니다.
2.  웹 브라우저에서 `http://localhost:8000/docs`에 접속하여 Swagger UI를 확인합니다.
3.  Swagger UI 또는 Postman과 같은 도구를 사용하여 API 엔드포인트를 테스트합니다.

**10단계: 데이터베이스 초기화**
`app/database.py` 에 명시된 `DATABASE_URL`을 기준으로, database를 생성하고, 테이블을 생성해야 합니다.
터미널에서 postgresql에 접속한 후 다음 명령어로 database를 생성합니다.

```bash
CREATE DATABASE fastapi;
CREATE USER fastapi WITH PASSWORD 'fastapi';
GRANT ALL PRIVILEGES ON DATABASE fastapi TO fastapi;
```
또는, `app/api.py` 에 있는 `models.Base.metadata.create_all(bind=engine)` 를 통해 table을 생성할 수 있습니다.

**핵심 요약:**

*   **Docker를 사용한 개발 환경 구축:** Docker Compose를 사용하여 FastAPI 애플리케이션과 PostgreSQL 데이터베이스를 컨테이너로 실행하여 개발 환경을 격리하고 일관성을 유지합니다.
*   **스키마 중심 개발:** Pydantic 모델을 사용하여 API 요청 및 응답 데이터의 구조를 정의하고 유효성을 검사합니다.
*   **의존성 주입:** FastAPI의 `Depends()`를 사용하여 데이터베이스 세션을 API 엔드포인트에 주입합니다. 이를 통해 코드의 재사용성과 테스트 용이성을 높입니다.
*   **SQLAlchemy:** SQLAlchemy를 사용하여 데이터베이스 테이블을 정의하고, ORM 기능을 활용하여 데이터베이스와 상호작용합니다.
*   **Swagger UI:** FastAPI는 Pydantic 모델과 경로 작동 데코레이터를 기반으로 Swagger UI 형식의 API 문서를 자동으로 생성합니다.

이 튜토리얼을 따라하면 FastAPI, PostgreSQL, 그리고 Docker를 사용하여 기본적인 CRUD API를 구축하는 방법을 이해할 수 있습니다. 이후에는 인증, 권한 부여, 로깅, 테스트 등 더 많은 기능을 추가하여 애플리케이션을 확장할 수 있습니다.