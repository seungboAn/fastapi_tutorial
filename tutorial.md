## 로컬 Docker, FastAPI, PostgreSQL 튜토리얼: 얼굴 Segmentation 및 동물 캐릭터 합성 서비스

이 튜토리얼은 로컬 환경에서 Docker, FastAPI, PostgreSQL을 사용하여 간단한 얼굴 Segmentation 및 동물 캐릭터 합성 서비스의 백엔드를 구축하는 방법을 안내합니다.  이 튜토리얼은 기본적인 API 엔드포인트를 만들고, 데이터베이스 연동을 설정하며, Docker를 사용하여 개발 환경을 격리하는 데 중점을 둡니다.

**목표:**

*   Docker Compose를 사용하여 FastAPI, PostgreSQL 환경 구축
*   FastAPI를 사용하여 API 엔드포인트 정의 (이미지 업로드, 결과 반환)
*   PostgreSQL 데이터베이스 연동 (사용자, 생성 이력 관리)
*   간단한 이미지 처리 (예: 이미지 크기 조정)

**사전 준비:**

*   Docker 설치 및 실행
*   Python 3.9 이상 설치
*   코드 편집기 (VS Code, PyCharm 등)

**프로젝트 구조:**

```
animal-avatar-service/
├── app/
│   ├── __init__.py
│   ├── api.py         # API 엔드포인트 정의
│   ├── database.py    # 데이터베이스 연결
│   ├── models.py      # 데이터베이스 모델 정의
│   ├── schemas.py     # Pydantic 스키마 정의
├── Dockerfile       # Docker 이미지 설정
├── docker-compose.yml # Docker Compose 설정
└── requirements.txt   # Python 의존성 목록
```

**1단계: 프로젝트 설정 및 Docker 환경 구축**

1.  프로젝트 디렉토리 생성:

    ```bash
    mkdir animal-avatar-service
    cd animal-avatar-service
    ```

2.  Docker 관련 파일 생성:

    *   `Dockerfile`:

        ```dockerfile
        FROM python:3.9-slim-buster

        WORKDIR /app

        COPY requirements.txt .

        RUN pip install --no-cache-dir -r requirements.txt

        COPY . .

        CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
        ```

    *   `docker-compose.yml`:

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
              DATABASE_URL: postgresql://user:password@db:5432/animal_avatar
          db:
            image: postgres:15
            environment:
              POSTGRES_USER: user
              POSTGRES_PASSWORD: password
              POSTGRES_DB: animal_avatar
            volumes:
              - db_data:/var/lib/postgresql/data

        volumes:
          db_data:
        ```

    *   `requirements.txt`:

        ```
        fastapi==0.95.0
        uvicorn[standard]==0.21.1
        SQLAlchemy==2.0.0
        psycopg2-binary==2.9.6
        python-multipart==0.0.5
        ```

3.  Docker 이미지 빌드 및 컨테이너 실행:

    ```bash
    docker-compose up --build
    ```

**2단계: 데이터베이스 연결 설정 (`app/database.py`)**

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/animal_avatar")  # 기본값 설정

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

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
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GenerationHistory(Base):
    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)  # 외래 키 설정 필요 (생략)
    image_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**4단계: Pydantic 스키마 정의 (`app/schemas.py`)**

```python
# app/schemas.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str

class User(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

class GenerationHistory(BaseModel):
    id: int
    user_id: int
    image_url: str
    created_at: str

    class Config:
        orm_mode = True
```

**5단계: API 엔드포인트 정의 (`app/api.py`)**

```python
# app/api.py
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
```

**6단계: 데이터베이스 초기화**

1.  Docker 컨테이너 접속:

    ```bash
    docker exec -it animal-avatar-service-db-1 bash  # 컨테이너 이름 확인 후 변경
    ```

2.  PostgreSQL 접속:

    ```bash
    psql -U user -d animal_avatar
    ```

3.  테이블 생성:

    ```sql
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE generation_history (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,  -- 외래 키 설정 필요
        image_url VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    ```

    또는 `app/api.py`에 `models.Base.metadata.create_all(bind=engine)`가 있으므로, 첫 API 호출 시 자동으로 테이블이 생성됩니다.

**7단계: API 테스트**

1.  애플리케이션 실행:

    ```bash
    docker-compose up --build
    ```

2.  웹 브라우저에서 `http://localhost:8000/docs`에 접속하여 Swagger UI를 확인합니다.

3.  Swagger UI 또는 Postman을 사용하여 API 엔드포인트를 테스트합니다.

    *   `/users/` (POST): 사용자 생성
    *   `/users/` (GET): 사용자 목록 조회
    *   `/upload-image/` (POST): 이미지 업로드 (파일 업로드 테스트)

**핵심 요약:**

*   **Docker Compose**: FastAPI 애플리케이션과 PostgreSQL 데이터베이스를 컨테이너로 실행하여 개발 환경 격리
*   **FastAPI**: REST API 엔드포인트 정의, 데이터 유효성 검사
*   **SQLAlchemy**: 데이터베이스 모델 정의 및 쿼리 작성
*   **Swagger UI**: API 문서 자동 생성

**다음 단계:**

*   **이미지 처리**: OpenCV 또는 Pillow를 사용하여 이미지 크기 조정, 얼굴 감지 등 이미지 처리 기능 구현
*   **얼굴 Segmentation**: Rekognition 또는 다른 라이브러리를 사용하여 얼굴 영역 분리
*   **Bedrock 연동**: AWS Bedrock API를 호출하여 동물 캐릭터 합성 이미지 생성 (클라우드 환경 필요)
*   **데이터베이스 외래 키 설정**: `generation_history` 테이블에 `user_id` 외래 키 설정
*   **테스트 코드 작성**: API 엔드포인트 테스트 코드 작성
*   **더 자세한 오류 처리**: 예외 처리 및 로깅 강화
*   **보안 강화**: API 인증 및 권한 부여

이 튜토리얼은 기본적인 백엔드 구조를 제공하며, 추가 기능을 구현하여 서비스를 완성해 나갈 수 있습니다. 특히 이미지 처리, 얼굴 Segmentation, Bedrock 연동 부분은 실제 구현에 필요한 라이브러리 및 API 사용법을 익혀야 합니다.

추가 API까지 진행할거야. 얼굴 seg, 동물캐릭터 합성만 gcp 서비스를 쓰는 방식으로 구현할 수 있을까?

## 얼굴 Segmentation 및 동물 캐릭터 합성 기능 분리 (GCP 활용)

네, 가능합니다. 핵심 이미지 처리 로직(얼굴 Segmentation, 동물 캐릭터 합성)만 GCP 서비스를 활용하고, 나머지 부분은 로컬 Docker 환경에서 FastAPI 및 PostgreSQL로 구축하는 방식으로 구현할 수 있습니다. 이는 다음과 같은 장점을 가집니다.

*   **개발 환경 격리:** 로컬 환경에서 FastAPI, PostgreSQL 개발을 진행하여 의존성 관리 및 개발 편의성을 높입니다.
*   **GCP 서비스 활용:** 얼굴 Segmentation, 동물 캐릭터 합성 기능은 GCP의 강력한 API를 활용하여 품질과 성능을 확보합니다.
*   **비용 효율성:** 로컬 환경에서 개발하므로 개발 비용을 절감하고, 필요한 경우에만 GCP 서비스를 호출하여 사용량 기반 비용을 지불합니다.

**1. 변경된 인프라 구성**

```
+---------------------+      +---------------------+      +---------------------+      +---------------------+
|       Client        |----->|     API Gateway     |----->|       FastAPI        |----->|   Cloud Functions   |
+---------------------+      +---------------------+      +---------------------+      +---------------------+
                           |                       |      |                       |      |                       |
                           |                       |      |                       |      |  1. Face Segment   |
                           |                       |      |                       |      |  2. Animal Compose |
                           |                       |      |                       |      +---------------------+
                           |                       |      |                       |               ^
                           |                       |      |                       |               |
                           |                       |      |                       |      +---------------------+
                           |                       |      |                       |<------|    Cloud Vision API |
                           |                       |      |                       |      |   + Vertex AI    |
                           |                       |      |                       |      +---------------------+
                           |                       |      |                       |
                           |                       |      |   +-----------------+ |      +---------------------+
                           |                       |      |   |     Database      | |      |   Cloud Storage     |
                           |                       |      |   |   (PostgreSQL)  | |      +---------------------+
                           |                       |      |   +-----------------+ |       (Temp Image Storage)
                           +---------------------+      +---------------------+      +---------------------+
```

**설명:**

1.  **Client:** 웹 또는 앱 클라이언트가 이미지를 업로드합니다.
2.  **API Gateway:** 클라이언트 요청을 받아 인증을 처리하고 FastAPI 서버로 요청을 라우팅합니다.
3.  **FastAPI**: 로컬 Docker 환경에서 실행되는 API 서버입니다.
    *   이미지 업로드, 사용자 관리, 생성 이력 관리 등을 처리합니다.
    *   얼굴 Segmentation 및 동물 캐릭터 합성 요청을 Cloud Functions로 전달합니다.
    *   Cloud Functions에서 결과 이미지를 받아 클라이언트에게 반환합니다.
4.  **Cloud Functions**: GCP에서 실행되는 서버리스 함수입니다.
    *   Cloud Vision API를 사용하여 얼굴 Segmentation을 수행합니다.
    *   Vertex AI (또는 다른 이미지 생성 모델)를 사용하여 동물 캐릭터 합성을 수행합니다.
    *   결과 이미지를 Cloud Storage에 임시 저장합니다.
    *   Cloud Storage에 저장된 이미지 URL을 FastAPI 서버에게 반환합니다.
5.  **PostgreSQL**: 로컬 Docker 환경에서 실행되는 데이터베이스입니다. 사용자 정보, 생성 이력 등을 저장합니다.
6.  **Cloud Storage**: Cloud Functions에서 생성된 이미지를 임시로 저장합니다.
7.  **Cloud Vision API**: 얼굴 Segmentation을 수행합니다.
8.  **Vertex AI (또는 다른 이미지 생성 모델)**: 동물 캐릭터 합성을 수행합니다.

**2. 수정된 구현 단계**

1.  **로컬 개발 환경 설정:**
    *   이전 튜토리얼을 따라 Docker, FastAPI, PostgreSQL 환경을 구축합니다.
2.  **GCP 설정:**
    *   GCP 프로젝트 생성 및 Cloud Vision API, Vertex AI API 활성화
    *   Cloud Functions 배포를 위한 IAM 권한 설정
    *   Cloud Storage 버킷 생성 (임시 이미지 저장)
3.  **Cloud Functions 개발:**
    *   Cloud Vision API를 사용하여 얼굴 Segmentation 수행
    *   Vertex AI (또는 다른 이미지 생성 모델)를 사용하여 동물 캐릭터 합성
    *   결과 이미지를 Cloud Storage에 임시 저장 및 URL 반환
4.  **FastAPI 수정:**
    *   이미지 업로드 엔드포인트 수정: 업로드된 이미지를 Cloud Functions로 전송하고, 결과 URL을 받아 클라이언트에게 반환
    *   데이터베이스 연동 코드 추가: 생성 이력을 데이터베이스에 저장
    *   오류 처리 및 로깅 강화

**3. 코드 수정 예시**

*   **`app/api.py` (FastAPI)**

```python
from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import httpx  # 외부 API 호출 라이브러리

from . import models, schemas
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ... (기존 코드)

CLOUD_FUNCTIONS_URL = "YOUR_CLOUD_FUNCTIONS_URL"  # Cloud Functions URL

@app.post("/generate-animal-avatar/")
async def generate_animal_avatar(file: UploadFile = File(...)):
    # 1. 이미지 파일을 Cloud Functions로 전송
    files = {"image": (file.filename, file.file, file.content_type)}
    async with httpx.AsyncClient() as client:
        response = await client.post(CLOUD_FUNCTIONS_URL, files=files)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="GCP Cloud Functions 오류")

    # 2. Cloud Functions로부터 결과 URL 받기
    result = response.json()
    image_url = result.get("image_url")

    if not image_url:
        raise HTTPException(status_code=500, detail="Cloud Functions에서 이미지 URL을 반환하지 않음")

    # 3. 데이터베이스에 이력 저장 (예시)
    # ... (데이터베이스 연동 코드)

    # 4. 클라이언트에게 이미지 URL 반환
    return {"image_url": image_url}
```

*   **Cloud Functions (Python)**

```python
from google.cloud import storage
from google.cloud import vision  # Cloud Vision API
# from google.cloud import aiplatform # Vertex AI 필요 시

import os
from io import BytesIO

def generate_animal_avatar(request):
    """HTTP Cloud Function."""
    if request.method == 'POST':
        # 1. 이미지 파일 받기
        if 'image' not in request.files:
            return 'No image file uploaded.', 400

        image_file = request.files['image']
        image_content = image_file.read()

        # 2. Cloud Vision API를 사용하여 얼굴 Segmentation
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_content)
        response = client.face_detection(image=image)
        faces = response.face_annotations

        # 얼굴이 없는 경우
        if not faces:
            return 'No faces detected.', 400

        # 얼굴 정보 추출 (예시: bounding box)
        for face in faces:
            print('Face bounding box: {}'.format(face.bounding_poly))

        # 3. Vertex AI를 사용하여 동물 캐릭터 합성 (예시)
        # (Vertex AI API 호출 코드 - 프롬프트 생성, 이미지 생성 등)
        # (합성된 이미지를 image_data 변수에 저장)
        image_data = b"fake image data"  # Replace this with your actual generated image

        # 4. Cloud Storage에 이미지 저장
        storage_client = storage.Client()
        bucket_name = os.environ.get("CLOUD_STORAGE_BUCKET")  # Cloud Storage 버킷 이름
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f"animal_avatar_{image_file.filename}")

        blob.upload_from_string(
            image_data,
            content_type=image_file.content_type
        )

        image_url = f"https://storage.googleapis.com/{bucket_name}/{blob.name}"

        # 5. 결과 반환
        return {'image_url': image_url}, 200
    else:
        return 'Only POST requests are accepted.', 405
```

**4. 장점 및 고려 사항**

*   **장점:**
    *   로컬 개발 환경과 GCP 서비스를 효과적으로 결합하여 개발 편의성 및 서비스 품질 향상
    *   얼굴 Segmentation 및 동물 캐릭터 합성 기능에 특화된 API 활용
    *   비용 효율적인 개발 및 운영
*   **고려 사항:**
    *   FastAPI와 Cloud Functions 간 통신 설정 (HTTP 요청)
    *   Cloud Functions 배포 및 권한 설정
    *   GCP 서비스 사용량에 따른 비용 관리
    *   네트워크 지연 시간 고려

**5. 결론**

이러한 방식으로 인프라를 구성하면 로컬 개발 환경의 편의성과 GCP의 강력한 API를 동시에 활용하여 효율적인 서비스를 구축할 수 있습니다. 개발 단계에서는 로컬 환경에서 빠르게 개발하고, 프로덕션 환경에서는 GCP 서비스를 통해 안정적인 성능을 제공할 수 있습니다.

**다음 단계:**

1.  **Cloud Functions 배포 및 설정:** Cloud Functions를 GCP에 배포하고, 필요한 환경 변수를 설정합니다.
2.  **FastAPI 코드 수정:** 이미지 업로드 및 Cloud Functions 호출 로직을 구현합니다.
3.  **테스트 및 디버깅:** 로컬 환경에서 전체 흐름을 테스트하고, 오류를 수정합니다.
4.  **배포:** 완성된 애플리케이션을 배포합니다.
