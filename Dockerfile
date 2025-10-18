# Python 3.12 슬림 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libclang-dev \
    clang \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# Flask 앱 환경 변수 설정
ENV FLASK_APP=app.main:app
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# 포트 노출
EXPOSE 5000

# 애플리케이션 실행
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
