# Redis 성능 최적화 가이드

## 목차
1. [개요](#개요)
2. [Redis 활용 전략](#redis-활용-전략)
3. [구현 방안](#구현-방안)
4. [배포 가이드](#배포-가이드)
5. [성능 측정](#성능-측정)
6. [트러블슈팅](#트러블슈팅)

---

## 개요

### 현재 시스템의 성능 병목

GenerateSDBAgent 프로젝트의 주요 성능 병목 지점:

1. **LLM API 호출** (가장 큰 병목)
   - OpenAI API 응답 시간: 5-30초
   - 타임아웃 설정: 60초
   - 동일한 요청에 대해 반복 호출
   - 비용: 요청당 $0.01-0.1

2. **Bitbucket API 호출**
   - 파일 읽기/쓰기 반복
   - 브랜치 정보 중복 조회
   - Rate Limiting 위험

3. **임베딩 계산**
   - 파일 기반 캐시로 Pod간 공유 불가
   - 멀티 인스턴스 환경에서 중복 계산

4. **동기 처리**
   - Webhook 응답 지연
   - 타임아웃 위험

### Redis 도입 효과 예측

| 항목 | 현재 | Redis 적용 후 | 개선율 |
|------|------|--------------|--------|
| LLM API 응답 | 10-30초 | 0.01-0.1초 (캐시 히트) | **100-300배** |
| Bitbucket 파일 읽기 | 0.5-2초 | 0.01초 | **50-200배** |
| 임베딩 검색 | 5-10초 | 0.1-1초 (캐시) | **10배** |
| Webhook 응답 | 30-120초 | 0.1초 (Queue) | **300-1200배** |
| API 비용 | $10/일 | $1/일 (캐시 히트율 90%) | **90% 절감** |

---

## Redis 활용 전략

### 1. LLM 응답 캐싱 (최우선 적용)

#### 문제점
```python
# app/llm_handler.py:239
def convert_issue_to_spec(self, issue: Dict) -> str:
    # 매번 OpenAI API 호출 (5-30초 소요)
    response = self.client.chat.completions.create(
        model=self.model,
        messages=[...],
        temperature=0.1
    )
```

**현재 문제:**
- 동일한 이슈로 여러 번 테스트 시 매번 API 호출
- 유사한 이슈도 처음부터 다시 생성
- 비용 및 시간 낭비

#### 해결 방안

**캐시 키 전략:**
```python
cache_key = f"llm:spec:{hash(issue_summary + issue_description)}"
```

**캐시 구조:**
```
Key: llm:spec:<hash>
Value: {
    "spec_content": "# Material DB 명세서\n...",
    "timestamp": "2025-10-16T10:30:00",
    "model": "gpt-4o",
    "tokens_used": 2500
}
TTL: 7일 (604800초)
```

**적용 위치:**
1. `convert_issue_to_spec()` - Jira 이슈 → Spec 변환
2. `generate_code_diff()` - 코드 수정 diff 생성
3. `generate_new_file()` - 새 파일 생성

**예상 효과:**
- 캐시 히트율: 70-90%
- 응답 속도: 10초 → 0.01초 (1000배)
- API 비용: 90% 절감
- 동일 이슈 재처리 시 즉시 응답

---

### 2. Bitbucket API 응답 캐싱

#### 문제점
```python
# app/bitbucket_api.py:198
def get_file_content(self, file_path: str, branch: str = "master") -> Optional[str]:
    # 매번 HTTP 요청 (0.5-2초)
    url = f"{self.repo_base}/src/{branch}/{file_path}"
    response = self.make_bitbucket_request(url)
```

**현재 문제:**
- 동일 파일을 여러 Agent가 중복 조회
- 브랜치 정보 반복 조회
- Bitbucket Rate Limit 위험 (시간당 1000건)

#### 해결 방안

**캐시 키 전략:**
```python
# 파일 내용 캐싱
cache_key = f"bb:file:{workspace}:{repository}:{branch}:{file_path}"

# 브랜치 정보 캐싱
cache_key = f"bb:branch:{workspace}:{repository}:{branch_name}"

# 디렉토리 목록 캐싱
cache_key = f"bb:dir:{workspace}:{repository}:{branch}:{dir_path}"
```

**TTL 설정:**
- 파일 내용: 300초 (5분)
- 브랜치 정보: 60초 (1분)
- 디렉토리 목록: 300초 (5분)

**캐시 무효화 전략:**
```python
# 파일 수정 시 캐시 삭제
def commit_file(self, branch, file_path, content, message):
    result = self._commit_to_bitbucket(...)

    # 캐시 무효화
    cache_key = f"bb:file:{self.workspace}:{self.repository}:{branch}:{file_path}"
    redis_client.delete(cache_key)

    return result
```

**예상 효과:**
- API 호출 50% 감소
- 파일 읽기 속도: 1초 → 0.01초
- Rate Limit 여유 확보

---

### 3. 임베딩 결과 캐싱

#### 문제점
```python
# app/embedding_search.py:182
class CachedEmbeddingSearch(EmbeddingBasedSearch):
    def __init__(self, model_name='all-MiniLM-L6-v2', cache_dir='.embedding_cache'):
        # 파일 기반 캐시 (로컬만 사용 가능)
        self.cache_dir = cache_dir
```

**현재 문제:**
- 파일 기반 캐시로 Pod 간 공유 불가
- 각 Pod가 동일한 임베딩 중복 계산
- 멀티 인스턴스 환경에서 비효율

#### 해결 방안

**Redis 기반 임베딩 캐시:**
```python
cache_key = f"embedding:{model_name}:{hash(function_list)}"

# 값: numpy array를 pickle/msgpack으로 직렬화
value = {
    "embeddings": base64.encode(pickle.dumps(embeddings)),
    "count": len(functions),
    "model": "all-MiniLM-L6-v2",
    "dimension": 384
}
TTL: 24시간
```

**적용 위치:**
- `CachedEmbeddingSearch.find_similar_functions_cached()`
- 모든 Pod가 동일한 캐시 공유

**예상 효과:**
- 멀티 Pod 환경에서 캐시 히트율 증가
- 임베딩 계산 시간: 5-10초 → 0.1초
- CPU 사용량 감소

---

### 4. Task Queue (비동기 처리)

#### 문제점
```python
# app/main.py:111
@app.route('/webhook', methods=['POST'])
def webhook_handler():
    # 동기 처리 (30-120초 소요)
    result = issue_processor.process_issue(issue)
    return jsonify({'status': 'processing', 'result': result}), 200
```

**현재 문제:**
- Webhook 응답 지연 (Jira 타임아웃 위험)
- 처리 중 오류 시 재시도 불가
- 부하 분산 불가

#### 해결 방안

**Redis Queue 도입:**

```python
# Option 1: Python RQ (추천 - 간단함)
from redis import Redis
from rq import Queue

redis_conn = Redis(host='localhost', port=6379)
task_queue = Queue('sdb_tasks', connection=redis_conn)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    payload = request.get_json()
    issue = payload.get('issue', {})

    # 큐에 작업 추가 (0.01초)
    job = task_queue.enqueue(
        'app.issue_processor.process_issue',
        issue,
        job_timeout='30m',  # 최대 30분
        result_ttl=86400    # 결과 보존 24시간
    )

    return jsonify({
        'status': 'queued',
        'job_id': job.id,
        'issue_key': issue.get('key')
    }), 202  # Accepted

# Worker 실행 (별도 프로세스)
# $ rq worker sdb_tasks --url redis://localhost:6379
```

**작업 상태 조회 API:**
```python
@app.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = task_queue.fetch_job(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify({
        'job_id': job.id,
        'status': job.get_status(),  # queued, started, finished, failed
        'result': job.result,
        'created_at': job.created_at.isoformat(),
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'ended_at': job.ended_at.isoformat() if job.ended_at else None
    })
```

**예상 효과:**
- Webhook 응답: 30-120초 → 0.1초 (즉시 응답)
- 안정성: 재시도, 실패 처리 자동화
- 확장성: Worker 수평 확장 가능
- 모니터링: 작업 상태 추적

---

### 5. Rate Limiting & Circuit Breaker

#### 목적
- OpenAI API Rate Limit 보호
- Bitbucket API Rate Limit 보호
- 장애 격리 (Circuit Breaker)

#### 구현 방안

**Rate Limiting (Sliding Window):**
```python
import redis
import time

class RateLimiter:
    def __init__(self, redis_client, key_prefix="rate_limit"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    def check_rate_limit(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Sliding Window Rate Limiting

        Args:
            identifier: 제한 대상 (예: "openai_api", "user_123")
            max_requests: 허용 요청 수
            window_seconds: 시간 창 (초)

        Returns:
            True if allowed, False if rate limited
        """
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        # Lua script로 원자적 연산 보장
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])

        -- 오래된 요청 제거
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

        -- 현재 요청 수 확인
        local current_count = redis.call('ZCARD', key)

        if current_count < max_requests then
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, ARGV[4])
            return 1
        else
            return 0
        end
        """

        result = self.redis.eval(
            lua_script,
            1,
            key,
            now,
            window_start,
            max_requests,
            window_seconds
        )

        return bool(result)

# 사용 예제
rate_limiter = RateLimiter(redis_client)

# OpenAI API: 분당 60회 제한
if not rate_limiter.check_rate_limit("openai_api", max_requests=60, window_seconds=60):
    raise Exception("OpenAI API rate limit exceeded")

# Bitbucket API: 시간당 1000회 제한
if not rate_limiter.check_rate_limit("bitbucket_api", max_requests=1000, window_seconds=3600):
    raise Exception("Bitbucket API rate limit exceeded")
```

**Circuit Breaker:**
```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # 정상 동작
    OPEN = "open"          # 차단 (에러 많음)
    HALF_OPEN = "half_open"  # 테스트 중

class CircuitBreaker:
    def __init__(self, redis_client, service_name,
                 failure_threshold=5, timeout=60):
        """
        Args:
            failure_threshold: 연속 실패 횟수 임계값
            timeout: OPEN 상태 유지 시간 (초)
        """
        self.redis = redis_client
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout

        self.state_key = f"circuit:{service_name}:state"
        self.failure_key = f"circuit:{service_name}:failures"
        self.last_failure_key = f"circuit:{service_name}:last_failure"

    def call(self, func, *args, **kwargs):
        """Circuit Breaker를 통한 함수 호출"""
        state = self._get_state()

        if state == CircuitState.OPEN:
            # OPEN 상태: timeout 지났는지 확인
            last_failure = self.redis.get(self.last_failure_key)
            if last_failure and (time.time() - float(last_failure)) > self.timeout:
                # HALF_OPEN으로 전환
                self._set_state(CircuitState.HALF_OPEN)
            else:
                raise Exception(f"Circuit breaker OPEN for {self.service_name}")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _get_state(self) -> CircuitState:
        state = self.redis.get(self.state_key)
        if not state:
            return CircuitState.CLOSED
        return CircuitState(state.decode())

    def _set_state(self, state: CircuitState):
        self.redis.set(self.state_key, state.value)

    def _on_success(self):
        """호출 성공 시"""
        self.redis.delete(self.failure_key)
        if self._get_state() == CircuitState.HALF_OPEN:
            self._set_state(CircuitState.CLOSED)

    def _on_failure(self):
        """호출 실패 시"""
        failures = self.redis.incr(self.failure_key)
        self.redis.set(self.last_failure_key, time.time())

        if failures >= self.failure_threshold:
            self._set_state(CircuitState.OPEN)

# 사용 예제
openai_breaker = CircuitBreaker(redis_client, "openai_api", failure_threshold=5, timeout=60)

def call_openai_with_protection():
    return openai_breaker.call(
        lambda: client.chat.completions.create(...)
    )
```

---

## 구현 방안

### Phase 1: LLM 캐싱 (빠른 적용)

**목표:** 즉시 효과를 볼 수 있는 LLM 캐싱만 적용

#### 1. Redis 연결 설정

```python
# app/redis_client.py (신규)
import redis
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis 클라이언트 싱글톤"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Redis 연결 초기화"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )

            # 연결 테스트
            self.client.ping()
            logger.info(f"Redis 연결 성공: {redis_url}")
            self.available = True

        except Exception as e:
            logger.warning(f"Redis 연결 실패: {str(e)}")
            logger.warning("캐싱 없이 동작합니다")
            self.client = None
            self.available = False

    def get(self, key: str) -> Optional[str]:
        """키로 값 조회"""
        if not self.available:
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET 실패: {str(e)}")
            return None

    def set(self, key: str, value: str, ttl: int = None):
        """키에 값 저장"""
        if not self.available:
            return
        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET 실패: {str(e)}")

    def delete(self, *keys):
        """키 삭제"""
        if not self.available:
            return
        try:
            self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE 실패: {str(e)}")

# 싱글톤 인스턴스
redis_client = RedisClient()
```

#### 2. LLM Handler 수정

```python
# app/llm_handler.py 수정
import hashlib
import json
from app.redis_client import redis_client

class LLMHandler:
    def __init__(self):
        # ... 기존 코드 ...
        self.cache_enabled = redis_client.available
        logger.info(f"LLM 캐싱: {'활성화' if self.cache_enabled else '비활성화'}")

    def _generate_cache_key(self, prefix: str, content: str) -> str:
        """캐시 키 생성"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"llm:{prefix}:{self.model}:{content_hash}"

    def convert_issue_to_spec(self, issue: Dict) -> str:
        """
        Jira 이슈(ADF 형식)를 Spec_File.md 형식으로 변환 (캐싱 적용)
        """
        # 캐시 키 생성
        summary = issue.get('fields', {}).get('summary', '')
        description = json.dumps(issue.get('fields', {}).get('description', ''))
        cache_content = f"{summary}|{description}"
        cache_key = self._generate_cache_key("spec", cache_content)

        # 캐시 확인
        if self.cache_enabled:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"✓ Spec 변환 캐시 히트: {cache_key[:32]}...")
                try:
                    cached_data = json.loads(cached)
                    return cached_data['spec_content']
                except Exception as e:
                    logger.warning(f"캐시 데이터 파싱 실패: {str(e)}")

        # 캐시 미스 - LLM 호출
        logger.info(f"✗ Spec 변환 캐시 미스: LLM 호출")

        if not self.client:
            # Fallback 로직
            return f"# Material DB 명세서\n\n## 기본 정보\n- 요약: {summary}\n\n(상세 변환 실패)"

        try:
            # ... 기존 LLM 호출 로직 ...
            spec_content = response.choices[0].message.content

            # 캐시 저장
            if self.cache_enabled:
                cache_data = {
                    'spec_content': spec_content,
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model,
                    'tokens_used': response.usage.total_tokens if hasattr(response, 'usage') else 0
                }
                redis_client.set(
                    cache_key,
                    json.dumps(cache_data, ensure_ascii=False),
                    ttl=7*24*3600  # 7일
                )
                logger.info(f"✓ Spec 변환 결과 캐시 저장: {cache_key[:32]}...")

            return spec_content

        except Exception as e:
            logger.error(f"Spec 변환 실패: {str(e)}")
            return f"# Material DB 명세서\n\n## 기본 정보\n- 요약: {summary}\n\n(상세 변환 실패)"

    def generate_code_diff(self, file_path: str, current_content: str,
                          issue_description: str, project_context: Dict) -> List[Dict]:
        """
        파일 수정을 위한 diff 정보 생성 (캐싱 적용)
        """
        # 캐시 키 생성
        cache_content = f"{file_path}|{current_content[:500]}|{issue_description}"
        cache_key = self._generate_cache_key("diff", cache_content)

        # 캐시 확인
        if self.cache_enabled:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"✓ Code diff 캐시 히트: {cache_key[:32]}...")
                try:
                    cached_data = json.loads(cached)
                    return cached_data['modifications']
                except Exception as e:
                    logger.warning(f"캐시 데이터 파싱 실패: {str(e)}")

        # 캐시 미스 - LLM 호출
        logger.info(f"✗ Code diff 캐시 미스: LLM 호출")

        if not self.client:
            return self._mock_code_diff(current_content, issue_description)

        try:
            # ... 기존 LLM 호출 로직 ...
            modifications = result.get('modifications', [])

            # 캐시 저장
            if self.cache_enabled and modifications:
                cache_data = {
                    'modifications': modifications,
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model,
                    'file_path': file_path
                }
                redis_client.set(
                    cache_key,
                    json.dumps(cache_data, ensure_ascii=False),
                    ttl=24*3600  # 24시간
                )
                logger.info(f"✓ Code diff 결과 캐시 저장: {cache_key[:32]}...")

            return modifications

        except Exception as e:
            logger.error(f"코드 diff 생성 실패: {str(e)}")
            return self._mock_code_diff(current_content, issue_description)

    def generate_new_file(self, file_path: str, issue_description: str,
                         project_context: Dict) -> str:
        """
        새 파일 생성 (캐싱 적용)
        """
        # 캐시 키 생성
        cache_content = f"{file_path}|{issue_description}"
        cache_key = self._generate_cache_key("newfile", cache_content)

        # 캐시 확인
        if self.cache_enabled:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"✓ 새 파일 생성 캐시 히트: {cache_key[:32]}...")
                try:
                    cached_data = json.loads(cached)
                    return cached_data['file_content']
                except Exception as e:
                    logger.warning(f"캐시 데이터 파싱 실패: {str(e)}")

        # 캐시 미스 - LLM 호출
        logger.info(f"✗ 새 파일 생성 캐시 미스: LLM 호출")

        if not self.client:
            return self._mock_new_file(file_path, issue_description)

        try:
            # ... 기존 LLM 호출 로직 ...
            new_code = self._extract_code_from_response(response.choices[0].message.content)

            # 캐시 저장
            if self.cache_enabled:
                cache_data = {
                    'file_content': new_code,
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model,
                    'file_path': file_path
                }
                redis_client.set(
                    cache_key,
                    json.dumps(cache_data, ensure_ascii=False),
                    ttl=24*3600  # 24시간
                )
                logger.info(f"✓ 새 파일 생성 결과 캐시 저장: {cache_key[:32]}...")

            return new_code

        except Exception as e:
            logger.error(f"새 파일 생성 실패: {str(e)}")
            return self._mock_new_file(file_path, issue_description)
```

#### 3. requirements.txt 업데이트

```txt
# requirements.txt에 추가
redis>=5.0.0
hiredis>=2.2.0  # 성능 향상 (선택사항)
```

#### 4. 환경 변수 설정

```bash
# .env
REDIS_URL=redis://localhost:6379/0

# Kubernetes ConfigMap
REDIS_URL=redis://redis-service:6379/0
```

---

### Phase 2: Bitbucket API 캐싱

#### Bitbucket API 클라이언트 수정

```python
# app/bitbucket_api.py 수정
from app.redis_client import redis_client

class BitbucketAPI:
    def __init__(self, url: str, username: str, access_token: str, workspace: str, repository: str):
        # ... 기존 코드 ...
        self.cache_enabled = redis_client.available
        self.cache_ttl_file = 300  # 5분
        self.cache_ttl_branch = 60  # 1분

    def _get_cache_key(self, resource_type: str, *args) -> str:
        """캐시 키 생성"""
        key_parts = [
            "bb",
            resource_type,
            self.workspace,
            self.repository
        ] + list(args)
        return ":".join(key_parts)

    def get_file_content(self, file_path: str, branch: str = "master") -> Optional[str]:
        """
        파일 내용 가져오기 (캐싱 적용)
        """
        # 캐시 확인
        cache_key = self._get_cache_key("file", branch, file_path)

        if self.cache_enabled:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"✓ Bitbucket 파일 캐시 히트: {file_path}")
                return cached

        # 캐시 미스 - API 호출
        logger.info(f"✗ Bitbucket 파일 캐시 미스: {file_path}")

        try:
            url = f"{self.repo_base}/src/{branch}/{file_path}"
            response = self.make_bitbucket_request(url)

            if response.status_code == 404:
                logger.info(f"파일이 존재하지 않음: {file_path}")
                return None

            response.raise_for_status()
            content = response.text

            # 캐시 저장
            if self.cache_enabled:
                redis_client.set(cache_key, content, ttl=self.cache_ttl_file)
                logger.info(f"✓ Bitbucket 파일 캐시 저장: {file_path}")

            return content

        except Exception as e:
            logger.error(f"파일 읽기 실패: {str(e)}")
            raise

    def get_file_content_raw(self, file_path: str, branch: str = "master") -> Optional[bytes]:
        """
        파일 내용을 바이너리로 가져오기 (캐싱 적용)
        """
        # 바이너리는 base64 인코딩하여 캐시
        cache_key = self._get_cache_key("file_raw", branch, file_path)

        if self.cache_enabled:
            cached = redis_client.get(cache_key)
            if cached:
                logger.info(f"✓ Bitbucket 바이너리 파일 캐시 히트: {file_path}")
                import base64
                return base64.b64decode(cached)

        # 캐시 미스 - API 호출
        logger.info(f"✗ Bitbucket 바이너리 파일 캐시 미스: {file_path}")

        try:
            url = f"{self.repo_base}/src/{branch}/{file_path}"
            response = self.make_bitbucket_request(url)

            if response.status_code == 404:
                logger.info(f"파일이 존재하지 않음: {file_path}")
                return None

            response.raise_for_status()
            content = response.content

            # 캐시 저장 (base64 인코딩)
            if self.cache_enabled:
                import base64
                encoded = base64.b64encode(content).decode('ascii')
                redis_client.set(cache_key, encoded, ttl=self.cache_ttl_file)
                logger.info(f"✓ Bitbucket 바이너리 파일 캐시 저장: {file_path}")

            return content

        except Exception as e:
            logger.error(f"파일 읽기 실패 (바이너리): {str(e)}")
            raise

    def commit_file(self, branch: str, file_path: str, content: str,
                   message: str, parent_commit: Optional[str] = None) -> Dict:
        """
        파일 커밋 (캐시 무효화 적용)
        """
        # ... 기존 커밋 로직 ...
        result = # ... 커밋 실행 ...

        # 캐시 무효화
        if self.cache_enabled:
            cache_key_text = self._get_cache_key("file", branch, file_path)
            cache_key_raw = self._get_cache_key("file_raw", branch, file_path)
            redis_client.delete(cache_key_text, cache_key_raw)
            logger.info(f"✓ 캐시 무효화: {file_path}")

        return result

    def commit_multiple_files(self, branch: str, file_changes: List[Dict],
                             message: str, parent_commit: Optional[str] = None) -> Dict:
        """
        여러 파일을 한 번에 커밋 (캐시 무효화 적용)
        """
        # ... 기존 커밋 로직 ...
        result = # ... 커밋 실행 ...

        # 캐시 무효화
        if self.cache_enabled:
            cache_keys = []
            for file_change in file_changes:
                file_path = file_change['path']
                cache_keys.append(self._get_cache_key("file", branch, file_path))
                cache_keys.append(self._get_cache_key("file_raw", branch, file_path))

            if cache_keys:
                redis_client.delete(*cache_keys)
                logger.info(f"✓ 캐시 무효화: {len(cache_keys)}개 파일")

        return result
```

---

### Phase 3: 임베딩 캐싱

#### Redis 기반 임베딩 캐시

```python
# app/embedding_search.py 수정
from app.redis_client import redis_client
import pickle
import base64

class RedisEmbeddingSearch(EmbeddingBasedSearch):
    """Redis 기반 임베딩 검색 (멀티 Pod 공유)"""

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        super().__init__(model_name)
        self.cache_enabled = redis_client.available
        self.cache_ttl = 24 * 3600  # 24시간

    def find_similar_functions_cached(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        Redis 캐싱된 임베딩 사용
        """
        if not self.available:
            return []

        if not functions:
            return []

        try:
            # 캐시 키 생성
            cache_key = self._generate_cache_key(functions)
            redis_key = f"embedding:{self.model.__class__.__name__}:{cache_key}"

            # 캐시 확인
            function_embeddings = None
            if self.cache_enabled:
                cached = redis_client.get(redis_key)
                if cached:
                    logger.info(f"✓ 임베딩 캐시 히트: {cache_key[:16]}...")
                    try:
                        # base64 디코딩 후 pickle 역직렬화
                        pickled = base64.b64decode(cached)
                        cached_data = pickle.loads(pickled)

                        # 함수 개수 검증
                        if cached_data['count'] == len(functions):
                            function_embeddings = cached_data['embeddings']
                        else:
                            logger.warning("캐시 크기 불일치. 재계산")
                    except Exception as e:
                        logger.warning(f"캐시 데이터 파싱 실패: {str(e)}")

            # 캐시 미스 - 임베딩 계산
            if function_embeddings is None:
                logger.info(f"✗ 임베딩 캐시 미스: 계산 중...")
                function_texts = [
                    self._create_function_text(func)
                    for func in functions
                ]
                function_embeddings = self.model.encode(
                    function_texts,
                    convert_to_numpy=True,
                    show_progress_bar=len(functions) > 100
                )

                # 캐시 저장
                if self.cache_enabled:
                    cached_data = {
                        'embeddings': function_embeddings,
                        'count': len(functions),
                        'model': self.model.__class__.__name__,
                        'dimension': function_embeddings.shape[1]
                    }
                    # pickle 직렬화 후 base64 인코딩
                    pickled = pickle.dumps(cached_data)
                    encoded = base64.b64encode(pickled).decode('ascii')

                    redis_client.set(redis_key, encoded, ttl=self.cache_ttl)
                    logger.info(f"✓ 임베딩 캐시 저장: {cache_key[:16]}...")

            # 쿼리 임베딩 및 검색
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            similarities = self._cosine_similarity(
                query_embedding,
                function_embeddings
            )

            # 필터링 및 정렬
            valid_indices = np.where(similarities >= min_similarity)[0]
            if len(valid_indices) == 0:
                logger.warning(f"유사도 {min_similarity} 이상인 함수 없음")
                return []

            valid_similarities = similarities[valid_indices]
            top_k_in_valid = min(top_k, len(valid_indices))
            top_indices_in_valid = np.argsort(valid_similarities)[::-1][:top_k_in_valid]
            top_indices = valid_indices[top_indices_in_valid]

            results = []
            for idx in top_indices:
                result = functions[idx].copy()
                result['similarity_score'] = float(similarities[idx])
                results.append(result)

            logger.info(f"Redis 캐시 사용하여 {len(results)}개 유사 함수 발견")
            for i, func in enumerate(results, 1):
                logger.info(f"  {i}. {func['name']}: 유사도 {func['similarity_score']:.3f}")

            return results

        except Exception as e:
            logger.error(f"Redis 임베딩 검색 실패: {e}")
            # 폴백: 캐시 없이 검색
            return super().find_similar_functions(query, functions, top_k, min_similarity)

    def _generate_cache_key(self, functions: List[Dict]) -> str:
        """함수 리스트의 해시 생성 (캐시 키)"""
        import hashlib
        func_names = sorted([f['name'] for f in functions])
        key_str = ','.join(func_names)
        return hashlib.md5(key_str.encode()).hexdigest()

    def clear_cache(self):
        """캐시 삭제"""
        # Redis에서는 패턴 매칭으로 삭제
        if self.cache_enabled:
            # 주의: KEYS 명령은 프로덕션에서 성능 문제 발생 가능
            # 대안: SCAN 사용
            logger.warning("Redis 임베딩 캐시 삭제는 수동으로 수행하세요")
```

---

### Phase 4: Task Queue (비동기 처리)

#### Python RQ 설치 및 설정

```bash
# requirements.txt에 추가
rq>=1.15.0
```

#### Worker 코드

```python
# app/worker.py (신규)
"""
RQ Worker - 백그라운드 작업 처리
"""
import os
import logging
from redis import Redis
from rq import Worker, Queue, Connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 연결
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(redis_url)

if __name__ == '__main__':
    # Worker 시작
    with Connection(redis_conn):
        worker = Worker(['sdb_tasks'], connection=redis_conn)
        logger.info("RQ Worker 시작: sdb_tasks 큐 모니터링 중...")
        worker.work()
```

#### Main.py 수정

```python
# app/main.py 수정
from redis import Redis
from rq import Queue
import os

# Redis 연결
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_conn = Redis.from_url(redis_url)
task_queue = Queue('sdb_tasks', connection=redis_conn)

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """
    Jira 웹훅 핸들러 (비동기 처리)
    """
    try:
        payload = request.get_json()

        if not payload:
            logger.error("웹훅 페이로드가 비어있습니다.")
            return jsonify({'error': '페이로드가 없습니다.'}), 400

        webhook_event = payload.get('webhookEvent')
        issue = payload.get('issue', {})

        # 이슈 생성 이벤트이고 SDB 개발 요청인 경우에만 처리
        if webhook_event == 'jira:issue_created':
            issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', '')

            if 'SDB' in issue_type or 'SDB 개발' in issue.get('fields', {}).get('summary', ''):
                logger.info(f"SDB 개발 요청 감지: {issue.get('key')}")

                # 큐에 작업 추가 (즉시 응답)
                job = task_queue.enqueue(
                    'app.tasks.process_issue_task',  # 작업 함수
                    issue,  # 인자
                    job_timeout='30m',  # 최대 30분
                    result_ttl=86400,   # 결과 보존 24시간
                    failure_ttl=86400   # 실패 정보 보존 24시간
                )

                logger.info(f"작업 큐 추가 완료: {job.id}")

                return jsonify({
                    'status': 'queued',
                    'job_id': job.id,
                    'issue_key': issue.get('key'),
                    'message': '작업이 큐에 추가되었습니다. /job/<job_id>로 상태 확인 가능'
                }), 202  # 202 Accepted
            else:
                logger.info("SDB 개발 요청이 아닙니다. 무시합니다.")
                return jsonify({'status': 'ignored', 'reason': 'Not SDB issue'}), 200

        return jsonify({'status': 'ignored', 'reason': 'Not issue created event'}), 200

    except Exception as e:
        logger.error(f"웹훅 처리 중 오류 발생: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/job/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    작업 상태 조회 API
    """
    try:
        from rq.job import Job

        job = Job.fetch(job_id, connection=redis_conn)

        response = {
            'job_id': job.id,
            'status': job.get_status(),  # queued, started, finished, failed
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None,
        }

        if job.is_finished:
            response['result'] = job.result
        elif job.is_failed:
            response['error'] = str(job.exc_info)

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"작업 상태 조회 실패: {str(e)}")
        return jsonify({'error': 'Job not found'}), 404


@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    작업 목록 조회 API
    """
    try:
        from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

        # 진행 중인 작업
        started_registry = StartedJobRegistry('sdb_tasks', connection=redis_conn)
        started_jobs = started_registry.get_job_ids()

        # 완료된 작업
        finished_registry = FinishedJobRegistry('sdb_tasks', connection=redis_conn)
        finished_jobs = finished_registry.get_job_ids()

        # 실패한 작업
        failed_registry = FailedJobRegistry('sdb_tasks', connection=redis_conn)
        failed_jobs = failed_registry.get_job_ids()

        # 대기 중인 작업
        queued_jobs = task_queue.job_ids

        return jsonify({
            'queued': len(queued_jobs),
            'started': len(started_jobs),
            'finished': len(finished_jobs),
            'failed': len(failed_jobs),
            'queued_jobs': queued_jobs[:10],  # 최근 10개
            'started_jobs': started_jobs[:10],
            'finished_jobs': finished_jobs[:10],
            'failed_jobs': failed_jobs[:10]
        }), 200

    except Exception as e:
        logger.error(f"작업 목록 조회 실패: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

#### Tasks 모듈

```python
# app/tasks.py (신규)
"""
백그라운드 작업 함수들
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

def process_issue_task(issue: Dict) -> Dict:
    """
    이슈 처리 작업 (백그라운드)

    Args:
        issue: Jira 이슈 정보

    Returns:
        처리 결과
    """
    logger.info(f"백그라운드 작업 시작: {issue.get('key')}")

    # IssueProcessor 초기화 (Worker 프로세스에서 실행)
    from app.bitbucket_api import BitbucketAPI
    from app.llm_handler import LLMHandler
    from app.issue_processor import IssueProcessor
    import os

    bitbucket_api = BitbucketAPI(
        url=os.getenv('BITBUCKET_URL', 'https://api.bitbucket.org'),
        username=os.getenv('BITBUCKET_USERNAME', 'api_user'),
        access_token=os.getenv('BITBUCKET_ACCESS_TOKEN'),
        workspace=os.getenv('BITBUCKET_WORKSPACE', 'mit_dev'),
        repository=os.getenv('BITBUCKET_REPOSITORY', 'genw_new')
    )

    llm_handler = LLMHandler()
    issue_processor = IssueProcessor(bitbucket_api, llm_handler)

    # 이슈 처리 (기존 로직)
    result = issue_processor.process_issue(issue)

    logger.info(f"백그라운드 작업 완료: {issue.get('key')}")
    return result
```

#### Worker 실행 스크립트

```bash
# scripts/start_worker.sh
#!/bin/bash

# 환경 변수 로드
source .env

# RQ Worker 시작
echo "Starting RQ Worker..."
rq worker sdb_tasks --url $REDIS_URL --verbose
```

---

### Phase 5: Rate Limiting & Circuit Breaker

#### Rate Limiter 클래스

```python
# app/rate_limiter.py (신규)
"""
Redis 기반 Rate Limiter 및 Circuit Breaker
"""
import redis
import time
import logging
from enum import Enum
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding Window Rate Limiter"""

    def __init__(self, redis_client: redis.Redis, key_prefix="rate_limit"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    def check_rate_limit(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        """
        Sliding Window Rate Limiting

        Args:
            identifier: 제한 대상 (예: "openai_api", "user_123")
            max_requests: 허용 요청 수
            window_seconds: 시간 창 (초)

        Returns:
            True if allowed, False if rate limited
        """
        key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        # Lua script로 원자적 연산 보장
        lua_script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window_start = tonumber(ARGV[2])
        local max_requests = tonumber(ARGV[3])
        local window_seconds = tonumber(ARGV[4])

        -- 오래된 요청 제거
        redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

        -- 현재 요청 수 확인
        local current_count = redis.call('ZCARD', key)

        if current_count < max_requests then
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, window_seconds)
            return 1
        else
            return 0
        end
        """

        try:
            result = self.redis.eval(
                lua_script,
                1,
                key,
                now,
                window_start,
                max_requests,
                window_seconds
            )
            return bool(result)
        except Exception as e:
            logger.error(f"Rate limit 체크 실패: {str(e)}")
            # 에러 시 허용 (Fail-open)
            return True

    def rate_limit(self, identifier: str, max_requests: int, window_seconds: int):
        """Rate Limiter 데코레이터"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not self.check_rate_limit(identifier, max_requests, window_seconds):
                    raise Exception(f"Rate limit exceeded for {identifier}")
                return func(*args, **kwargs)
            return wrapper
        return decorator


class CircuitState(Enum):
    CLOSED = "closed"      # 정상 동작
    OPEN = "open"          # 차단 (에러 많음)
    HALF_OPEN = "half_open"  # 테스트 중


class CircuitBreaker:
    """Circuit Breaker 패턴 구현"""

    def __init__(self, redis_client: redis.Redis, service_name: str,
                 failure_threshold: int = 5, timeout: int = 60):
        """
        Args:
            redis_client: Redis 클라이언트
            service_name: 서비스 이름
            failure_threshold: 연속 실패 횟수 임계값
            timeout: OPEN 상태 유지 시간 (초)
        """
        self.redis = redis_client
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout

        self.state_key = f"circuit:{service_name}:state"
        self.failure_key = f"circuit:{service_name}:failures"
        self.last_failure_key = f"circuit:{service_name}:last_failure"

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Circuit Breaker를 통한 함수 호출"""
        state = self._get_state()

        if state == CircuitState.OPEN:
            # OPEN 상태: timeout 지났는지 확인
            last_failure = self.redis.get(self.last_failure_key)
            if last_failure and (time.time() - float(last_failure)) > self.timeout:
                # HALF_OPEN으로 전환
                self._set_state(CircuitState.HALF_OPEN)
                logger.info(f"Circuit breaker {self.service_name}: OPEN -> HALF_OPEN")
            else:
                raise Exception(f"Circuit breaker OPEN for {self.service_name}")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _get_state(self) -> CircuitState:
        state = self.redis.get(self.state_key)
        if not state:
            return CircuitState.CLOSED
        return CircuitState(state.decode())

    def _set_state(self, state: CircuitState):
        self.redis.set(self.state_key, state.value)

    def _on_success(self):
        """호출 성공 시"""
        self.redis.delete(self.failure_key)
        current_state = self._get_state()
        if current_state == CircuitState.HALF_OPEN:
            self._set_state(CircuitState.CLOSED)
            logger.info(f"Circuit breaker {self.service_name}: HALF_OPEN -> CLOSED")

    def _on_failure(self):
        """호출 실패 시"""
        failures = self.redis.incr(self.failure_key)
        self.redis.set(self.last_failure_key, time.time())

        if failures >= self.failure_threshold:
            self._set_state(CircuitState.OPEN)
            logger.error(f"Circuit breaker {self.service_name}: CLOSED/HALF_OPEN -> OPEN (failures: {failures})")

    def circuit_breaker(self, func: Callable) -> Callable:
        """Circuit Breaker 데코레이터"""
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return self.call(func, *args, **kwargs)
        return wrapper


# 사용 예제
def example_usage():
    from app.redis_client import redis_client

    # Rate Limiter
    rate_limiter = RateLimiter(redis_client.client)

    @rate_limiter.rate_limit("openai_api", max_requests=60, window_seconds=60)
    def call_openai_api():
        # OpenAI API 호출
        pass

    # Circuit Breaker
    openai_breaker = CircuitBreaker(
        redis_client.client,
        "openai_api",
        failure_threshold=5,
        timeout=60
    )

    @openai_breaker.circuit_breaker
    def call_openai_with_protection():
        # OpenAI API 호출
        pass
```

#### LLM Handler에 적용

```python
# app/llm_handler.py에 추가
from app.rate_limiter import RateLimiter, CircuitBreaker
from app.redis_client import redis_client

class LLMHandler:
    def __init__(self):
        # ... 기존 코드 ...

        # Rate Limiter 설정
        if redis_client.available:
            self.rate_limiter = RateLimiter(redis_client.client)
            self.circuit_breaker = CircuitBreaker(
                redis_client.client,
                "openai_api",
                failure_threshold=5,
                timeout=60
            )
        else:
            self.rate_limiter = None
            self.circuit_breaker = None

    def _call_openai_with_protection(self, **kwargs):
        """Rate Limit 및 Circuit Breaker 적용된 OpenAI 호출"""

        # Rate Limit 체크
        if self.rate_limiter:
            if not self.rate_limiter.check_rate_limit(
                "openai_api",
                max_requests=60,  # 분당 60회
                window_seconds=60
            ):
                raise Exception("OpenAI API rate limit exceeded")

        # Circuit Breaker를 통한 호출
        if self.circuit_breaker:
            return self.circuit_breaker.call(
                lambda: self.client.chat.completions.create(**kwargs)
            )
        else:
            return self.client.chat.completions.create(**kwargs)

    def convert_issue_to_spec(self, issue: Dict) -> str:
        # ... 캐시 확인 로직 ...

        # LLM 호출 시 보호 적용
        response = self._call_openai_with_protection(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=self.max_tokens
        )

        # ... 나머지 로직 ...
```

---

## 배포 가이드

### 로컬 개발 환경

#### 1. Redis 설치 및 실행

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Docker
docker run -d -p 6379:6379 redis:7-alpine
```

#### 2. 환경 변수 설정

```bash
# .env
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
BITBUCKET_ACCESS_TOKEN=...
```

#### 3. 애플리케이션 실행

```bash
# Flask 앱 실행
python -m app.main

# RQ Worker 실행 (별도 터미널)
rq worker sdb_tasks --url redis://localhost:6379/0
```

---

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
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
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - BITBUCKET_ACCESS_TOKEN=${BITBUCKET_ACCESS_TOKEN}
      - BITBUCKET_WORKSPACE=${BITBUCKET_WORKSPACE}
      - BITBUCKET_REPOSITORY=${BITBUCKET_REPOSITORY}
    depends_on:
      redis:
        condition: service_healthy
    command: python -m app.main

  worker:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - BITBUCKET_ACCESS_TOKEN=${BITBUCKET_ACCESS_TOKEN}
      - BITBUCKET_WORKSPACE=${BITBUCKET_WORKSPACE}
      - BITBUCKET_REPOSITORY=${BITBUCKET_REPOSITORY}
    depends_on:
      redis:
        condition: service_healthy
    command: rq worker sdb_tasks --url redis://redis:6379/0 --verbose

volumes:
  redis_data:
```

**실행:**
```bash
docker-compose up -d
```

---

### Kubernetes 배포

#### 1. Redis Deployment

```yaml
# k8s/redis/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: agent-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
          name: redis
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --maxmemory
        - "2gb"
        - --maxmemory-policy
        - "allkeys-lru"  # LRU 정책
        volumeMounts:
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-data
        persistentVolumeClaim:
          claimName: redis-pvc
```

#### 2. Redis Service

```yaml
# k8s/redis/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: agent-system
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379
  type: ClusterIP
```

#### 3. Redis PVC

```yaml
# k8s/redis/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: agent-system
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: standard  # 클라우드 제공자에 따라 변경
```

#### 4. SDB Agent Deployment (Redis 연동)

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
      containers:
      - name: sdb-agent
        image: your-registry/sdb-agent:latest
        ports:
        - containerPort: 5000
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: OPENAI_API_KEY
        # ... 기타 환경 변수 ...
```

#### 5. RQ Worker Deployment

```yaml
# k8s/rq-worker/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rq-worker
  namespace: agent-system
  labels:
    app: rq-worker
spec:
  replicas: 3  # Worker 수
  selector:
    matchLabels:
      app: rq-worker
  template:
    metadata:
      labels:
        app: rq-worker
    spec:
      containers:
      - name: rq-worker
        image: your-registry/sdb-agent:latest
        command:
        - rq
        - worker
        - sdb_tasks
        - --url
        - redis://redis-service:6379/0
        - --verbose
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: OPENAI_API_KEY
        - name: BITBUCKET_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: agent-secrets
              key: BITBUCKET_ACCESS_TOKEN
        # ... 기타 환경 변수 ...
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
```

#### 6. HPA (Worker 자동 스케일링)

```yaml
# k8s/rq-worker/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: rq-worker-hpa
  namespace: agent-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: rq-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### 7. 배포 순서

```bash
# 1. Namespace
kubectl apply -f k8s/base/namespace.yaml

# 2. Secrets
kubectl create secret generic agent-secrets \
  --from-literal=OPENAI_API_KEY='sk-...' \
  --from-literal=BITBUCKET_ACCESS_TOKEN='your-token' \
  -n agent-system

# 3. Redis
kubectl apply -f k8s/redis/pvc.yaml
kubectl apply -f k8s/redis/deployment.yaml
kubectl apply -f k8s/redis/service.yaml

# 4. SDB Agent (Redis 연동)
kubectl apply -f k8s/sdb-agent/deployment.yaml
kubectl apply -f k8s/sdb-agent/service.yaml

# 5. RQ Worker
kubectl apply -f k8s/rq-worker/deployment.yaml
kubectl apply -f k8s/rq-worker/hpa.yaml

# 6. 상태 확인
kubectl get pods -n agent-system
```

---

### Redis Cluster (고가용성)

프로덕션 환경에서는 Redis Cluster 또는 Sentinel 권장:

```yaml
# Helm으로 Redis Cluster 배포
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install redis bitnami/redis-cluster \
  --namespace agent-system \
  --set cluster.nodes=6 \
  --set cluster.replicas=1 \
  --set persistence.size=10Gi \
  --set password=your-redis-password
```

---

## 성능 측정

### 캐시 히트율 모니터링

```python
# app/metrics.py (신규)
"""
Redis 캐시 메트릭 수집
"""
from prometheus_client import Counter, Histogram, Gauge

# 캐시 메트릭
cache_hits = Counter('cache_hits_total', 'Total cache hits', ['cache_type'])
cache_misses = Counter('cache_misses_total', 'Total cache misses', ['cache_type'])
cache_size = Gauge('cache_size_bytes', 'Cache size in bytes', ['cache_type'])

# API 호출 메트릭
api_calls = Counter('api_calls_total', 'Total API calls', ['service', 'status'])
api_duration = Histogram('api_duration_seconds', 'API call duration', ['service'])

# 작업 큐 메트릭
queue_size = Gauge('queue_size', 'Number of jobs in queue', ['queue_name'])
job_duration = Histogram('job_duration_seconds', 'Job processing duration', ['job_type'])

def record_cache_hit(cache_type: str):
    cache_hits.labels(cache_type=cache_type).inc()

def record_cache_miss(cache_type: str):
    cache_misses.labels(cache_type=cache_type).inc()

def record_api_call(service: str, status: str, duration: float):
    api_calls.labels(service=service, status=status).inc()
    api_duration.labels(service=service).observe(duration)
```

### Grafana 대시보드

**주요 메트릭:**

1. **캐시 히트율**
   ```promql
   rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
   ```

2. **API 호출 절감율**
   ```promql
   100 - (rate(api_calls_total{status="success"}[5m]) / rate(cache_misses_total[5m]) * 100)
   ```

3. **평균 응답 시간**
   ```promql
   rate(api_duration_seconds_sum[5m]) / rate(api_duration_seconds_count[5m])
   ```

4. **작업 큐 크기**
   ```promql
   queue_size{queue_name="sdb_tasks"}
   ```

---

## 트러블슈팅

### 1. Redis 연결 실패

**증상:**
```
Redis 연결 실패: Connection refused
```

**해결:**
```bash
# Redis 상태 확인
kubectl get pods -n agent-system | grep redis

# Redis 로그 확인
kubectl logs -f redis-<pod-id> -n agent-system

# Redis 연결 테스트
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli ping
```

---

### 2. 캐시 메모리 부족

**증상:**
```
OOM command not allowed when used memory > 'maxmemory'
```

**해결:**
```bash
# Redis maxmemory 설정 확인
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli CONFIG GET maxmemory

# maxmemory-policy 확인
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli CONFIG GET maxmemory-policy

# LRU 정책으로 변경
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

### 3. Worker 과부하

**증상:**
```
작업 처리 지연, 큐 크기 증가
```

**해결:**
```bash
# Worker 수 증가
kubectl scale deployment rq-worker --replicas=5 -n agent-system

# Worker 로그 확인
kubectl logs -f deployment/rq-worker -n agent-system

# 작업 큐 상태 확인
curl http://sdb-agent-service:5000/jobs
```

---

### 4. 캐시 데이터 손상

**증상:**
```
캐시 데이터 파싱 실패
```

**해결:**
```bash
# 특정 캐시 키 삭제
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli DEL "llm:spec:..."

# 모든 캐시 초기화 (주의!)
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli FLUSHDB
```

---

### 5. Rate Limit 오작동

**증상:**
```
정상 요청이 차단됨
```

**해결:**
```bash
# Rate Limit 카운터 확인
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli ZCARD "rate_limit:openai_api"

# Rate Limit 초기화
kubectl exec -it redis-<pod-id> -n agent-system -- redis-cli DEL "rate_limit:openai_api"
```

---

## 성능 벤치마크 예상

### Before Redis (현재)

| 작업 | 평균 시간 | API 호출 | 비용 |
|------|----------|---------|------|
| Spec 변환 | 15초 | 1회 | $0.05 |
| Code Diff 생성 | 20초 | 1회 | $0.08 |
| 파일 읽기 (5개) | 5초 | 5회 | - |
| 전체 처리 | 60-120초 | 10-15회 | $0.50 |

**일일 100건 처리 시:**
- 총 처리 시간: 100-200분
- API 비용: $50/일
- Bitbucket API 호출: 1000-1500회/일

---

### After Redis (예상)

| 작업 | 평균 시간 | API 호출 | 비용 | 개선율 |
|------|----------|---------|------|--------|
| Spec 변환 (캐시) | 0.01초 | 0.1회 (10% 미스) | $0.005 | **99.9%↑** |
| Code Diff 생성 (캐시) | 0.01초 | 0.2회 (20% 미스) | $0.016 | **99.9%↑** |
| 파일 읽기 (5개, 캐시) | 0.05초 | 1회 (80% 히트) | - | **99%↑** |
| 전체 처리 (큐) | 0.1초 (응답) | 3-5회 | $0.10 | **600-1200배↑** |

**일일 100건 처리 시:**
- Webhook 응답: 10초 (즉시)
- 실제 처리 시간: 30-60분 (백그라운드)
- API 비용: $10/일 (**80% 절감**)
- Bitbucket API 호출: 200-300회/일 (**70% 절감**)

---

## 참고 자료

### Redis 공식 문서
- [Redis Documentation](https://redis.io/docs/)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Redis Persistence](https://redis.io/docs/manual/persistence/)

### Python RQ
- [Python RQ Documentation](https://python-rq.org/)
- [RQ Patterns](https://python-rq.org/patterns/)

### Prometheus & Grafana
- [Prometheus Redis Exporter](https://github.com/oliver006/redis_exporter)
- [RQ Dashboard](https://github.com/Parallels/rq-dashboard)

### 관련 내부 문서
- [MULTI_AGENT_ARCHITECTURE.md](./MULTI_AGENT_ARCHITECTURE.md) - 멀티 Agent 아키텍처
- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md) - Docker 배포
- [PROCESS_FLOW.md](./PROCESS_FLOW.md) - 전체 프로세스

---

## 다음 단계

### 단계별 적용 로드맵

#### Week 1: LLM 캐싱
- [ ] Redis 연결 설정
- [ ] LLM Handler 캐싱 적용
- [ ] 로컬 테스트
- [ ] 성능 측정

#### Week 2: Bitbucket 캐싱
- [ ] Bitbucket API 캐싱 적용
- [ ] 캐시 무효화 로직
- [ ] 통합 테스트

#### Week 3: Task Queue
- [ ] RQ Worker 설정
- [ ] Webhook 비동기 처리
- [ ] 작업 상태 API
- [ ] Worker 모니터링

#### Week 4: 프로덕션 배포
- [ ] Kubernetes 배포
- [ ] Redis Cluster 구성
- [ ] 모니터링 대시보드
- [ ] 부하 테스트

---

**문서 버전**: 1.0.0
**최종 업데이트**: 2025-10-16
**작성자**: Development Team
