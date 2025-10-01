"""
임베딩 기반 유사 함수 검색 (Vector DB 불필요)
"""

import numpy as np
from typing import List, Dict, Optional
import logging
import os
import pickle
import hashlib

logger = logging.getLogger(__name__)


class EmbeddingBasedSearch:
    """메모리 기반 임베딩 검색 (Vector DB 불필요)"""

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Args:
            model_name: 임베딩 모델
                - all-MiniLM-L6-v2: 빠르고 가벼움 (384차원, 80MB) - 추천
                - all-mpnet-base-v2: 더 정확 (768차원, 420MB)
                - paraphrase-multilingual-MiniLM-L12-v2: 다국어 (한국어 지원)
        """
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"임베딩 모델 로딩 중: {model_name}")
            self.model = SentenceTransformer(model_name)
            self.available = True
            logger.info(f"임베딩 모델 로드 완료 (차원: {self.model.get_sentence_embedding_dimension()})")
        except ImportError:
            logger.warning("sentence-transformers 미설치. 임베딩 검색 비활성화")
            logger.warning("설치: pip install sentence-transformers")
            self.available = False
            self.model = None
        except Exception as e:
            logger.error(f"임베딩 모델 로드 실패: {e}")
            self.available = False
            self.model = None

    def find_similar_functions(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        유사한 함수 찾기 (Vector DB 없이 메모리 상에서 처리)

        Args:
            query: 검색 쿼리 (예: "SP16_2017_tB3 재질 DB 추가")
            functions: 함수 리스트 (extract_functions 결과)
            top_k: 반환할 개수
            min_similarity: 최소 유사도 (0.0 ~ 1.0)

        Returns:
            유사도 높은 함수 top_k개 (similarity_score 포함)
        """
        if not self.available:
            logger.warning("임베딩 모델 사용 불가. 빈 리스트 반환")
            return []

        if not functions:
            return []

        try:
            # 1. 쿼리 임베딩
            logger.info(f"쿼리 임베딩 중: '{query}'")
            query_embedding = self.model.encode(query, convert_to_numpy=True)

            # 2. 모든 함수 임베딩 (메모리 상에서)
            logger.info(f"{len(functions)}개 함수 임베딩 중...")
            function_texts = [
                self._create_function_text(func)
                for func in functions
            ]
            function_embeddings = self.model.encode(
                function_texts,
                convert_to_numpy=True,
                show_progress_bar=len(functions) > 100
            )

            # 3. 코사인 유사도 계산
            similarities = self._cosine_similarity(
                query_embedding,
                function_embeddings
            )

            # 4. 최소 유사도 필터링
            valid_indices = np.where(similarities >= min_similarity)[0]
            if len(valid_indices) == 0:
                logger.warning(f"유사도 {min_similarity} 이상인 함수 없음")
                return []

            # 5. 상위 k개 선택
            valid_similarities = similarities[valid_indices]
            top_k_in_valid = min(top_k, len(valid_indices))
            top_indices_in_valid = np.argsort(valid_similarities)[::-1][:top_k_in_valid]
            top_indices = valid_indices[top_indices_in_valid]

            results = []
            for idx in top_indices:
                result = functions[idx].copy()
                result['similarity_score'] = float(similarities[idx])
                results.append(result)

            logger.info(f"상위 {len(results)}개 유사 함수 발견")
            for i, func in enumerate(results, 1):
                logger.info(f"  {i}. {func['name']}: 유사도 {func['similarity_score']:.3f}")

            return results

        except Exception as e:
            logger.error(f"임베딩 검색 실패: {e}")
            return []

    def _create_function_text(self, func: Dict) -> str:
        """
        함수 정보를 텍스트로 변환 (임베딩용)

        중요: 어떤 정보를 포함시키느냐가 검색 품질을 결정
        """
        text_parts = []

        # 함수 이름 (필수)
        text_parts.append(func['name'])

        # 시그니처 (있으면 추가)
        if 'signature' in func:
            text_parts.append(func['signature'])
        elif 'qualified_name' in func:
            text_parts.append(func['qualified_name'])

        # 주석 추출 (함수 설명)
        if 'content' in func:
            content = func['content']
            lines = content.split('\n')[:20]  # 처음 20줄만

            comments = []
            for line in lines:
                stripped = line.strip()
                # 주석 라인 추출
                if stripped.startswith('//'):
                    comments.append(stripped[2:].strip())
                elif stripped.startswith('/*'):
                    comments.append(stripped[2:].strip())
                elif '*/' in stripped:
                    break

            if comments:
                text_parts.extend(comments[:5])  # 최대 5줄 주석

        return ' '.join(text_parts)

    def _cosine_similarity(
        self,
        query_vec: np.ndarray,
        doc_vecs: np.ndarray
    ) -> np.ndarray:
        """
        코사인 유사도 계산

        Args:
            query_vec: 쿼리 벡터 (D,)
            doc_vecs: 문서 벡터들 (N, D)

        Returns:
            유사도 배열 (N,)
        """
        # 정규화 (L2 norm)
        query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-10)

        # 내적 = 코사인 유사도 (정규화된 벡터)
        similarities = np.dot(doc_norms, query_norm)

        return similarities


class CachedEmbeddingSearch(EmbeddingBasedSearch):
    """임베딩 결과 캐싱 (Vector DB 대신 파일 캐시 사용)"""

    def __init__(self, model_name='all-MiniLM-L6-v2', cache_dir='.embedding_cache'):
        """
        Args:
            model_name: 임베딩 모델
            cache_dir: 캐시 저장 디렉토리
        """
        super().__init__(model_name)
        self.cache_dir = cache_dir
        if self.available:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"임베딩 캐시 디렉토리: {cache_dir}")

    def find_similar_functions_cached(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """
        캐싱된 임베딩 사용

        Args:
            query: 검색 쿼리
            functions: 함수 리스트
            top_k: 반환할 개수
            min_similarity: 최소 유사도

        Returns:
            유사 함수 리스트
        """
        if not self.available:
            return []

        if not functions:
            return []

        try:
            # 캐시 키 생성
            cache_key = self._generate_cache_key(functions)
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")

            # 캐시 확인
            if os.path.exists(cache_path):
                logger.info(f"캐시에서 임베딩 로드: {cache_key[:8]}...")
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                    function_embeddings = cached_data['embeddings']
                    # 함수 리스트 검증
                    if len(function_embeddings) != len(functions):
                        logger.warning("캐시 크기 불일치. 재계산")
                        raise ValueError("Cache size mismatch")
            else:
                # 임베딩 계산
                logger.info(f"임베딩 계산 중... (캐시 없음)")
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
                cached_data = {
                    'embeddings': function_embeddings,
                    'count': len(functions)
                }
                with open(cache_path, 'wb') as f:
                    pickle.dump(cached_data, f)
                logger.info(f"임베딩 캐시 저장: {cache_key[:8]}...")

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

            logger.info(f"캐시 사용하여 {len(results)}개 유사 함수 발견")
            for i, func in enumerate(results, 1):
                logger.info(f"  {i}. {func['name']}: 유사도 {func['similarity_score']:.3f}")

            return results

        except Exception as e:
            logger.error(f"캐싱된 임베딩 검색 실패: {e}")
            # 폴백: 캐시 없이 검색
            return super().find_similar_functions(query, functions, top_k, min_similarity)

    def _generate_cache_key(self, functions: List[Dict]) -> str:
        """함수 리스트의 해시 생성 (캐시 키)"""
        # 함수 이름들을 정렬하여 해시
        func_names = sorted([f['name'] for f in functions])
        key_str = ','.join(func_names)
        return hashlib.md5(key_str.encode()).hexdigest()

    def clear_cache(self):
        """캐시 삭제"""
        if os.path.exists(self.cache_dir):
            import shutil
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir)
            logger.info("임베딩 캐시 삭제 완료")


class MemoryCachedSearch(EmbeddingBasedSearch):
    """메모리 캐싱 (세션 동안만 유지)"""

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        super().__init__(model_name)
        self._embedding_cache = {}

    def find_similar_functions(
        self,
        query: str,
        functions: List[Dict],
        top_k: int = 3,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """메모리 캐싱 사용"""
        if not self.available:
            return []

        if not functions:
            return []

        try:
            # 함수 리스트 해시
            cache_key = self._hash_functions(functions)

            # 캐시 확인
            if cache_key not in self._embedding_cache:
                logger.info("새로운 임베딩 계산 (메모리 캐시)")
                function_texts = [
                    self._create_function_text(func)
                    for func in functions
                ]
                embeddings = self.model.encode(
                    function_texts,
                    convert_to_numpy=True
                )
                self._embedding_cache[cache_key] = embeddings
            else:
                logger.info("메모리 캐시에서 임베딩 로드")
                embeddings = self._embedding_cache[cache_key]

            # 검색
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            similarities = self._cosine_similarity(query_embedding, embeddings)

            # 필터링 및 정렬
            valid_indices = np.where(similarities >= min_similarity)[0]
            if len(valid_indices) == 0:
                return []

            valid_similarities = similarities[valid_indices]
            top_k_in_valid = min(top_k, len(valid_indices))
            top_indices_in_valid = np.argsort(valid_similarities)[::-1][:top_k_in_valid]
            top_indices = valid_indices[top_indices_in_valid]

            results = [
                {**functions[idx], 'similarity_score': float(similarities[idx])}
                for idx in top_indices
            ]

            return results

        except Exception as e:
            logger.error(f"메모리 캐싱 검색 실패: {e}")
            return []

    def _hash_functions(self, functions: List[Dict]) -> str:
        """함수 리스트 해시"""
        return '|'.join(sorted([f['name'] for f in functions]))

    def clear_cache(self):
        """메모리 캐시 삭제"""
        self._embedding_cache.clear()
        logger.info("메모리 캐시 삭제 완료")
