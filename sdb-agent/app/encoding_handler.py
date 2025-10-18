"""
인코딩 감지 및 변환 처리
파일의 원본 인코딩을 유지하면서 안전하게 디코딩/인코딩
"""

import chardet
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class EncodingHandler:
    """파일 인코딩 감지 및 변환 처리"""

    @staticmethod
    def detect_encoding(content_bytes: bytes) -> str:
        """
        바이너리 데이터에서 인코딩 감지

        Args:
            content_bytes: 바이너리 파일 내용

        Returns:
            감지된 인코딩 (예: 'utf-8', 'euc-kr', 'cp949')
        """
        if not content_bytes:
            logger.warning("빈 파일, UTF-8 기본값 사용")
            return 'utf-8'

        result = chardet.detect(content_bytes)
        detected_encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0.0)

        logger.info(f"인코딩 감지: {detected_encoding} (신뢰도: {confidence:.2f})")

        # CP949와 EUC-KR은 거의 동일하므로 통일
        if detected_encoding and detected_encoding.lower() in ['euc-kr', 'euc_kr']:
            detected_encoding = 'cp949'
            logger.info("EUC-KR을 CP949로 변환")

        return detected_encoding or 'utf-8'

    @staticmethod
    def detect_encoding_with_hint(content_bytes: bytes, file_path: str) -> str:
        """
        파일 확장자 힌트를 활용한 인코딩 감지

        Args:
            content_bytes: 바이너리 데이터
            file_path: 파일 경로

        Returns:
            감지된 인코딩
        """
        detected = chardet.detect(content_bytes)
        encoding = detected.get('encoding')
        confidence = detected.get('confidence', 0.0)
        
        logger.info(f"chardet 감지: {encoding} (신뢰도: {confidence:.2f}) - {file_path}")
        
        # EUC-KR을 CP949로 통일
        if encoding and encoding.lower() in ['euc-kr', 'euc_kr']:
            encoding = 'cp949'
            logger.info("EUC-KR을 CP949로 변환")
        
        # C++ 파일 특별 처리
        if file_path.endswith(('.cpp', '.h', '.c', '.cc', '.hpp')):
            # 한글 바이트 패턴 확인 (파일 크기에 따라 동적 조정, 최대 10KB)
            sample_size = min(len(content_bytes), 10240)  # 10KB
            has_korean = any(b > 0x7F for b in content_bytes[:sample_size])
            
            # ⭐ 주요 개선: 신뢰도 0.95 미만은 모두 의심!
            if confidence < 0.95:
                # ISO-8859-1, windows-1252 등은 false positive 주범
                suspicious_encodings = ['iso-8859-1', 'windows-1252', 'latin-1', 'ascii', 'utf-8']
                
                if encoding is None or encoding.lower() in [e.lower() for e in suspicious_encodings]:
                    if has_korean:
                        logger.info(f"C++ 파일 + 한글 감지 + 신뢰도 낮음({confidence:.2f}) + 의심스러운 인코딩({encoding}), CP949 시도")
                        return 'cp949'
                    else:
                        # 한글이 없으면 ASCII 호환 인코딩
                        logger.info(f"C++ 파일 + 한글 없음, 신뢰도 낮음({confidence:.2f}), CP949 시도 (fallback)")
                        return 'cp949'
            
            # 신뢰도가 높아도 ISO-8859-1이면 의심
            if encoding and encoding.lower() in ['iso-8859-1', 'windows-1252', 'latin-1']:
                if has_korean:
                    logger.warning(f"⚠️ ISO-8859-1 계열 감지 (신뢰도: {confidence:.2f}), 한글 있음 → CP949로 강제 변경")
                    return 'cp949'
        
        elif file_path.endswith(('.py', '.js', '.json', '.md')):
            logger.info(f"텍스트 파일 감지, UTF-8 사용")
            return 'utf-8'
        
        return encoding or 'utf-8'

    @staticmethod
    def decode_with_fallback(content_bytes: bytes, encoding: str = None) -> Tuple[str, str]:
        """
        바이너리를 문자열로 안전하게 디코딩

        Args:
            content_bytes: 바이너리 데이터
            encoding: 시도할 인코딩 (None이면 자동 감지)

        Returns:
            (디코딩된 문자열, 사용된 인코딩)
        """
        if not content_bytes:
            logger.warning("빈 바이너리 데이터")
            return "", "utf-8"

        if encoding is None:
            encoding = EncodingHandler.detect_encoding(content_bytes)

        # 시도할 인코딩 순서
        encodings_to_try = [
            encoding,
            'utf-8',
            'cp949',
            'euc-kr',
            'utf-8-sig',  # UTF-8 with BOM
            'latin-1'  # 최후의 수단 (절대 실패 안 함)
        ]

        # 중복 제거 (순서 유지)
        seen = set()
        encodings_to_try = [x for x in encodings_to_try if not (x in seen or seen.add(x))]

        for enc in encodings_to_try:
            try:
                decoded = content_bytes.decode(enc)
                logger.info(f"디코딩 성공: {enc}")
                return decoded, enc
            except (UnicodeDecodeError, LookupError, AttributeError) as e:
                logger.debug(f"디코딩 실패 ({enc}): {str(e)}")
                continue

        # 여기까지 오면 안 됨 (latin-1은 항상 성공)
        raise Exception("파일 디코딩 실패")

    @staticmethod
    def encode_preserving_original(text: str, original_encoding: str) -> bytes:
        """
        원본 인코딩을 유지하며 문자열을 바이너리로 인코딩

        Args:
            text: 수정된 텍스트
            original_encoding: 원본 파일의 인코딩

        Returns:
            인코딩된 바이너리 데이터
        """
        if not text:
            logger.warning("빈 텍스트, 빈 바이트 반환")
            return b""

        try:
            encoded = text.encode(original_encoding)
            logger.info(f"인코딩 성공: {original_encoding}")
            return encoded
        except (UnicodeEncodeError, LookupError) as e:
            logger.warning(f"원본 인코딩({original_encoding}) 인코딩 실패: {str(e)}")
            logger.warning("UTF-8로 폴백")
            try:
                return text.encode('utf-8')
            except UnicodeEncodeError:
                # 에러 문자를 무시하고 인코딩
                logger.error("UTF-8 인코딩도 실패, 에러 문자 대체")
                return text.encode('utf-8', errors='replace')

    @staticmethod
    def remove_bom(content_bytes: bytes) -> bytes:
        """
        UTF-8 BOM (Byte Order Mark) 제거

        Args:
            content_bytes: 바이너리 데이터

        Returns:
            BOM이 제거된 바이너리 데이터
        """
        # UTF-8 BOM
        if content_bytes.startswith(b'\xef\xbb\xbf'):
            logger.info("UTF-8 BOM 제거")
            return content_bytes[3:]

        # UTF-16 LE BOM
        if content_bytes.startswith(b'\xff\xfe'):
            logger.info("UTF-16 LE BOM 감지")
            return content_bytes[2:]

        # UTF-16 BE BOM
        if content_bytes.startswith(b'\xfe\xff'):
            logger.info("UTF-16 BE BOM 감지")
            return content_bytes[2:]

        return content_bytes

    @staticmethod
    def safe_decode(content_bytes: bytes, encoding: str) -> str:
        """
        에러를 무시하고 디코딩 (에러 문자를 대체)

        Args:
            content_bytes: 바이너리 데이터
            encoding: 인코딩

        Returns:
            디코딩된 문자열
        """
        try:
            return content_bytes.decode(encoding)
        except UnicodeDecodeError:
            # 디코딩 실패 시 에러 문자 대체
            logger.warning(f"디코딩 에러 발생, 에러 문자 대체: {encoding}")
            return content_bytes.decode(encoding, errors='replace')
        except LookupError:
            # 알 수 없는 인코딩
            logger.error(f"알 수 없는 인코딩: {encoding}, UTF-8 시도")
            return content_bytes.decode('utf-8', errors='replace')
