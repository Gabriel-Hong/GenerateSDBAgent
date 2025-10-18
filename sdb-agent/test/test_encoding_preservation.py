"""
인코딩 유지 기능 테스트
"""

import pytest
from app.encoding_handler import EncodingHandler


class TestEncodingHandler:
    """EncodingHandler 클래스 테스트"""

    def test_detect_utf8(self):
        """UTF-8 인코딩 감지 테스트"""
        content = "Hello World".encode('utf-8')
        handler = EncodingHandler()

        encoding = handler.detect_encoding(content)
        assert encoding == 'utf-8'

    def test_detect_cp949(self):
        """CP949 인코딩 감지 테스트"""
        content = "안녕하세요".encode('cp949')
        handler = EncodingHandler()

        encoding = handler.detect_encoding(content)
        assert encoding == 'cp949'

    def test_detect_euc_kr_to_cp949(self):
        """EUC-KR을 CP949로 변환 테스트"""
        content = "테스트".encode('euc-kr')
        handler = EncodingHandler()

        encoding = handler.detect_encoding(content)
        # EUC-KR은 CP949로 통일
        assert encoding == 'cp949'

    def test_decode_with_fallback_utf8(self):
        """UTF-8 디코딩 테스트"""
        content = "Hello World".encode('utf-8')
        handler = EncodingHandler()

        decoded, encoding = handler.decode_with_fallback(content)
        assert decoded == "Hello World"
        assert encoding == 'utf-8'

    def test_decode_with_fallback_cp949(self):
        """CP949 디코딩 테스트"""
        content = "테스트".encode('cp949')
        handler = EncodingHandler()

        decoded, encoding = handler.decode_with_fallback(content)
        assert decoded == "테스트"
        assert encoding == 'cp949'

    def test_decode_with_hint(self):
        """파일 확장자 힌트 기반 인코딩 감지 테스트"""
        # ASCII 전용 파일 (신뢰도 낮음)
        content = "int main() {}".encode('utf-8')
        handler = EncodingHandler()

        # C++ 파일이면 CP949 추정
        encoding = handler.detect_encoding_with_hint(content, "test.cpp")
        # ASCII는 UTF-8와 CP949 모두 호환되므로 어느 것이든 가능
        assert encoding in ['utf-8', 'cp949']

    def test_encode_preserving_original(self):
        """원본 인코딩 유지 테스트"""
        original_text = "// 주석\nvoid function() {}"
        original_encoding = 'cp949'
        handler = EncodingHandler()

        # CP949로 인코딩
        encoded = handler.encode_preserving_original(original_text, original_encoding)

        # 다시 디코딩하여 확인
        decoded, _ = handler.decode_with_fallback(encoded, original_encoding)
        assert decoded == original_text

    def test_encode_fallback_to_utf8(self):
        """인코딩 실패 시 UTF-8 폴백 테스트"""
        # 이모지는 CP949로 인코딩 불가
        text_with_emoji = "Hello 😀"
        handler = EncodingHandler()

        # CP949로 시도하지만 실패하여 UTF-8로 폴백
        encoded = handler.encode_preserving_original(text_with_emoji, 'cp949')

        # UTF-8로 디코딩되어야 함
        decoded, encoding = handler.decode_with_fallback(encoded)
        assert decoded == text_with_emoji
        assert encoding == 'utf-8'

    def test_remove_bom_utf8(self):
        """UTF-8 BOM 제거 테스트"""
        content_with_bom = b'\xef\xbb\xbfHello'
        handler = EncodingHandler()

        content_without_bom = handler.remove_bom(content_with_bom)
        assert content_without_bom == b'Hello'

    def test_remove_bom_utf16le(self):
        """UTF-16 LE BOM 제거 테스트"""
        content_with_bom = b'\xff\xfeHello'
        handler = EncodingHandler()

        content_without_bom = handler.remove_bom(content_with_bom)
        assert content_without_bom == b'Hello'

    def test_remove_bom_none(self):
        """BOM이 없는 경우 테스트"""
        content = b'Hello'
        handler = EncodingHandler()

        result = handler.remove_bom(content)
        assert result == b'Hello'

    def test_safe_decode_with_errors(self):
        """에러 문자 대체 디코딩 테스트"""
        # 잘못된 UTF-8 바이트
        invalid_utf8 = b'Hello \xff World'
        handler = EncodingHandler()

        # 에러 문자를 대체하여 디코딩
        decoded = handler.safe_decode(invalid_utf8, 'utf-8')
        assert 'Hello' in decoded
        assert 'World' in decoded

    def test_round_trip_preservation(self):
        """왕복 변환 테스트 (원본 유지)"""
        original_text = """
// 한글 주석
void processData() {
    int value = 100;
    // 처리 로직
}
"""
        handler = EncodingHandler()

        # CP949로 인코딩
        encoded = handler.encode_preserving_original(original_text, 'cp949')

        # 다시 디코딩
        decoded, detected_encoding = handler.decode_with_fallback(encoded, 'cp949')

        # 원본과 동일해야 함
        assert decoded == original_text
        assert detected_encoding == 'cp949'

    def test_empty_content(self):
        """빈 내용 처리 테스트"""
        handler = EncodingHandler()

        # 빈 바이트
        encoding = handler.detect_encoding(b'')
        assert encoding == 'utf-8'  # 기본값

        # 빈 문자열 인코딩
        encoded = handler.encode_preserving_original('', 'utf-8')
        assert encoded == b''

        # 빈 바이트 디코딩
        decoded, encoding = handler.decode_with_fallback(b'')
        assert decoded == ''


class TestEncodingIntegration:
    """인코딩 유지 통합 테스트"""

    def test_cpp_file_simulation(self):
        """C++ 파일 시뮬레이션 테스트"""
        # 원본 파일 내용 (CP949)
        original_content = """
// 데이터베이스 처리 클래스
class DBHandler {
public:
    void processData();  // 데이터 처리
};
"""
        handler = EncodingHandler()

        # 1. CP949로 인코딩 (Bitbucket에서 읽어온 상태)
        file_bytes = original_content.encode('cp949')

        # 2. 인코딩 감지
        detected_encoding = handler.detect_encoding(file_bytes)
        assert detected_encoding == 'cp949'

        # 3. 디코딩 (수정 작업용)
        content_text, _ = handler.decode_with_fallback(file_bytes, detected_encoding)

        # 4. 코드 수정 (LLM이 한다고 가정)
        modified_text = content_text.replace(
            'void processData();',
            'void processData();\n    void processNewData();  // 새로운 처리'
        )

        # 5. 원본 인코딩으로 다시 인코딩
        modified_bytes = handler.encode_preserving_original(modified_text, detected_encoding)

        # 6. 검증: 한글이 제대로 인코딩되었는지 확인
        final_text, final_encoding = handler.decode_with_fallback(modified_bytes, detected_encoding)
        assert '데이터베이스' in final_text
        assert '새로운 처리' in final_text
        assert final_encoding == 'cp949'

    def test_mixed_encoding_file(self):
        """혼합 인코딩 파일 처리 테스트"""
        # ASCII + 한글 혼합
        mixed_content = "int value = 100;  // 값 설정"
        handler = EncodingHandler()

        # UTF-8로 인코딩
        utf8_bytes = mixed_content.encode('utf-8')
        decoded_utf8, enc1 = handler.decode_with_fallback(utf8_bytes)
        assert decoded_utf8 == mixed_content

        # CP949로 인코딩
        cp949_bytes = mixed_content.encode('cp949')
        decoded_cp949, enc2 = handler.decode_with_fallback(cp949_bytes)
        assert decoded_cp949 == mixed_content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
