## FastAPI, PostgreSQL, UV를 활용한 백엔드 개발 튜토리얼 (초보자용)

이 튜토리얼은 백엔드 개발 경험이 없는 분들을 대상으로, FastAPI, PostgreSQL, UV를 사용하여 간단한 API를 구축하는 과정을 단계별로 안내합니다. 앞서 제시된 개발 규칙들을 준수하며, 실제 코드를 통해 실습해 볼 수 있도록 구성했습니다.

**목표:**

*   FastAPI를 사용하여 RESTful API를 구축합니다.
*   PostgreSQL 데이터베이스와 연동합니다.
*   UV를 사용하여 가상 환경 및 의존성을 관리합니다.
*   Pydantic을 사용하여 데이터 유효성 검사를 수행합니다.
*   SQLAlchemy Core를 사용하여 데이터베이스 쿼리를 작성합니다.
*   테스트 코드를 작성합니다.
*   API 문서를 자동으로 생성합니다.

**사전 준비:**

*   Python 3.9 이상 설치
*   `uv` 설치: `pip install uv` (또는 운영체제별 설치 방법 참고)
*   PostgreSQL 설치 및 실행 (또는 Docker를 사용하여 PostgreSQL 컨테이너 실행)
*   코드 편집기 (VS Code, PyCharm 등)
*   (선택 사항) Docker, Docker Compose

**프로젝트 구조:**

```
fastapi-postgresql-tutorial/      # 프로젝트 루트 디렉토리
├── src/                        # 소스 코드 디렉토리
│   ├── my_app/                 # 애플리케이션 패키지
│   │   ├── __init__.py
│   │   ├── api/                # API 라우터
│   │   │   ├── __init__.py
│   │   │   └── items.py       # Item 관련 API 엔드포인트
│   │   ├── database.py        # 데이터베이스 연결 설정
│   │   ├── main.py            # FastAPI 애플리케이션 진입점
│   │   ├── models/            # 데이터베이스 모델 (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   └── item.py
│   │   ├── schemas/           # Pydantic 스키마
│   │   │   ├── __init__.py
│   │   │   └── item.py
│   │   └── services/          # 서비스 로직
│   │       ├── __init__.py
│   │       └── item_service.py
│   └── tests/                # 테스트 코드
│        ├── __init__.py
│        └── test_items.py     # items.py에 대한 테스트 (예시)
├── pyproject.toml              # 프로젝트 메타데이터, 의존성
├── requirements.txt           # 프로덕션 의존성 (uv pip compile로 생성)
├── requirements-dev.txt       # 개발 의존성 (uv pip compile로 생성)
└── .env                       # 환경 변수 (선택 사항)
```

---

**1단계: 프로젝트 설정 및 가상 환경 생성**

1.  프로젝트 디렉토리를 생성합니다.
    ```bash
    mkdir fastapi-postgresql-tutorial
    cd fastapi-postgresql-tutorial
    ```

2.  `uv`를 사용하여 가상 환경을 생성합니다.
    ```bash
    uv venv
    ```
    *   `.venv` 디렉토리가 생성됩니다. (가상 환경)

3.  가상 환경을 활성화합니다.
    *   **Linux/macOS:**  `source .venv/bin/activate`
    *   **Windows:**  `.venv\Scripts\activate`

4.  프로젝트 구조에 따라 디렉토리와 빈 파일들을 생성합니다.

**2단계: 의존성 설치 (`uv pip install`)**

1.  `pyproject.toml` 파일을 생성하고, 다음 내용을 작성합니다.

    ```toml
    # pyproject.toml
    [project]
    name = "fastapi-postgresql-tutorial"
    version = "0.1.0"
    description = "A tutorial project for FastAPI and PostgreSQL"
    dependencies = [
        "fastapi>=0.95.0",          # FastAPI
        "uvicorn[standard]>=0.21.1", # ASGI 서버
        "databases[postgresql]>=0.7.0",  # 비동기 데이터베이스 라이브러리
        "asyncpg>=0.27.0",          # PostgreSQL 드라이버
        "sqlalchemy>=2.0.0",        # SQLAlchemy Core (또는 ORM)
        "pydantic>=1.10.0",        # 데이터 유효성 검사
        "python-dotenv>=1.0.0",   # 환경 변수 (선택 사항)
    ]

    [build-system]
    requires = ["setuptools", "wheel"]
    build-backend = "setuptools.build_meta"

    ```

2.  `uv pip compile`을 사용하여 의존성을 `requirements.txt`에 고정합니다.

    ```bash
    uv pip compile
    ```
    *   `requirements.txt` 파일이 생성됩니다.

3.  `uv pip sync`를 사용하여 의존성을 설치합니다.
    ```bash
    uv pip sync
    ```

**3단계: Pydantic 스키마 정의 (`src/my_app/schemas/item.py`)**

```python
# src/my_app/schemas/item.py
from typing import Optional
from pydantic import BaseModel, Field

class ItemBase(BaseModel):
    name: str = Field(..., title="Item Name", min_length=1)
    description: Optional[str] = Field(None, title="Item Description")
    price: float = Field(..., title="Price", gt=0)

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    name: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, gt=0)

class Item(ItemBase):
    id: int = Field(..., title="Item ID")

    class Config:
        orm_mode = True
```

**4단계: 데이터베이스 모델 정의 (`src/my_app/models/item.py`)**

```python
# src/my_app/models/item.py
import sqlalchemy
from ..database import metadata
from datetime import datetime

Item = sqlalchemy.Table(
    "items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    sqlalchemy.Column("name", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String),
    sqlalchemy.Column("price", sqlalchemy.Float, nullable=False),
    sqlalchemy.Column("created_at", sqlalchemy.DateTime, default=datetime.utcnow, nullable=False)
)

```

**5단계: 데이터베이스 연결 설정 (`src/my_app/database.py`)**

```python
# src/my_app/database.py
import databases
import sqlalchemy
import os
from dotenv import load_dotenv

load_dotenv() # .env 파일에서 환경변수를 불러옵니다.

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/mydatabase")

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL) # 동기 작업에 사용

async def connect_to_db():
    await database.connect()

async def disconnect_from_db():
    await database.disconnect()
```

**6단계: 서비스 로직 구현 (`src/my_app/services/item_service.py`)**

```python
# src/my_app/services/item_service.py
import databases
from typing import List, Optional
from ..models.item import Item
from ..schemas.item import ItemCreate, ItemUpdate, Item
from fastapi import Depends, HTTPException

class ItemService:
    def __init__(self, database: databases.Database = Depends(database)): # type: ignore
        self.db = database

    async def create_item(self, item: ItemCreate) -> Item:
        query = Item.insert().values(**item.dict())
        last_record_id = await self.db.execute(query)
        return Item(**item.dict(), id=last_record_id)

    async def get_item(self, item_id: int) -> Optional[Item]:
        query = Item.select().where(Item.c.id == item_id) # type: ignore
        result = await self.db.fetch_one(query)
        if result:
            return Item.from_orm(result)
        return None

    async def get_all_items(self) -> List[Item]:
         query = Item.select()
         results = await self.db.fetch_all(query)
         return [Item.from_orm(result) for result in results]

    async def update_item(self, item_id: int, item: ItemUpdate) -> Optional[Item]:
        # Check if the item exists
        existing_item = await self.get_item(item_id)
        if not existing_item:
            return None

        update_data = item.dict(exclude_unset=True)
        if not update_data:  # No fields to update
            return existing_item
        query = Item.update().where(Item.c.id == item_id).values(**update_data) # type: ignore
        await self.db.execute(query)
        return await self.get_item(item_id)

    async def delete_item(self, item_id: int) -> None:
        # Check if the item exists (optional, but good practice)
        existing_item = await self.get_item(item_id)
        if not existing_item:
            raise HTTPException(status_code=404, detail="Item not found")

        query = Item.delete().where(Item.c.id == item_id) # type: ignore
        await self.db.execute(query)

```

**7단계: API 라우터 구현 (`src/my_app/api/items.py`)**

```python
# src/my_app/api/items.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from ..schemas.item import ItemCreate, ItemUpdate, Item
from ..services.item_service import ItemService

router = APIRouter()

@router.post("/items/", response_model=Item, status_code=201)
async def create_item(item: ItemCreate, item_service: ItemService = Depends(ItemService)):
    return await item_service.create_item(item)

@router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int, item_service: ItemService = Depends(ItemService)):
    item = await item_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.get("/items/", response_model=List[Item])
async def get_all_items(item_service: ItemService = Depends(ItemService)):
    return await item_service.get_all_items()

@router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemUpdate, item_service: ItemService = Depends(ItemService)):
    updated_item = await item_service.update_item(item_id, item)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item

@router.delete("/items/{item_id}", status_code=204)
async def delete_item(item_id: int, item_service: ItemService = Depends(ItemService)):
    await item_service.delete_item(item_id)
    return {"message": "Item deleted successfully"}
```

**8단계: FastAPI 애플리케이션 설정 (`src/my_app/main.py`)**

```python
# src/my_app/main.py
from fastapi import FastAPI
from .api import items
from .database import connect_to_db, disconnect_from_db, engine, metadata

app = FastAPI()

# 데이터베이스 테이블 생성 (개발/테스트 환경에서만)
def create_tables():
    metadata.create_all(bind=engine)
create_tables()

# 이벤트 핸들러 (시작 시 DB 연결, 종료 시 연결 해제)
app.add_event_handler("startup", connect_to_db)
app.add_event_handler("shutdown", disconnect_from_db)

# API 라우터 등록
app.include_router(items.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

```

**9단계: 테스트 코드 작성 (`src/tests/test_items.py`)**

```python
# src/tests/test_items.py
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from src.my_app.main import app
from src.my_app.database import database
import databases
import sqlalchemy

# Use a test database URL
TEST_DATABASE_URL = "postgresql://user:password@localhost:5432/testdb" # Create a test database


# Fixture for the test database
@pytest.fixture(scope="session")
def test_db():
    test_engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    test_metadata = sqlalchemy.MetaData()
    test_metadata.create_all(bind=test_engine)  # Create tables
    test_db = databases.Database(TEST_DATABASE_URL)

    yield test_db  # Provide the database connection

    test_metadata.drop_all(bind=test_engine)  # Drop tables after tests


@pytest.fixture(scope="module")
def client(test_db):
    # Override the database dependency for testing
    async def override_get_db():
        try:
            await test_db.connect()
            yield test_db
        finally:
            await test_db.disconnect()

    app.dependency_overrides[database] = override_get_db # type: ignore

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()



def test_create_item(client):
    response = client.post("/items/", json={"name": "Test Item", "price": 10.99})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data


def test_get_item(client):
    # First, create an item to retrieve
    response = client.post("/items/", json={"name": "Another Item", "price": 5.50})
    assert response.status_code == status.HTTP_201_CREATED
    item_id = response.json()["id"]

    # Now, try to retrieve it
    response = client.get(f"/items/{item_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Another Item"
    assert data["id"] == item_id


def test_get_item_not_found(client):
    response = client.get("/items/9999")  # Assuming item 9999 doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_all_items(client):
     response = client.get("/items/")
     assert response.status_code == status.HTTP_200_OK
     assert isinstance(response.json(), list)

def test_update_item(client):
    post_response = client.post("/items/", json={"name": "Test update", "price": 20})
    assert post_response.status_code == status.HTTP_201_CREATED
    item_id = post_response.json()["id"]

    response = client.put(f"/items/{item_id}", json={"name": "Updated Item", "price": 11.99, "description": "des"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Item"
    assert data["description"] == "des"

    bad_response = client.put("/items/999", json={"name": "Updated Item", "price": 19.99})
    assert bad_response.status_code == status.HTTP_404_NOT_FOUND

def test_delete_item(client):
    response = client.post("/items/", json={"name": "Item delete", "price": 10.99})
    assert response.status_code == status.HTTP_201_CREATED
    item_id = response.json()["id"]

    delete_response = client.delete(f"/items/{item_id}")
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Check item not found
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

    bad_response = client.delete("/items/999")
    assert bad_response.status_code == status.HTTP_404_NOT_FOUND
```

**10단계: 개발 서버 실행 및 API 테스트**

1.  `uvicorn`을 사용하여 FastAPI 애플리케이션을 실행합니다.

    ```bash
    uvicorn src.my_app.main:app --reload
    ```

    *   `--reload`: 코드 변경 시 서버가 자동으로 재시작됩니다 (개발 편의 기능).

2.  웹 브라우저에서 `http://127.0.0.1:8000/docs`에 접속하여 Swagger UI를 확인합니다.  API 문서를 보고, 직접 API를 테스트해 볼 수 있습니다.

3.  Postman, curl 등의 도구를 사용하여 API를 테스트할 수도 있습니다.

4.  `pytest`를 사용하여 테스트 코드를 실행합니다.
    ```bash
    pytest src/tests
    ```

**11단계: (선택 사항) Docker Compose를 사용한 로컬 개발 환경**

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:  # FastAPI application
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/database  # Connect to the 'db' service
    depends_on:
      - db
    volumes:
          - ./src:/app/src # Live reloading

  db:  # PostgreSQL database
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: database
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```dockerfile
# Dockerfile
FROM python:3.9
WORKDIR /app

COPY pyproject.toml requirements*.txt ./
RUN pip install --no-cache-dir uv && uv pip install -r requirements.txt

COPY ./src /app/src

CMD ["uvicorn", "src.my_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```
docker compose up --build
```

**핵심 요약 및 추가 설명:**

*   **스키마 중심 개발:** Pydantic 모델을 사용하여 API 요청 및 응답 데이터의 구조를 정의하고 유효성을 검사합니다.
*   **의존성 주입:** `Depends()`를 사용하여 데이터베이스 연결(`database`)과 서비스 로직(`ItemService`)을 API 엔드포인트에 주입합니다. 이를 통해 코드의 재사용성과 테스트 용이성을 높입니다.
*   **비동기 처리:** `async` 및 `await` 키워드를 사용하여 데이터베이스 쿼리 등 I/O 작업을 비동기적으로 처리합니다.
*   **SQLAlchemy Core:** SQLAlchemy Core를 사용하여 데이터베이스 테이블을 정의하고, SQL 쿼리를 작성합니다.
*   **`databases` 라이브러리:** `databases`를 사용하여 FastAPI와 PostgreSQL 데이터베이스를 비동기적으로 연결합니다.
*   **테스트:** `pytest`와 FastAPI의 `TestClient`를 사용하여 API 엔드포인트를 테스트합니다.
* **uv를 활용한 관리**: `uv`를 통해 가상환경을 관리하고, 패키지 설치, 의존성 관리를 합니다.
*   **자동 문서 생성:** FastAPI는 Pydantic 모델과 경로 작동 데코레이터를 기반으로 Swagger UI 및 ReDoc 형식의 API 문서를 자동으로 생성합니다.

이 튜토리얼은 FastAPI, PostgreSQL, UV를 사용한 백엔드 개발의 기본적인 내용을 다룹니다.  실제 프로젝트에서는 더 많은 기능(인증, 권한 부여, 로깅, 에러 처리, 배포 등)이 필요할 수 있습니다. 하지만 이 튜토리얼을 통해 백엔드 개발의 핵심 개념과 흐름을 이해하고, 추가적인 학습을 위한 기반을 다질 수 있을 것입니다.
