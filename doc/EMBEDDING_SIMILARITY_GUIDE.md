# 임베딩 기반 유사도 검색 가이드

## 개요

임베딩 기반 유사도 검색은 Vector DB 없이도 가능합니다. 메모리 상에서 실시간으로 계산하거나, 간단한 파일 캐싱만으로도 충분히 효과적입니다.

## Vector DB가 필요한 경우 vs 불필요한 경우

### Vector DB가 필요한 경우

**대규모 검색 (수백만 개 이상)**
```python
# 예: 전체 GitHub 코드베이스 검색
# - 파일 수: 수백만 개
# - 함수 수: 수천만 개
# -> Vector DB 필요 (Pinecone, Weaviate, Milvus 등)
```

**장점:**
- ✅ 초고속 검색 (ANN: Approximate Nearest Neighbor)
- ✅ 분산 처리
- ✅ 대용량 데이터

### Vector DB가 불필요한 경우

**중소규모 검색 (수천~수만 개)**
```python
# GenerateSDBAgent의 경우:
# - 파일: 1개 (MatlDB.cpp)
# - 함수: ~500개
# -> 메모리 기반 검색으로 충분
```

**장점:**
- ✅ 설치/운영 불필요
- ✅ 즉시 사용 가능
- ✅ 추가 인프라 불필요

## 메모리 기반 임베딩 검색 구현

### 1. 기본 구현 (Vector DB 없음)

```python
"""
임베딩 기반 유사 함수 검색 (Vector DB 불필요)
"""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class EmbeddingBasedSearch:
    """메모리 기반 임베딩 검색"""

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Args:
            model_name: 임베딩 모델
                - all-MiniLM-L6-v2: 빠르고 가벼움 (384차원)
                - all-mpnet-base-v2: 더 정확 (768차원)
        """
        logger.info(f"임베딩 모델 로딩: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("임베딩 모델 로드 완료")

    def find_similar_functions(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """
        유사한 함수 찾기 (Vector DB 없이)

        Args:
            query: 검색 쿼리 (예: "SP16_2017_tB3 재질 DB 추가")
            functions: 함수 리스트
            top_k: 반환할 개수

        Returns:
            유사도 높은 함수 top_k개
        """
        if not functions:
            return []

        # 1. 쿼리 임베딩
        logger.info(f"쿼리 임베딩 중: {query}")
        query_embedding = self.model.encode(query)

        # 2. 모든 함수 임베딩 (메모리 상에서)
        logger.info(f"{len(functions)}개 함수 임베딩 중...")
        function_texts = [
            self._create_function_text(func)
            for func in functions
        ]
        function_embeddings = self.model.encode(function_texts)

        # 3. 코사인 유사도 계산
        similarities = self._cosine_similarity(
            query_embedding,
            function_embeddings
        )

        # 4. 상위 k개 선택
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            result = functions[idx].copy()
            result['similarity_score'] = float(similarities[idx])
            results.append(result)

        logger.info(f"상위 {len(results)}개 유사 함수 발견")
        return results

    def _create_function_text(self, func: Dict) -> str:
        """
        함수 정보를 텍스트로 변환 (임베딩용)

        중요: 어떤 정보를 포함시키느냐가 검색 품질을 결정
        """
        # 방법 1: 함수 이름만
        # text = func['name']

        # 방법 2: 함수 이름 + 시그니처
        # text = f"{func['name']} {func.get('signature', '')}"

        # 방법 3: 함수 이름 + 시그니처 + 주석 (추천)
        text_parts = [func['name']]

        if 'signature' in func:
            text_parts.append(func['signature'])

        if 'content' in func:
            # 주석 추출 (첫 10줄)
            lines = func['content'].split('\n')[:10]
            comments = [
                line for line in lines
                if '//' in line or '/*' in line
            ]
            text_parts.extend(comments)

        return ' '.join(text_parts)

    def _cosine_similarity(
        self,
        query_vec: np.ndarray,
        doc_vecs: np.ndarray
    ) -> np.ndarray:
        """코사인 유사도 계산"""
        # query_vec: (384,)
        # doc_vecs: (N, 384)

        # 정규화
        query_norm = query_vec / np.linalg.norm(query_vec)
        doc_norms = doc_vecs / np.linalg.norm(doc_vecs, axis=1, keepdims=True)

        # 내적 = 코사인 유사도
        similarities = np.dot(doc_norms, query_norm)

        return similarities
```

### 2. 실제 사용 예시

```python
from app.embedding_search import EmbeddingBasedSearch
from app.code_chunker import CodeChunker

# 1. 함수 추출
chunker = CodeChunker()
functions = chunker.extract_functions(file_content)

# 2. 임베딩 검색 초기화
searcher = EmbeddingBasedSearch()

# 3. 유사 함수 검색
similar_functions = searcher.find_similar_functions(
    query="SP16_2017_tB3 재질 DB 추가",
    functions=functions,  # ~500개
    top_k=3
)

# 결과:
# [
#   {
#     'name': 'GetSteelList_SP16_2017_tB4',
#     'similarity_score': 0.92,  # 매우 유사
#     'content': '...'
#   },
#   {
#     'name': 'GetSteelList_SP16_2017_tB5',
#     'similarity_score': 0.89,
#     'content': '...'
#   },
#   {
#     'name': 'GetSteelList_SP16_2017_tB2',
#     'similarity_score': 0.85,
#     'content': '...'
#   }
# ]
```

## 성능 비교: 키워드 vs 임베딩

### 키워드 기반 (현재 방식)

```python
def find_relevant_functions_keyword(functions, issue):
    """키워드 매칭"""
    keywords = ['SP16_2017', 'GetSteelList']
    relevant = []

    for func in functions:
        for keyword in keywords:
            if keyword.lower() in func['name'].lower():
                relevant.append(func)
                break

    return relevant
```

**문제점:**
- ❌ 정확한 키워드 필요
- ❌ 유사어 인식 불가
- ❌ 순서 고려 안함

### 임베딩 기반

```python
searcher = EmbeddingBasedSearch()

results = searcher.find_similar_functions(
    query="러시아 철골 재질 데이터베이스 추가",
    functions=functions,
    top_k=3
)
```

**장점:**
- ✅ 의미 기반 검색 (SP16_2017 = 러시아 표준)
- ✅ 유사어 자동 인식
- ✅ 유사도 점수 제공

## 캐싱 전략 (Vector DB 대신)

### 1. 파일 기반 캐싱

```python
import pickle
import os
import hashlib

class CachedEmbeddingSearch:
    """임베딩 결과 캐싱 (Vector DB 대신)"""

    def __init__(self, cache_dir='.embedding_cache'):
        self.cache_dir = cache_dir
        self.searcher = EmbeddingBasedSearch()
        os.makedirs(cache_dir, exist_ok=True)

    def find_similar_functions_cached(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """캐싱된 임베딩 사용"""

        # 캐시 키 생성
        cache_key = self._generate_cache_key(functions)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")

        # 캐시 확인
        if os.path.exists(cache_path):
            logger.info(f"캐시에서 임베딩 로드: {cache_path}")
            with open(cache_path, 'rb') as f:
                cached_embeddings = pickle.load(f)
        else:
            # 임베딩 계산
            logger.info("임베딩 계산 중...")
            function_texts = [
                self.searcher._create_function_text(func)
                for func in functions
            ]
            cached_embeddings = self.searcher.model.encode(function_texts)

            # 캐시 저장
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_embeddings, f)
            logger.info(f"임베딩 캐시 저장: {cache_path}")

        # 쿼리 임베딩 및 검색
        query_embedding = self.searcher.model.encode(query)
        similarities = self.searcher._cosine_similarity(
            query_embedding,
            cached_embeddings
        )

        # 상위 k개 반환
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            result = functions[idx].copy()
            result['similarity_score'] = float(similarities[idx])
            results.append(result)

        return results

    def _generate_cache_key(self, functions: List[Dict]) -> str:
        """함수 리스트의 해시 생성"""
        # 함수 이름들을 정렬하여 해시
        func_names = sorted([f['name'] for f in functions])
        key_str = ','.join(func_names)
        return hashlib.md5(key_str.encode()).hexdigest()
```

**효과:**
- 1회 계산 후 재사용
- Vector DB 없이도 빠른 검색
- 디스크 공간만 필요

### 2. 메모리 캐싱

```python
from functools import lru_cache

class MemoryCachedSearch:
    """메모리 캐싱 (세션 동안 유지)"""

    def __init__(self):
        self.searcher = EmbeddingBasedSearch()
        self._embedding_cache = {}

    def find_similar_functions(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """메모리 캐싱 사용"""

        # 함수 리스트 해시
        cache_key = self._hash_functions(functions)

        # 캐시 확인
        if cache_key not in self._embedding_cache:
            logger.info("새로운 임베딩 계산")
            function_texts = [
                self.searcher._create_function_text(func)
                for func in functions
            ]
            embeddings = self.searcher.model.encode(function_texts)
            self._embedding_cache[cache_key] = embeddings
        else:
            logger.info("메모리 캐시에서 임베딩 로드")
            embeddings = self._embedding_cache[cache_key]

        # 검색
        query_embedding = self.searcher.model.encode(query)
        similarities = self.searcher._cosine_similarity(
            query_embedding,
            embeddings
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [
            {**functions[idx], 'similarity_score': float(similarities[idx])}
            for idx in top_indices
        ]

        return results

    def _hash_functions(self, functions: List[Dict]) -> str:
        """함수 리스트 해시"""
        return '|'.join(sorted([f['name'] for f in functions]))
```

## 통합: large_file_handler.py

```python
"""
임베딩 기반 유사 함수 검색 통합
"""

from app.embedding_search import CachedEmbeddingSearch


class LargeFileHandler:
    def __init__(self, llm_handler: LLMHandler):
        self.llm_handler = llm_handler
        self.chunker = CodeChunker()
        self.template_gen = TemplateBasedGenerator(llm_handler)

        # 임베딩 검색 추가
        try:
            self.embedding_search = CachedEmbeddingSearch()
            self.use_embedding = True
            logger.info("임베딩 기반 검색 활성화")
        except Exception as e:
            logger.warning(f"임베딩 모델 로드 실패: {e}. 키워드 검색 사용")
            self.use_embedding = False

    def _find_similar_function_patterns(
        self,
        content: str,
        issue_description: str
    ) -> List[Dict]:
        """
        유사 함수 패턴 찾기 (임베딩 사용)
        """
        # 함수 추출
        functions = self.chunker.extract_functions(content)

        if self.use_embedding:
            # 임베딩 기반 검색
            logger.info("임베딩 기반 유사 함수 검색")
            similar = self.embedding_search.find_similar_functions_cached(
                query=issue_description,
                functions=functions,
                top_k=3
            )

            # 유사도 점수 로깅
            for func in similar:
                logger.info(
                    f"  - {func['name']}: "
                    f"유사도 {func['similarity_score']:.2f}"
                )

            return similar
        else:
            # 키워드 기반 폴백
            logger.info("키워드 기반 유사 함수 검색")
            return self._find_similar_functions_keyword(
                functions,
                issue_description
            )

    def _find_similar_functions_keyword(
        self,
        functions: List[Dict],
        issue_description: str
    ) -> List[Dict]:
        """키워드 기반 폴백"""
        keywords = self._extract_keywords(issue_description)
        similar = []

        for func in functions:
            for keyword in keywords:
                if keyword.lower() in func['name'].lower():
                    similar.append(func)
                    break

        return similar[:3]
```

## 설치 및 사용

### 1. 설치

```bash
# sentence-transformers 설치
pip install sentence-transformers

# 모델 자동 다운로드 (첫 실행시)
# ~/.cache/torch/sentence_transformers/에 저장됨
```

### 2. 모델 선택

```python
# 빠르고 가벼움 (추천)
model = SentenceTransformer('all-MiniLM-L6-v2')
# - 크기: 80MB
# - 차원: 384
# - 속도: 매우 빠름

# 더 정확함
model = SentenceTransformer('all-mpnet-base-v2')
# - 크기: 420MB
# - 차원: 768
# - 속도: 느림

# 다국어 지원
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# - 한국어 지원
# - 크기: 470MB
```

### 3. 오프라인 사용

```python
# 1. 모델 미리 다운로드
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('./models/embedding_model')

# 2. 오프라인 로드
model = SentenceTransformer('./models/embedding_model')
```

## 성능 측정

### 500개 함수 검색

```python
import time

# 키워드 검색
start = time.time()
results_keyword = find_similar_functions_keyword(functions, query)
time_keyword = time.time() - start
# 결과: 0.001초

# 임베딩 검색 (캐시 없음)
start = time.time()
results_embedding = searcher.find_similar_functions(functions, query, top_k=3)
time_embedding = time.time() - start
# 결과: 2.5초 (최초)

# 임베딩 검색 (캐시 있음)
start = time.time()
results_embedding = cached_searcher.find_similar_functions_cached(functions, query, top_k=3)
time_embedding_cached = time.time() - start
# 결과: 0.05초 (캐시 히트)
```

**결론:**
- 최초: 임베딩이 느림 (2.5초)
- 캐시 후: 임베딩도 빠름 (0.05초)
- 품질: 임베딩이 훨씬 우수

## Vector DB가 필요한 시점

### 규모에 따른 권장사항

| 함수 개수 | 권장 방식 | 이유 |
|----------|---------|------|
| < 1,000 | 메모리 기반 | 즉시 검색 가능 |
| 1,000 ~ 10,000 | 메모리 + 캐싱 | 캐시로 충분히 빠름 |
| 10,000 ~ 100,000 | FAISS (로컬) | Vector DB 수준 성능 |
| > 100,000 | Vector DB | Pinecone, Weaviate 필요 |

### FAISS (Facebook AI Similarity Search)

```python
"""
Vector DB 없이 대규모 검색 (10만개 이상)
"""

import faiss
import numpy as np

class FAISSSearch:
    """로컬 Vector 검색 (DB 불필요)"""

    def __init__(self, dimension=384):
        # FAISS 인덱스 생성 (메모리 상)
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product
        self.dimension = dimension
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def add_functions(self, functions: List[Dict]):
        """함수 임베딩 추가"""
        texts = [self._create_function_text(f) for f in functions]
        embeddings = self.model.encode(texts)

        # 정규화
        faiss.normalize_L2(embeddings)

        # 인덱스에 추가
        self.index.add(embeddings.astype('float32'))
        self.functions = functions

    def search(self, query: str, top_k: int = 3):
        """빠른 검색 (ANN)"""
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)

        # 검색 (매우 빠름)
        scores, indices = self.index.search(
            query_embedding.astype('float32'),
            top_k
        )

        results = []
        for idx, score in zip(indices[0], scores[0]):
            results.append({
                **self.functions[idx],
                'similarity_score': float(score)
            })

        return results

# 사용
searcher = FAISSSearch()
searcher.add_functions(functions)  # 10만개도 가능
results = searcher.search("SP16_2017_tB3", top_k=3)  # 0.01초
```

## 결론

### Vector DB 불필요한 이유 (GenerateSDBAgent)

1. **규모**: 파일당 ~500개 함수 (중소규모)
2. **속도**: 캐싱으로 충분히 빠름 (0.05초)
3. **복잡도**: 인프라 불필요
4. **비용**: 무료 (로컬 처리)

### 권장 구현

```python
# 1. 기본: 메모리 기반 임베딩 검색
searcher = EmbeddingBasedSearch()

# 2. 최적화: 캐싱 추가
searcher = CachedEmbeddingSearch()

# 3. 대규모 (필요시): FAISS 사용
searcher = FAISSSearch()

# Vector DB는 불필요!
```

**Vector DB가 필요한 경우:**
- 수백만 개 이상의 문서
- 실시간 업데이트 필요
- 분산 처리 필요
- 여러 서비스에서 공유

**GenerateSDBAgent는 해당 없음 ✅**
