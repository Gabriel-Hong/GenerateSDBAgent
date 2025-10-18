# PostgreSQL 통합 가이드

## 목차
1. [개요](#개요)
2. [PostgreSQL이란?](#postgresql이란)
3. [데이터베이스 설계](#데이터베이스-설계)
4. [구현 방안](#구현-방안)
5. [배포 가이드](#배포-가이드)
6. [API 엔드포인트](#api-엔드포인트)
7. [데이터 분석 및 통계](#데이터-분석-및-통계)
8. [백업 및 복구](#백업-및-복구)
9. [성능 최적화](#성능-최적화)
10. [트러블슈팅](#트러블슈팅)

---

## 개요

### 현재 시스템의 문제점

GenerateSDBAgent는 현재 **데이터 영속성**이 없습니다:

```python
# app/issue_processor.py:440
def process_issue(self, issue: Dict) -> Dict[str, Any]:
    result = {
        'status': 'started',
        'issue_key': issue.get('key'),
        'branch_name': None,
        'pr_url': None,
        'modified_files': [],
        'errors': []
    }
    # ... 처리 ...
    return result  # ❌ 메모리에만 존재! 앱 종료 시 사라짐
```

**문제점:**
1. ❌ **처리 이력 없음**: 어떤 이슈를 언제 처리했는지 모름
2. ❌ **중복 처리 위험**: 같은 이슈를 여러 번 처리 가능
3. ❌ **통계 불가**: 성공률, 평균 처리 시간 등 분석 불가
4. ❌ **디버깅 어려움**: 과거 실패 원인 추적 불가
5. ❌ **비용 추적 불가**: LLM API 비용 모니터링 불가
6. ❌ **감사 추적 불가**: 누가 언제 무엇을 변경했는지 기록 없음

### PostgreSQL 도입 효과

| 항목 | 현재 | PostgreSQL 도입 후 |
|------|------|-------------------|
| 이슈 처리 이력 | ❌ 없음 | ✅ 영구 보존 |
| 중복 처리 방지 | ❌ 불가능 | ✅ DB 레벨 체크 |
| 실패 원인 추적 | ❌ 로그만 | ✅ 구조화된 데이터 |
| 통계 및 분석 | ❌ 불가능 | ✅ SQL 쿼리로 즉시 가능 |
| 비용 추적 | ❌ 수동 계산 | ✅ 실시간 모니터링 |
| 감사 추적 | ❌ 없음 | ✅ 모든 변경 기록 |

---

## PostgreSQL이란?

### 기본 개념

**PostgreSQL**은 세계에서 가장 진보된 오픈소스 **관계형 데이터베이스(RDBMS)**입니다.

**쉬운 비유:**
- **Excel**: 개인용 데이터 관리 (작은 데이터, 단일 사용자)
- **Redis**: 초고속 메모장 (임시 데이터, 캐싱)
- **PostgreSQL**: 회사의 안전금고 (영구 보관, 복잡한 검색, 다중 사용자)

### 핵심 특징

1. **관계형 데이터베이스**
   - 데이터를 테이블(행/열) 형태로 저장
   - 테이블 간 관계(Foreign Key) 설정
   - SQL(Structured Query Language) 사용

2. **ACID 보장**
   - **A**tomicity (원자성): 트랜잭션이 전부 성공 or 전부 실패
   - **C**onsistency (일관성): 데이터 무결성 항상 유지
   - **I**solation (격리성): 동시 작업 간 간섭 없음
   - **D**urability (영속성): 커밋된 데이터는 영구 보존

3. **고급 기능**
   - **JSON/JSONB**: NoSQL처럼 유연한 스키마
   - **Full-text Search**: 전문 검색 엔진 내장
   - **Window Functions**: 복잡한 통계 쿼리
   - **CTE (Common Table Expressions)**: 재귀 쿼리
   - **트리거 및 함수**: 데이터 변경 시 자동 동작

### Redis vs PostgreSQL

| 특징 | Redis | PostgreSQL |
|------|-------|-----------|
| **타입** | Key-Value 저장소 | 관계형 데이터베이스 |
| **저장 위치** | 메모리 (RAM) | 디스크 (+ 메모리 캐시) |
| **속도** | 초고속 (0.001초) | 빠름 (0.01-0.1초) |
| **데이터 크기** | 제한적 (메모리 한계) | 대용량 (수백 TB) |
| **영속성** | 옵션 (주로 휘발성) | 보장 (영구 저장) |
| **쿼리** | 단순 (Key로 조회) | 복잡 (JOIN, 집계 등) |
| **트랜잭션** | 제한적 | 완전 지원 |
| **용도** | 캐시, 세션, 큐 | 비즈니스 데이터, 이력 |
| **적합성** | 임시 데이터, 빠른 조회 | 중요 데이터, 복잡한 분석 |

**역할 분담:**
- **Redis**: 속도가 중요한 캐싱 (LLM 응답, Bitbucket 파일)
- **PostgreSQL**: 데이터 보존이 중요한 이력 (처리 기록, 통계)

---

## 데이터베이스 설계

### ERD (Entity Relationship Diagram)

```
┌─────────────────────────────┐
│  issue_processing_history   │  메인 테이블
├─────────────────────────────┤
│ id (PK)                     │
│ issue_key                   │
│ issue_summary               │
│ status                      │
│ branch_name                 │
│ pr_url                      │
│ created_at                  │
│ started_at                  │
│ completed_at                │
│ processing_duration_seconds │
│ modified_files_count        │
│ error_message               │
│ issue_data (JSONB)          │
│ result_data (JSONB)         │
└─────────────────────────────┘
         ↓ 1:N
┌─────────────────────────────┐
│ file_modification_history   │  파일 수정 이력
├─────────────────────────────┤
│ id (PK)                     │
│ history_id (FK)             │
│ file_path                   │
│ action                      │
│ diff_count                  │
│ diff_text                   │
│ original_encoding           │
│ modified_encoding           │
│ created_at                  │
└─────────────────────────────┘

         ↓ 1:N
┌─────────────────────────────┐
│    llm_call_history         │  LLM 호출 이력
├─────────────────────────────┤
│ id (PK)                     │
│ history_id (FK)             │
│ call_type                   │
│ model                       │
│ prompt_tokens               │
│ completion_tokens           │
│ total_tokens                │
│ estimated_cost              │
│ cache_hit                   │
│ cache_key                   │
│ duration_seconds            │
│ created_at                  │
└─────────────────────────────┘

         ↓ 1:N
┌─────────────────────────────┐
│   bitbucket_api_history     │  Bitbucket API 호출 이력
├─────────────────────────────┤
│ id (PK)                     │
│ history_id (FK)             │
│ api_method                  │
│ endpoint                    │
│ status_code                 │
│ duration_seconds            │
│ created_at                  │
└─────────────────────────────┘
```

### 1. 이슈 처리 이력 테이블

```sql
-- issue_processing_history 테이블
CREATE TABLE issue_processing_history (
    -- 기본 키
    id SERIAL PRIMARY KEY,

    -- 이슈 정보
    issue_key VARCHAR(50) NOT NULL,
    issue_summary TEXT,

    -- 처리 상태
    status VARCHAR(20) NOT NULL,  -- queued, processing, completed, failed

    -- 결과 정보
    branch_name VARCHAR(255),
    pr_url TEXT,

    -- 타이밍 정보
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    processing_duration_seconds INTEGER,

    -- 결과 통계
    modified_files_count INTEGER DEFAULT 0,
    error_message TEXT,

    -- 메타데이터 (JSONB = JSON + 인덱싱)
    issue_data JSONB,      -- 전체 Jira 이슈 데이터
    result_data JSONB,     -- 전체 처리 결과

    -- 제약 조건
    CONSTRAINT check_status CHECK (status IN ('queued', 'processing', 'completed', 'failed'))
);

-- 인덱스 생성 (빠른 검색)
CREATE INDEX idx_iph_issue_key ON issue_processing_history(issue_key);
CREATE INDEX idx_iph_status ON issue_processing_history(status);
CREATE INDEX idx_iph_created_at ON issue_processing_history(created_at DESC);
CREATE INDEX idx_iph_completed_at ON issue_processing_history(completed_at DESC) WHERE completed_at IS NOT NULL;

-- JSONB 검색용 GIN 인덱스
CREATE INDEX idx_iph_issue_data ON issue_processing_history USING GIN (issue_data);
CREATE INDEX idx_iph_result_data ON issue_processing_history USING GIN (result_data);

-- 복합 인덱스 (자주 사용하는 쿼리 최적화)
CREATE INDEX idx_iph_issue_key_status ON issue_processing_history(issue_key, status);

-- 코멘트
COMMENT ON TABLE issue_processing_history IS '이슈 처리 이력 - 모든 Jira 이슈 처리 기록';
COMMENT ON COLUMN issue_processing_history.status IS 'queued: 대기중, processing: 처리중, completed: 완료, failed: 실패';
COMMENT ON COLUMN issue_processing_history.issue_data IS 'Jira에서 받은 전체 이슈 데이터 (JSONB)';
COMMENT ON COLUMN issue_processing_history.result_data IS '처리 결과 전체 데이터 (JSONB)';
```

### 2. 파일 수정 이력 테이블

```sql
-- file_modification_history 테이블
CREATE TABLE file_modification_history (
    -- 기본 키
    id SERIAL PRIMARY KEY,

    -- 외래 키
    history_id INTEGER NOT NULL REFERENCES issue_processing_history(id) ON DELETE CASCADE,

    -- 파일 정보
    file_path VARCHAR(500) NOT NULL,
    action VARCHAR(20) NOT NULL,  -- modified, created, deleted

    -- Diff 정보
    diff_count INTEGER DEFAULT 0,
    diff_text TEXT,

    -- 인코딩 정보
    original_encoding VARCHAR(50),
    modified_encoding VARCHAR(50),

    -- 전체 내용 (선택사항 - 용량 주의)
    -- 프로덕션에서는 파일 크기 제한 필요
    original_content TEXT,
    modified_content TEXT,

    -- 타이밍
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- 제약 조건
    CONSTRAINT check_action CHECK (action IN ('modified', 'created', 'deleted'))
);

-- 인덱스
CREATE INDEX idx_fmh_history_id ON file_modification_history(history_id);
CREATE INDEX idx_fmh_file_path ON file_modification_history(file_path);
CREATE INDEX idx_fmh_created_at ON file_modification_history(created_at DESC);

-- 복합 인덱스
CREATE INDEX idx_fmh_file_path_created ON file_modification_history(file_path, created_at DESC);

-- 코멘트
COMMENT ON TABLE file_modification_history IS '파일 수정 이력 - 각 이슈 처리 시 변경된 파일들';
COMMENT ON COLUMN file_modification_history.diff_text IS 'Unified diff 형식의 변경 내용';
```

### 3. LLM 호출 이력 테이블

```sql
-- llm_call_history 테이블
CREATE TABLE llm_call_history (
    -- 기본 키
    id SERIAL PRIMARY KEY,

    -- 외래 키
    history_id INTEGER NOT NULL REFERENCES issue_processing_history(id) ON DELETE CASCADE,

    -- 호출 정보
    call_type VARCHAR(50) NOT NULL,  -- spec_conversion, code_diff, new_file
    model VARCHAR(50) NOT NULL,      -- gpt-4o, gpt-4-turbo-preview

    -- 토큰 정보
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,

    -- 비용 (USD)
    estimated_cost DECIMAL(10, 4),

    -- 캐시 정보
    cache_hit BOOLEAN DEFAULT FALSE,
    cache_key VARCHAR(255),

    -- 타이밍
    duration_seconds DECIMAL(6, 3),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- 제약 조건
    CONSTRAINT check_call_type CHECK (
        call_type IN ('spec_conversion', 'code_diff', 'new_file', 'other')
    )
);

-- 인덱스
CREATE INDEX idx_lch_history_id ON llm_call_history(history_id);
CREATE INDEX idx_lch_call_type ON llm_call_history(call_type);
CREATE INDEX idx_lch_created_at ON llm_call_history(created_at DESC);
CREATE INDEX idx_lch_cache_hit ON llm_call_history(cache_hit);

-- 코멘트
COMMENT ON TABLE llm_call_history IS 'LLM API 호출 이력 - 비용 추적 및 성능 분석용';
COMMENT ON COLUMN llm_call_history.estimated_cost IS 'USD 단위 예상 비용';
COMMENT ON COLUMN llm_call_history.cache_hit IS 'Redis 캐시 히트 여부';
```

### 4. Bitbucket API 호출 이력 테이블

```sql
-- bitbucket_api_history 테이블
CREATE TABLE bitbucket_api_history (
    -- 기본 키
    id SERIAL PRIMARY KEY,

    -- 외래 키
    history_id INTEGER NOT NULL REFERENCES issue_processing_history(id) ON DELETE CASCADE,

    -- API 정보
    api_method VARCHAR(10) NOT NULL,  -- GET, POST, PUT, DELETE
    endpoint VARCHAR(500) NOT NULL,
    status_code INTEGER,

    -- 타이밍
    duration_seconds DECIMAL(6, 3),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- 에러 정보
    error_message TEXT,

    -- 제약 조건
    CONSTRAINT check_api_method CHECK (api_method IN ('GET', 'POST', 'PUT', 'DELETE'))
);

-- 인덱스
CREATE INDEX idx_bah_history_id ON bitbucket_api_history(history_id);
CREATE INDEX idx_bah_endpoint ON bitbucket_api_history(endpoint);
CREATE INDEX idx_bah_status_code ON bitbucket_api_history(status_code);
CREATE INDEX idx_bah_created_at ON bitbucket_api_history(created_at DESC);

-- 코멘트
COMMENT ON TABLE bitbucket_api_history IS 'Bitbucket API 호출 이력 - Rate Limit 추적';
```

### 5. 유용한 뷰 (View)

```sql
-- 처리 통계 뷰
CREATE VIEW v_processing_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total_issues,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status = 'processing') as processing,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) as success_rate,
    ROUND(AVG(processing_duration_seconds) FILTER (WHERE status = 'completed'), 2) as avg_duration,
    SUM(modified_files_count) FILTER (WHERE status = 'completed') as total_files_modified
FROM issue_processing_history
GROUP BY DATE(created_at);

-- LLM 비용 집계 뷰
CREATE VIEW v_llm_cost_daily AS
SELECT
    DATE(created_at) as date,
    call_type,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cache_hit = true) / COUNT(*), 2) as cache_hit_rate,
    SUM(total_tokens) as total_tokens,
    ROUND(SUM(estimated_cost), 2) as total_cost
FROM llm_call_history
GROUP BY DATE(created_at), call_type;

-- 최근 처리 이력 뷰
CREATE VIEW v_recent_issues AS
SELECT
    iph.issue_key,
    iph.issue_summary,
    iph.status,
    iph.branch_name,
    iph.pr_url,
    iph.created_at,
    iph.processing_duration_seconds,
    iph.modified_files_count,
    COUNT(fmh.id) as file_count,
    COUNT(lch.id) as llm_call_count,
    SUM(lch.estimated_cost) as total_llm_cost
FROM issue_processing_history iph
LEFT JOIN file_modification_history fmh ON iph.id = fmh.history_id
LEFT JOIN llm_call_history lch ON iph.id = lch.history_id
GROUP BY iph.id
ORDER BY iph.created_at DESC;
```

---

## 구현 방안

### Phase 1: SQLAlchemy ORM 설정

#### 1. 의존성 설치

```bash
# requirements.txt에 추가
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0  # PostgreSQL 드라이버
alembic>=1.12.0         # 마이그레이션 도구 (선택)
```

#### 2. 데이터베이스 모델 정의

```python
# app/models.py (신규)
"""
PostgreSQL 데이터 모델 (SQLAlchemy ORM)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, CheckConstraint
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class IssueProcessingHistory(Base):
    """이슈 처리 이력"""
    __tablename__ = 'issue_processing_history'

    # 기본 키
    id = Column(Integer, primary_key=True)

    # 이슈 정보
    issue_key = Column(String(50), nullable=False, index=True)
    issue_summary = Column(Text)

    # 처리 상태
    status = Column(String(20), nullable=False, index=True)

    # 결과 정보
    branch_name = Column(String(255))
    pr_url = Column(Text)

    # 타이밍 정보
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_duration_seconds = Column(Integer)

    # 결과 통계
    modified_files_count = Column(Integer, default=0)
    error_message = Column(Text)

    # 메타데이터
    issue_data = Column(JSON)
    result_data = Column(JSON)

    # 관계 (1:N)
    file_modifications = relationship(
        "FileModificationHistory",
        back_populates="processing_history",
        cascade="all, delete-orphan"
    )
    llm_calls = relationship(
        "LLMCallHistory",
        back_populates="processing_history",
        cascade="all, delete-orphan"
    )
    bitbucket_calls = relationship(
        "BitbucketAPIHistory",
        back_populates="processing_history",
        cascade="all, delete-orphan"
    )

    # 제약 조건
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed')",
            name='check_status'
        ),
    )

    def __repr__(self):
        return f"<IssueProcessingHistory(issue_key='{self.issue_key}', status='{self.status}')>"


class FileModificationHistory(Base):
    """파일 수정 이력"""
    __tablename__ = 'file_modification_history'

    # 기본 키
    id = Column(Integer, primary_key=True)

    # 외래 키
    history_id = Column(Integer, ForeignKey('issue_processing_history.id'), nullable=False, index=True)

    # 파일 정보
    file_path = Column(String(500), nullable=False, index=True)
    action = Column(String(20), nullable=False)

    # Diff 정보
    diff_count = Column(Integer, default=0)
    diff_text = Column(Text)

    # 인코딩 정보
    original_encoding = Column(String(50))
    modified_encoding = Column(String(50))

    # 전체 내용 (선택사항)
    original_content = Column(Text)
    modified_content = Column(Text)

    # 타이밍
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    # 관계
    processing_history = relationship("IssueProcessingHistory", back_populates="file_modifications")

    # 제약 조건
    __table_args__ = (
        CheckConstraint(
            "action IN ('modified', 'created', 'deleted')",
            name='check_action'
        ),
    )

    def __repr__(self):
        return f"<FileModificationHistory(file_path='{self.file_path}', action='{self.action}')>"


class LLMCallHistory(Base):
    """LLM 호출 이력"""
    __tablename__ = 'llm_call_history'

    # 기본 키
    id = Column(Integer, primary_key=True)

    # 외래 키
    history_id = Column(Integer, ForeignKey('issue_processing_history.id'), nullable=False, index=True)

    # 호출 정보
    call_type = Column(String(50), nullable=False, index=True)
    model = Column(String(50), nullable=False)

    # 토큰 정보
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)

    # 비용
    estimated_cost = Column(DECIMAL(10, 4))

    # 캐시 정보
    cache_hit = Column(Boolean, default=False, index=True)
    cache_key = Column(String(255))

    # 타이밍
    duration_seconds = Column(DECIMAL(6, 3))
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # 관계
    processing_history = relationship("IssueProcessingHistory", back_populates="llm_calls")

    # 제약 조건
    __table_args__ = (
        CheckConstraint(
            "call_type IN ('spec_conversion', 'code_diff', 'new_file', 'other')",
            name='check_call_type'
        ),
    )

    def __repr__(self):
        return f"<LLMCallHistory(call_type='{self.call_type}', model='{self.model}', cost={self.estimated_cost})>"


class BitbucketAPIHistory(Base):
    """Bitbucket API 호출 이력"""
    __tablename__ = 'bitbucket_api_history'

    # 기본 키
    id = Column(Integer, primary_key=True)

    # 외래 키
    history_id = Column(Integer, ForeignKey('issue_processing_history.id'), nullable=False, index=True)

    # API 정보
    api_method = Column(String(10), nullable=False)
    endpoint = Column(String(500), nullable=False, index=True)
    status_code = Column(Integer, index=True)

    # 타이밍
    duration_seconds = Column(DECIMAL(6, 3))
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # 에러 정보
    error_message = Column(Text)

    # 관계
    processing_history = relationship("IssueProcessingHistory", back_populates="bitbucket_calls")

    # 제약 조건
    __table_args__ = (
        CheckConstraint(
            "api_method IN ('GET', 'POST', 'PUT', 'DELETE')",
            name='check_api_method'
        ),
    )

    def __repr__(self):
        return f"<BitbucketAPIHistory(method='{self.api_method}', endpoint='{self.endpoint}')>"


# 데이터베이스 연결 설정
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://sdb_user:sdb_password@localhost:5432/sdb_agent'
)

# SQLAlchemy 엔진 생성
try:
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,           # 커넥션 풀 크기
        max_overflow=20,        # 최대 추가 커넥션
        pool_pre_ping=True,     # 연결 유효성 체크
        echo=False              # SQL 로그 출력 (개발 시 True)
    )

    # 세션 팩토리
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    logger.info(f"PostgreSQL 연결 성공: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

except Exception as e:
    logger.error(f"PostgreSQL 연결 실패: {str(e)}")
    raise


def init_db():
    """데이터베이스 테이블 생성"""
    Base.metadata.create_all(bind=engine)
    logger.info("데이터베이스 테이블 생성 완료")


def get_db():
    """
    데이터베이스 세션 제공 (FastAPI 의존성 주입용)

    Usage:
        from fastapi import Depends

        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### 3. 초기화 스크립트

```python
# scripts/init_db.py (신규)
"""
데이터베이스 초기화 스크립트
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import init_db, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_views():
    """뷰 생성"""
    views_sql = """
    -- 처리 통계 뷰
    CREATE OR REPLACE VIEW v_processing_stats AS
    SELECT
        DATE(created_at) as date,
        COUNT(*) as total_issues,
        COUNT(*) FILTER (WHERE status = 'completed') as completed,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        COUNT(*) FILTER (WHERE status = 'processing') as processing,
        ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) as success_rate,
        ROUND(AVG(processing_duration_seconds) FILTER (WHERE status = 'completed'), 2) as avg_duration,
        SUM(modified_files_count) FILTER (WHERE status = 'completed') as total_files_modified
    FROM issue_processing_history
    GROUP BY DATE(created_at);

    -- LLM 비용 집계 뷰
    CREATE OR REPLACE VIEW v_llm_cost_daily AS
    SELECT
        DATE(created_at) as date,
        call_type,
        COUNT(*) as total_calls,
        COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits,
        ROUND(100.0 * COUNT(*) FILTER (WHERE cache_hit = true) / COUNT(*), 2) as cache_hit_rate,
        SUM(total_tokens) as total_tokens,
        ROUND(SUM(estimated_cost), 2) as total_cost
    FROM llm_call_history
    GROUP BY DATE(created_at), call_type;

    -- 최근 처리 이력 뷰
    CREATE OR REPLACE VIEW v_recent_issues AS
    SELECT
        iph.id,
        iph.issue_key,
        iph.issue_summary,
        iph.status,
        iph.branch_name,
        iph.pr_url,
        iph.created_at,
        iph.processing_duration_seconds,
        iph.modified_files_count,
        COUNT(DISTINCT fmh.id) as file_count,
        COUNT(DISTINCT lch.id) as llm_call_count,
        SUM(lch.estimated_cost) as total_llm_cost
    FROM issue_processing_history iph
    LEFT JOIN file_modification_history fmh ON iph.id = fmh.history_id
    LEFT JOIN llm_call_history lch ON iph.id = lch.history_id
    GROUP BY iph.id
    ORDER BY iph.created_at DESC;
    """

    with engine.connect() as conn:
        conn.execute(text(views_sql))
        conn.commit()

    logger.info("뷰 생성 완료")


if __name__ == '__main__':
    logger.info("데이터베이스 초기화 시작...")

    # 테이블 생성
    init_db()

    # 뷰 생성
    create_views()

    logger.info("데이터베이스 초기화 완료!")
```

**실행:**
```bash
python scripts/init_db.py
```

---

### Phase 2: IssueProcessor 통합

#### IssueProcessor 수정

```python
# app/issue_processor.py 수정
from app.models import (
    IssueProcessingHistory,
    FileModificationHistory,
    LLMCallHistory,
    BitbucketAPIHistory,
    SessionLocal
)
from datetime import datetime
import time

class IssueProcessor:
    """Jira 이슈 처리 프로세서 (DB 통합)"""

    def __init__(self, bitbucket_api, llm_handler):
        self.bitbucket_api = bitbucket_api
        self.llm_handler = llm_handler
        self.large_file_handler = LargeFileHandler(llm_handler)
        self.prompt_builder = PromptBuilder(llm_handler)

        # DB 세션
        self.db = SessionLocal()

    def __del__(self):
        """소멸자 - DB 세션 정리"""
        if hasattr(self, 'db'):
            self.db.close()

    def process_issue(self, issue: Dict) -> Dict[str, Any]:
        """
        Jira 이슈를 처리하는 메인 워크플로우 (DB 통합)
        """
        issue_key = issue.get('key')
        issue_summary = issue.get('fields', {}).get('summary', '')

        # ✅ 1. 중복 처리 방지
        existing = self.db.query(IssueProcessingHistory).filter(
            IssueProcessingHistory.issue_key == issue_key,
            IssueProcessingHistory.status.in_(['processing', 'completed'])
        ).first()

        if existing:
            if existing.status == 'processing':
                logger.warning(f"이슈 {issue_key}는 이미 처리 중입니다 (시작: {existing.started_at})")
                return {
                    'status': 'already_processing',
                    'started_at': existing.started_at.isoformat(),
                    'history_id': existing.id
                }
            else:
                logger.warning(f"이슈 {issue_key}는 이미 처리되었습니다 (PR: {existing.pr_url})")
                return {
                    'status': 'already_completed',
                    'pr_url': existing.pr_url,
                    'completed_at': existing.completed_at.isoformat(),
                    'history_id': existing.id
                }

        # ✅ 2. 처리 시작 기록
        history = IssueProcessingHistory(
            issue_key=issue_key,
            issue_summary=issue_summary,
            status='processing',
            started_at=datetime.now(),
            issue_data=issue  # 전체 이슈 데이터 JSONB로 저장
        )
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)  # ID 가져오기

        logger.info(f"✅ 이슈 처리 시작 기록: {issue_key} (history_id: {history.id})")

        result = {
            'status': 'started',
            'issue_key': issue_key,
            'history_id': history.id,
            'branch_name': None,
            'pr_url': None,
            'modified_files': [],
            'errors': []
        }

        start_time = time.time()

        try:
            # 1. 이슈를 Material DB Spec으로 변환
            logger.info("Step 1: 이슈를 Material DB Spec으로 변환 중...")
            material_spec, llm_duration = self._convert_issue_with_timing(issue)

            # LLM 호출 기록
            self._record_llm_call(
                history.id,
                'spec_conversion',
                duration=llm_duration
            )

            # Spec 파일 저장
            spec_file_path = self._save_spec_file(issue_key, material_spec)
            logger.info(f"Spec 파일 생성 완료: {spec_file_path}")

            # 2. 브랜치 생성
            branch_name = self._generate_branch_name(issue)
            logger.info(f"Step 2: 브랜치 생성 중: {branch_name}")

            try:
                self._create_branch_with_logging(branch_name, history.id)
                result['branch_name'] = branch_name
                history.branch_name = branch_name
                self.db.commit()
            except Exception as e:
                logger.error(f"브랜치 생성 실패: {str(e)}")
                result['errors'].append(f"브랜치 생성 실패: {str(e)}")
                raise

            # 3. TARGET_FILES에서 수정 대상 파일 목록 가져오기
            from app.target_files_config import get_target_files
            target_files = get_target_files()
            files_to_modify = [f['path'] for f in target_files]

            logger.info(f"Step 3: 수정 대상 파일 {len(files_to_modify)}개")

            # 4. 파일 수정 (DB 기록 포함)
            logger.info("Step 4: 파일 수정 및 커밋 중...")
            modified_files = self._modify_files_with_logging(
                files_to_modify,
                branch_name,
                material_spec,
                issue,
                history.id
            )

            result['modified_files'] = modified_files
            history.modified_files_count = len(modified_files)
            self.db.commit()

            # 5. Pull Request 생성
            if modified_files:
                logger.info("Step 5: Pull Request 생성 중...")
                pr_title = f"[{issue_key}] {issue_summary}"
                pr_description = self._generate_pr_description(issue, modified_files)

                try:
                    pr_data, pr_duration = self._create_pr_with_logging(
                        branch_name,
                        'master',
                        pr_title,
                        pr_description,
                        history.id
                    )

                    pr_url = pr_data.get('links', {}).get('html', {}).get('href')
                    result['pr_url'] = pr_url
                    result['status'] = 'completed'

                    # ✅ DB 업데이트: 성공
                    history.status = 'completed'
                    history.completed_at = datetime.now()
                    history.processing_duration_seconds = int(time.time() - start_time)
                    history.pr_url = pr_url
                    history.result_data = result
                    self.db.commit()

                    logger.info(f"✅ 처리 완료: {issue_key} (소요시간: {history.processing_duration_seconds}초)")

                except Exception as e:
                    logger.error(f"PR 생성 실패: {str(e)}")
                    result['errors'].append(f"PR 생성 실패: {str(e)}")
                    raise
            else:
                logger.warning("수정된 파일이 없어 PR을 생성하지 않았습니다.")
                result['status'] = 'no_changes'

                history.status = 'completed'
                history.completed_at = datetime.now()
                history.processing_duration_seconds = int(time.time() - start_time)
                history.result_data = result
                self.db.commit()

            return result

        except Exception as e:
            logger.error(f"이슈 처리 중 예기치 않은 오류: {str(e)}", exc_info=True)
            result['errors'].append(f"예기치 않은 오류: {str(e)}")
            result['status'] = 'failed'

            # ✅ DB 업데이트: 실패
            history.status = 'failed'
            history.completed_at = datetime.now()
            history.processing_duration_seconds = int(time.time() - start_time)
            history.error_message = str(e)
            history.result_data = result
            self.db.commit()

            logger.error(f"❌ 처리 실패: {issue_key} (소요시간: {history.processing_duration_seconds}초)")

            return result

    def _convert_issue_with_timing(self, issue: Dict) -> tuple:
        """Spec 변환 + 타이밍 측정"""
        start = time.time()
        spec_content = self.llm_handler.convert_issue_to_spec(issue)
        duration = time.time() - start
        return spec_content, duration

    def _record_llm_call(self, history_id: int, call_type: str, duration: float,
                         model: str = None, tokens: Dict = None, cost: float = None,
                         cache_hit: bool = False, cache_key: str = None):
        """LLM 호출 기록"""
        llm_call = LLMCallHistory(
            history_id=history_id,
            call_type=call_type,
            model=model or self.llm_handler.model,
            prompt_tokens=tokens.get('prompt_tokens') if tokens else None,
            completion_tokens=tokens.get('completion_tokens') if tokens else None,
            total_tokens=tokens.get('total_tokens') if tokens else None,
            estimated_cost=cost,
            cache_hit=cache_hit,
            cache_key=cache_key,
            duration_seconds=round(duration, 3)
        )
        self.db.add(llm_call)
        self.db.commit()

        logger.info(f"LLM 호출 기록: {call_type} (소요시간: {duration:.2f}초, 캐시: {cache_hit})")

    def _create_branch_with_logging(self, branch_name: str, history_id: int):
        """브랜치 생성 + Bitbucket API 로깅"""
        start = time.time()

        try:
            self.bitbucket_api.create_branch(branch_name)
            duration = time.time() - start

            # API 호출 기록
            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='POST',
                endpoint=f'/refs/branches',
                status_code=200,
                duration_seconds=round(duration, 3)
            )
            self.db.add(bb_call)
            self.db.commit()

        except Exception as e:
            duration = time.time() - start

            # 실패도 기록
            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='POST',
                endpoint=f'/refs/branches',
                status_code=500,
                duration_seconds=round(duration, 3),
                error_message=str(e)
            )
            self.db.add(bb_call)
            self.db.commit()

            raise

    def _modify_files_with_logging(self, files_to_modify: List[str],
                                   branch_name: str, material_spec: str,
                                   issue: Dict, history_id: int) -> List[Dict]:
        """파일 수정 + DB 기록"""
        from app.encoding_handler import EncodingHandler
        encoding_handler = EncodingHandler()

        modified_files = []
        file_changes = []

        for file_path in files_to_modify:
            try:
                # 파일 읽기 (Bitbucket API 호출 기록)
                current_content_bytes, read_duration = self._get_file_with_timing(
                    file_path, branch_name, history_id
                )

                if current_content_bytes is None:
                    logger.warning(f"파일을 찾을 수 없음: {file_path}")
                    continue

                # 인코딩 감지 및 디코딩
                original_encoding = encoding_handler.detect_encoding_with_hint(
                    current_content_bytes, file_path
                )
                current_content, detected_encoding = encoding_handler.decode_with_fallback(
                    current_content_bytes, original_encoding
                )

                # ... (기존 파일 수정 로직) ...

                # diff 생성 (LLM 호출 기록)
                diffs, llm_duration = self._generate_diff_with_timing(
                    file_path, current_content, material_spec
                )

                self._record_llm_call(
                    history_id,
                    'code_diff',
                    duration=llm_duration
                )

                # diff 적용
                modified_content = self.llm_handler.apply_diff_to_content(current_content, diffs)
                diff_text = self._generate_diff_text(current_content, modified_content, file_path)

                # 인코딩 후 커밋 준비
                modified_content_bytes = encoding_handler.encode_preserving_original(
                    modified_content, detected_encoding
                )

                file_changes.append({
                    'path': file_path,
                    'content_bytes': modified_content_bytes,
                    'action': 'update'
                })

                # ✅ 파일 수정 이력 DB에 기록
                file_mod = FileModificationHistory(
                    history_id=history_id,
                    file_path=file_path,
                    action='modified',
                    diff_count=len(diffs),
                    diff_text=diff_text,
                    original_encoding=original_encoding,
                    modified_encoding=detected_encoding
                    # original_content와 modified_content는 용량 문제로 선택적 저장
                )
                self.db.add(file_mod)
                self.db.commit()

                modified_files.append({
                    'path': file_path,
                    'action': 'modified',
                    'diff_count': len(diffs),
                    'encoding': detected_encoding
                })

                logger.info(f"파일 수정 준비 완료: {file_path} ({len(diffs)}개 변경)")

            except Exception as e:
                logger.error(f"파일 수정 실패 ({file_path}): {str(e)}")

        # 모든 파일 커밋 (Bitbucket API 기록)
        if file_changes:
            commit_message = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary', 'SDB 기능 추가')}"
            self._commit_files_with_logging(
                branch_name, file_changes, commit_message, history_id
            )

        return modified_files

    def _get_file_with_timing(self, file_path: str, branch: str, history_id: int) -> tuple:
        """파일 읽기 + 타이밍 + API 기록"""
        start = time.time()

        try:
            content = self.bitbucket_api.get_file_content_raw(file_path, branch)
            duration = time.time() - start

            # API 호출 기록
            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='GET',
                endpoint=f'/src/{branch}/{file_path}',
                status_code=200 if content else 404,
                duration_seconds=round(duration, 3)
            )
            self.db.add(bb_call)
            self.db.commit()

            return content, duration

        except Exception as e:
            duration = time.time() - start

            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='GET',
                endpoint=f'/src/{branch}/{file_path}',
                status_code=500,
                duration_seconds=round(duration, 3),
                error_message=str(e)
            )
            self.db.add(bb_call)
            self.db.commit()

            raise

    def _generate_diff_with_timing(self, file_path: str, content: str, spec: str) -> tuple:
        """Diff 생성 + 타이밍"""
        start = time.time()
        # ... (기존 diff 생성 로직) ...
        diffs = []  # 실제 구현 필요
        duration = time.time() - start
        return diffs, duration

    def _commit_files_with_logging(self, branch: str, file_changes: List[Dict],
                                   message: str, history_id: int):
        """파일 커밋 + API 기록"""
        start = time.time()

        try:
            self.bitbucket_api.commit_multiple_files_binary(branch, file_changes, message)
            duration = time.time() - start

            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='POST',
                endpoint=f'/src',
                status_code=200,
                duration_seconds=round(duration, 3)
            )
            self.db.add(bb_call)
            self.db.commit()

            logger.info(f"커밋 완료: {len(file_changes)}개 파일 ({duration:.2f}초)")

        except Exception as e:
            duration = time.time() - start

            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='POST',
                endpoint=f'/src',
                status_code=500,
                duration_seconds=round(duration, 3),
                error_message=str(e)
            )
            self.db.add(bb_call)
            self.db.commit()

            raise

    def _create_pr_with_logging(self, source: str, dest: str, title: str,
                                description: str, history_id: int) -> tuple:
        """PR 생성 + API 기록"""
        start = time.time()

        try:
            pr_data = self.bitbucket_api.create_pull_request(source, dest, title, description)
            duration = time.time() - start

            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='POST',
                endpoint='/pullrequests',
                status_code=200,
                duration_seconds=round(duration, 3)
            )
            self.db.add(bb_call)
            self.db.commit()

            return pr_data, duration

        except Exception as e:
            duration = time.time() - start

            bb_call = BitbucketAPIHistory(
                history_id=history_id,
                api_method='POST',
                endpoint='/pullrequests',
                status_code=500,
                duration_seconds=round(duration, 3),
                error_message=str(e)
            )
            self.db.add(bb_call)
            self.db.commit()

            raise
```

---

### Phase 3: LLM Handler 통합 (비용 추적)

```python
# app/llm_handler.py 수정
from app.models import LLMCallHistory, SessionLocal
import time

class LLMHandler:
    def __init__(self):
        # ... 기존 코드 ...
        self.db = SessionLocal()

        # GPT-4 모델별 비용 (USD per 1K tokens)
        self.pricing = {
            'gpt-4o': {
                'prompt': 0.005,      # $0.005 / 1K tokens
                'completion': 0.015   # $0.015 / 1K tokens
            },
            'gpt-4-turbo-preview': {
                'prompt': 0.01,
                'completion': 0.03
            },
            'gpt-3.5-turbo': {
                'prompt': 0.0005,
                'completion': 0.0015
            }
        }

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """토큰 기반 비용 계산"""
        if model not in self.pricing:
            return 0.0

        pricing = self.pricing[model]
        prompt_cost = (prompt_tokens / 1000) * pricing['prompt']
        completion_cost = (completion_tokens / 1000) * pricing['completion']

        return round(prompt_cost + completion_cost, 4)

    def convert_issue_to_spec(self, issue: Dict, history_id: int = None) -> str:
        """
        Jira 이슈를 Spec으로 변환 (비용 추적 포함)
        """
        # ... (캐시 확인 로직) ...

        start_time = time.time()
        cache_hit = False
        cache_key = None

        try:
            # LLM 호출
            response = self.client.chat.completions.create(...)

            spec_content = response.choices[0].message.content
            duration = time.time() - start_time

            # 토큰 및 비용 계산
            usage = response.usage
            cost = self._calculate_cost(
                self.model,
                usage.prompt_tokens,
                usage.completion_tokens
            )

            # ✅ DB에 LLM 호출 기록
            if history_id:
                llm_call = LLMCallHistory(
                    history_id=history_id,
                    call_type='spec_conversion',
                    model=self.model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    estimated_cost=cost,
                    cache_hit=cache_hit,
                    cache_key=cache_key,
                    duration_seconds=round(duration, 3)
                )
                self.db.add(llm_call)
                self.db.commit()

                logger.info(f"LLM 호출 비용: ${cost:.4f} ({usage.total_tokens} tokens)")

            return spec_content

        except Exception as e:
            logger.error(f"Spec 변환 실패: {str(e)}")
            raise
```

---

## API 엔드포인트

### Flask API 추가

```python
# app/main.py에 추가
from app.models import (
    IssueProcessingHistory,
    FileModificationHistory,
    LLMCallHistory,
    SessionLocal
)
from sqlalchemy import func, desc
from flask import jsonify, request

@app.route('/history', methods=['GET'])
def get_history():
    """
    처리 이력 조회

    Query Parameters:
        - limit: 반환할 개수 (기본: 20)
        - status: 상태 필터 (completed, failed, processing)
        - issue_key: 특정 이슈 키
    """
    db = SessionLocal()

    try:
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status')
        issue_key = request.args.get('issue_key')

        query = db.query(IssueProcessingHistory).order_by(
            desc(IssueProcessingHistory.created_at)
        )

        if status:
            query = query.filter(IssueProcessingHistory.status == status)

        if issue_key:
            query = query.filter(IssueProcessingHistory.issue_key == issue_key)

        results = query.limit(limit).all()

        return jsonify([{
            'id': r.id,
            'issue_key': r.issue_key,
            'issue_summary': r.issue_summary,
            'status': r.status,
            'branch_name': r.branch_name,
            'pr_url': r.pr_url,
            'created_at': r.created_at.isoformat(),
            'started_at': r.started_at.isoformat() if r.started_at else None,
            'completed_at': r.completed_at.isoformat() if r.completed_at else None,
            'duration': r.processing_duration_seconds,
            'modified_files_count': r.modified_files_count,
            'error_message': r.error_message
        } for r in results]), 200

    finally:
        db.close()


@app.route('/history/<int:history_id>', methods=['GET'])
def get_history_detail(history_id):
    """특정 처리 이력 상세 조회"""
    db = SessionLocal()

    try:
        history = db.query(IssueProcessingHistory).filter(
            IssueProcessingHistory.id == history_id
        ).first()

        if not history:
            return jsonify({'error': 'Not found'}), 404

        # 파일 수정 이력
        files = db.query(FileModificationHistory).filter(
            FileModificationHistory.history_id == history_id
        ).all()

        # LLM 호출 이력
        llm_calls = db.query(LLMCallHistory).filter(
            LLMCallHistory.history_id == history_id
        ).all()

        return jsonify({
            'id': history.id,
            'issue_key': history.issue_key,
            'issue_summary': history.issue_summary,
            'status': history.status,
            'branch_name': history.branch_name,
            'pr_url': history.pr_url,
            'created_at': history.created_at.isoformat(),
            'duration': history.processing_duration_seconds,
            'files': [{
                'path': f.file_path,
                'action': f.action,
                'diff_count': f.diff_count,
                'encoding': f.modified_encoding
            } for f in files],
            'llm_calls': [{
                'call_type': l.call_type,
                'model': l.model,
                'total_tokens': l.total_tokens,
                'cost': float(l.estimated_cost) if l.estimated_cost else 0,
                'cache_hit': l.cache_hit,
                'duration': float(l.duration_seconds) if l.duration_seconds else 0
            } for l in llm_calls],
            'total_llm_cost': sum(float(l.estimated_cost or 0) for l in llm_calls)
        }), 200

    finally:
        db.close()


@app.route('/stats', methods=['GET'])
def get_stats():
    """전체 통계"""
    db = SessionLocal()

    try:
        # 전체 통계
        total = db.query(IssueProcessingHistory).count()
        completed = db.query(IssueProcessingHistory).filter(
            IssueProcessingHistory.status == 'completed'
        ).count()
        failed = db.query(IssueProcessingHistory).filter(
            IssueProcessingHistory.status == 'failed'
        ).count()
        processing = db.query(IssueProcessingHistory).filter(
            IssueProcessingHistory.status == 'processing'
        ).count()

        # 평균 처리 시간
        avg_duration = db.query(
            func.avg(IssueProcessingHistory.processing_duration_seconds)
        ).filter(
            IssueProcessingHistory.status == 'completed'
        ).scalar()

        # 총 LLM 비용
        total_llm_cost = db.query(
            func.sum(LLMCallHistory.estimated_cost)
        ).scalar()

        # 캐시 히트율
        total_llm_calls = db.query(LLMCallHistory).count()
        cache_hits = db.query(LLMCallHistory).filter(
            LLMCallHistory.cache_hit == True
        ).count()

        return jsonify({
            'total_issues': total,
            'completed': completed,
            'failed': failed,
            'processing': processing,
            'success_rate': round(100 * completed / total, 2) if total > 0 else 0,
            'avg_duration_seconds': round(avg_duration, 2) if avg_duration else 0,
            'total_llm_cost_usd': round(float(total_llm_cost or 0), 2),
            'total_llm_calls': total_llm_calls,
            'cache_hit_rate': round(100 * cache_hits / total_llm_calls, 2) if total_llm_calls > 0 else 0
        }), 200

    finally:
        db.close()


@app.route('/stats/daily', methods=['GET'])
def get_daily_stats():
    """일별 통계"""
    db = SessionLocal()

    try:
        days = request.args.get('days', 7, type=int)

        # v_processing_stats 뷰 사용
        from sqlalchemy import text

        query = text("""
            SELECT *
            FROM v_processing_stats
            WHERE date >= CURRENT_DATE - :days
            ORDER BY date DESC
        """)

        result = db.execute(query, {'days': days})
        rows = result.fetchall()

        return jsonify([{
            'date': str(row[0]),
            'total_issues': row[1],
            'completed': row[2],
            'failed': row[3],
            'processing': row[4],
            'success_rate': float(row[5]) if row[5] else 0,
            'avg_duration': float(row[6]) if row[6] else 0,
            'total_files_modified': row[7]
        } for row in rows]), 200

    finally:
        db.close()


@app.route('/stats/llm-cost', methods=['GET'])
def get_llm_cost_stats():
    """LLM 비용 통계"""
    db = SessionLocal()

    try:
        days = request.args.get('days', 7, type=int)

        query = text("""
            SELECT *
            FROM v_llm_cost_daily
            WHERE date >= CURRENT_DATE - :days
            ORDER BY date DESC, call_type
        """)

        result = db.execute(query, {'days': days})
        rows = result.fetchall()

        return jsonify([{
            'date': str(row[0]),
            'call_type': row[1],
            'total_calls': row[2],
            'cache_hits': row[3],
            'cache_hit_rate': float(row[4]) if row[4] else 0,
            'total_tokens': row[5],
            'total_cost': float(row[6]) if row[6] else 0
        } for row in rows]), 200

    finally:
        db.close()


@app.route('/files/<path:file_path>/history', methods=['GET'])
def get_file_history(file_path):
    """특정 파일의 수정 이력"""
    db = SessionLocal()

    try:
        modifications = db.query(
            FileModificationHistory, IssueProcessingHistory
        ).join(
            IssueProcessingHistory,
            FileModificationHistory.history_id == IssueProcessingHistory.id
        ).filter(
            FileModificationHistory.file_path == file_path
        ).order_by(
            desc(FileModificationHistory.created_at)
        ).limit(20).all()

        return jsonify([{
            'file_path': mod.file_path,
            'action': mod.action,
            'diff_count': mod.diff_count,
            'created_at': mod.created_at.isoformat(),
            'issue_key': hist.issue_key,
            'issue_summary': hist.issue_summary,
            'pr_url': hist.pr_url
        } for mod, hist in modifications]), 200

    finally:
        db.close()
```

---

## 데이터 분석 및 통계

### 유용한 SQL 쿼리 모음

#### 1. 성공률 추이 (주별)

```sql
SELECT
    DATE_TRUNC('week', created_at) as week,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'completed') as success,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) as success_rate
FROM issue_processing_history
WHERE created_at >= NOW() - INTERVAL '3 months'
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;
```

#### 2. 가장 자주 수정되는 파일 Top 10

```sql
SELECT
    file_path,
    COUNT(*) as modification_count,
    COUNT(DISTINCT history_id) as unique_issues,
    MAX(created_at) as last_modified
FROM file_modification_history
GROUP BY file_path
ORDER BY modification_count DESC
LIMIT 10;
```

#### 3. LLM 비용 분석 (모델별, 호출 타입별)

```sql
SELECT
    model,
    call_type,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE cache_hit = true) as cache_hits,
    ROUND(100.0 * COUNT(*) FILTER (WHERE cache_hit = true) / COUNT(*), 2) as cache_hit_rate,
    SUM(total_tokens) as total_tokens,
    ROUND(SUM(estimated_cost), 2) as total_cost,
    ROUND(AVG(estimated_cost), 4) as avg_cost_per_call
FROM llm_call_history
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY model, call_type
ORDER BY total_cost DESC;
```

#### 4. 시간대별 처리량 분석

```sql
SELECT
    EXTRACT(HOUR FROM created_at) as hour,
    COUNT(*) as issue_count,
    ROUND(AVG(processing_duration_seconds), 2) as avg_duration
FROM issue_processing_history
WHERE created_at >= NOW() - INTERVAL '7 days'
    AND status = 'completed'
GROUP BY EXTRACT(HOUR FROM created_at)
ORDER BY hour;
```

#### 5. 실패 원인 분석

```sql
SELECT
    SUBSTRING(error_message, 1, 100) as error_preview,
    COUNT(*) as occurrence_count,
    MAX(created_at) as last_occurred
FROM issue_processing_history
WHERE status = 'failed'
    AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY SUBSTRING(error_message, 1, 100)
ORDER BY occurrence_count DESC
LIMIT 20;
```

#### 6. Bitbucket API Rate Limit 추적

```sql
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    api_method,
    COUNT(*) as call_count,
    ROUND(AVG(duration_seconds), 3) as avg_duration,
    COUNT(*) FILTER (WHERE status_code >= 400) as error_count
FROM bitbucket_api_history
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at), api_method
ORDER BY hour DESC, call_count DESC;
```

#### 7. 처리 시간 백분위수

```sql
SELECT
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY processing_duration_seconds) as p50,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY processing_duration_seconds) as p75,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY processing_duration_seconds) as p90,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_duration_seconds) as p95,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY processing_duration_seconds) as p99
FROM issue_processing_history
WHERE status = 'completed'
    AND created_at >= NOW() - INTERVAL '30 days';
```

---

## 배포 가이드

### 로컬 개발 환경

#### 1. PostgreSQL 설치 및 실행

**macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql-15 postgresql-contrib
sudo systemctl start postgresql
```

**Docker:**
```bash
docker run -d \
  --name postgres-sdb \
  -e POSTGRES_USER=sdb_user \
  -e POSTGRES_PASSWORD=sdb_password \
  -e POSTGRES_DB=sdb_agent \
  -p 5432:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:15-alpine
```

#### 2. 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 및 사용자 생성
CREATE USER sdb_user WITH PASSWORD 'sdb_password';
CREATE DATABASE sdb_agent OWNER sdb_user;
GRANT ALL PRIVILEGES ON DATABASE sdb_agent TO sdb_user;

# 연결 테스트
\c sdb_agent sdb_user
```

#### 3. 환경 변수 설정

```bash
# .env
DATABASE_URL=postgresql://sdb_user:sdb_password@localhost:5432/sdb_agent
```

#### 4. 테이블 생성

```bash
python scripts/init_db.py
```

---

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: postgres-sdb
    environment:
      POSTGRES_USER: sdb_user
      POSTGRES_PASSWORD: sdb_password
      POSTGRES_DB: sdb_agent
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sdb_user -d sdb_agent"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://sdb_user:sdb_password@postgres:5432/sdb_agent
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - BITBUCKET_ACCESS_TOKEN=${BITBUCKET_ACCESS_TOKEN}
      - BITBUCKET_WORKSPACE=${BITBUCKET_WORKSPACE}
      - BITBUCKET_REPOSITORY=${BITBUCKET_REPOSITORY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python -m app.main

  worker:
    build: .
    environment:
      - DATABASE_URL=postgresql://sdb_user:sdb_password@postgres:5432/sdb_agent
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - BITBUCKET_ACCESS_TOKEN=${BITBUCKET_ACCESS_TOKEN}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: rq worker sdb_tasks --url redis://redis:6379/0 --verbose

volumes:
  postgres_data:
  redis_data:
```

**실행:**
```bash
docker-compose up -d
```

---

### Kubernetes 배포

#### 1. PostgreSQL StatefulSet

```yaml
# k8s/postgres/statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: agent-system
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
          name: postgres
        env:
        - name: POSTGRES_USER
          value: "sdb_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: POSTGRES_PASSWORD
        - name: POSTGRES_DB
          value: "sdb_agent"
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - sdb_user
            - -d
            - sdb_agent
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - sdb_user
            - -d
            - sdb_agent
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: "standard"
      resources:
        requests:
          storage: 20Gi
```

#### 2. PostgreSQL Service

```yaml
# k8s/postgres/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: agent-system
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432
  type: ClusterIP
```

#### 3. Secret 생성

```bash
kubectl create secret generic agent-secrets \
  --from-literal=POSTGRES_PASSWORD='sdb_password' \
  --from-literal=OPENAI_API_KEY='sk-...' \
  --from-literal=BITBUCKET_ACCESS_TOKEN='your-token' \
  -n agent-system
```

#### 4. SDB Agent Deployment (DB 연동)

```yaml
# k8s/sdb-agent/deployment.yaml 수정
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sdb-agent
  namespace: agent-system
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sdb-agent
  template:
    metadata:
      labels:
        app: sdb-agent
    spec:
      initContainers:
      - name: init-db
        image: your-registry/sdb-agent:latest
        command: ['python', 'scripts/init_db.py']
        env:
        - name: DATABASE_URL
          value: "postgresql://sdb_user:$(POSTGRES_PASSWORD)@postgres-service:5432/sdb_agent"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: POSTGRES_PASSWORD
      containers:
      - name: sdb-agent
        image: your-registry/sdb-agent:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          value: "postgresql://sdb_user:$(POSTGRES_PASSWORD)@postgres-service:5432/sdb_agent"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: POSTGRES_PASSWORD
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: OPENAI_API_KEY
        # ... 기타 환경 변수 ...
```

#### 5. 배포 순서

```bash
# 1. Namespace
kubectl apply -f k8s/base/namespace.yaml

# 2. Secrets
kubectl create secret generic agent-secrets ...

# 3. PostgreSQL
kubectl apply -f k8s/postgres/statefulset.yaml
kubectl apply -f k8s/postgres/service.yaml

# 4. Redis
kubectl apply -f k8s/redis/

# 5. SDB Agent
kubectl apply -f k8s/sdb-agent/

# 6. RQ Worker
kubectl apply -f k8s/rq-worker/

# 7. 상태 확인
kubectl get pods -n agent-system
```

---

## 백업 및 복구

### 자동 백업 스크립트

```bash
# scripts/backup_postgres.sh
#!/bin/bash

# 환경 변수
BACKUP_DIR="/var/backups/postgresql"
DB_NAME="sdb_agent"
DB_USER="sdb_user"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sdb_agent_${TIMESTAMP}.sql"

# 디렉토리 생성
mkdir -p $BACKUP_DIR

# 백업 실행
PGPASSWORD=$POSTGRES_PASSWORD pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_FILE

# 압축
gzip $BACKUP_FILE

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "백업 완료: ${BACKUP_FILE}.gz"
```

**Cron 설정 (매일 새벽 2시):**
```bash
crontab -e

# 추가
0 2 * * * /path/to/scripts/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
```

### 복구 스크립트

```bash
# scripts/restore_postgres.sh
#!/bin/bash

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

# 압축 해제
gunzip -c $BACKUP_FILE > /tmp/restore.sql

# 복구
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U sdb_user -d sdb_agent < /tmp/restore.sql

# 임시 파일 삭제
rm /tmp/restore.sql

echo "복구 완료"
```

---

## 성능 최적화

### 1. 인덱스 최적화

```sql
-- 느린 쿼리 찾기
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- 사용되지 않는 인덱스 찾기
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;

-- 인덱스 크기 확인
SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

### 2. 파티셔닝 (대용량 데이터)

```sql
-- 월별 파티셔닝 예제
CREATE TABLE issue_processing_history_partitioned (
    -- ... 기존 컬럼들 ...
) PARTITION BY RANGE (created_at);

-- 파티션 생성
CREATE TABLE issue_processing_history_2025_01
    PARTITION OF issue_processing_history_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE issue_processing_history_2025_02
    PARTITION OF issue_processing_history_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- 자동 파티션 생성 함수
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE := DATE_TRUNC('month', CURRENT_DATE);
    partition_name TEXT := 'issue_processing_history_' || TO_CHAR(partition_date, 'YYYY_MM');
    next_month DATE := partition_date + INTERVAL '1 month';
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I
        PARTITION OF issue_processing_history_partitioned
        FOR VALUES FROM (%L) TO (%L)',
        partition_name, partition_date, next_month
    );
END;
$$ LANGUAGE plpgsql;

-- 매월 1일 자동 실행 (cron)
SELECT cron.schedule('create-partition', '0 0 1 * *', 'SELECT create_monthly_partition()');
```

### 3. VACUUM 및 ANALYZE

```sql
-- 수동 VACUUM
VACUUM ANALYZE issue_processing_history;

-- Auto-vacuum 설정 확인
SELECT
    relname,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE relname LIKE 'issue%';
```

### 4. 커넥션 풀링

```python
# app/models.py 수정
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # 기본 커넥션 수
    max_overflow=20,        # 최대 추가 커넥션
    pool_pre_ping=True,     # 연결 유효성 체크
    pool_recycle=3600,      # 1시간마다 커넥션 재생성
    echo=False
)
```

---

## 트러블슈팅

### 1. 연결 문제

**증상:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**해결:**
```bash
# PostgreSQL 상태 확인
sudo systemctl status postgresql

# 포트 확인
sudo netstat -plnt | grep 5432

# 방화벽 확인
sudo ufw allow 5432/tcp

# postgresql.conf 수정
listen_addresses = '*'

# pg_hba.conf 수정
host    all             all             0.0.0.0/0            md5
```

---

### 2. 테이블 잠금 (Lock)

**증상:**
```
처리가 느려지거나 멈춤
```

**해결:**
```sql
-- 잠금 확인
SELECT
    pg_stat_activity.pid,
    pg_stat_activity.query,
    pg_locks.mode,
    pg_locks.granted
FROM pg_stat_activity
JOIN pg_locks ON pg_stat_activity.pid = pg_locks.pid
WHERE NOT pg_locks.granted;

-- 프로세스 종료
SELECT pg_terminate_backend(pid);
```

---

### 3. 디스크 용량 부족

**증상:**
```
ERROR: could not extend file: No space left on device
```

**해결:**
```bash
# 디스크 사용량 확인
df -h

# PostgreSQL 데이터 크기 확인
du -sh /var/lib/postgresql/data

# 불필요한 데이터 삭제
DELETE FROM file_modification_history
WHERE created_at < NOW() - INTERVAL '90 days'
    AND modified_content IS NOT NULL;

# VACUUM으로 공간 회수
VACUUM FULL;
```

---

### 4. 느린 쿼리

**증상:**
```
특정 API 호출이 느림
```

**해결:**
```sql
-- pg_stat_statements 활성화
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- 느린 쿼리 확인
SELECT
    query,
    calls,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- EXPLAIN ANALYZE로 쿼리 계획 확인
EXPLAIN ANALYZE
SELECT * FROM issue_processing_history
WHERE issue_key = 'GEN-123';

-- 필요시 인덱스 추가
CREATE INDEX idx_custom ON table_name(column_name);
```

---

## 마이그레이션 (Alembic)

### Alembic 설정

```bash
# Alembic 설치
pip install alembic

# 초기화
alembic init alembic

# alembic.ini 수정
sqlalchemy.url = postgresql://sdb_user:sdb_password@localhost/sdb_agent
```

### 마이그레이션 생성

```bash
# 자동 마이그레이션 생성
alembic revision --autogenerate -m "Add new column"

# 수동 마이그레이션 생성
alembic revision -m "Add index"
```

### 마이그레이션 적용

```bash
# 최신 버전으로 업그레이드
alembic upgrade head

# 특정 버전으로 다운그레이드
alembic downgrade -1

# 마이그레이션 히스토리 확인
alembic history
```

---

## 참고 자료

### PostgreSQL 공식 문서
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

### 관련 내부 문서
- [REDIS_OPTIMIZATION_GUIDE.md](./REDIS_OPTIMIZATION_GUIDE.md) - Redis 최적화
- [MULTI_AGENT_ARCHITECTURE.md](./MULTI_AGENT_ARCHITECTURE.md) - 멀티 Agent 아키텍처
- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md) - Docker 배포

---

## 다음 단계

### 단계별 적용 로드맵

#### Week 1: 기본 구조
- [ ] PostgreSQL 설치 및 설정
- [ ] SQLAlchemy 모델 정의
- [ ] 테이블 생성 및 테스트

#### Week 2: IssueProcessor 통합
- [ ] 이슈 처리 이력 저장
- [ ] 중복 처리 방지
- [ ] 기본 API 엔드포인트

#### Week 3: 상세 이력 추가
- [ ] 파일 수정 이력
- [ ] LLM 호출 이력
- [ ] Bitbucket API 이력

#### Week 4: 분석 및 최적화
- [ ] 통계 API 구현
- [ ] 성능 최적화
- [ ] 백업 자동화

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-10-16
**작성자**: Development Team
