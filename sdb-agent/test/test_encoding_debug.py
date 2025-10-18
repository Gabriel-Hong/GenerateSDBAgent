#!/usr/bin/env python3
"""
인코딩 문제 디버깅 스크립트
각 단계에서 인코딩이 어떻게 변경되는지 추적
"""

import os
import sys
import chardet
from dotenv import load_dotenv

# 프로젝트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.bitbucket_api import BitbucketAPI
from app.encoding_handler import EncodingHandler

load_dotenv()

def analyze_file_encoding(file_path: str, branch: str = "master"):
    """
    파일의 인코딩을 단계별로 분석
    """
    print("="*80)
    print(f"파일 인코딩 분석: {file_path}")
    print("="*80)

    # Bitbucket API 초기화
    api = BitbucketAPI(
        url=os.getenv('BITBUCKET_URL', 'https://api.bitbucket.org'),
        username=os.getenv('BITBUCKET_USERNAME'),
        access_token=os.getenv('BITBUCKET_ACCESS_TOKEN'),
        workspace=os.getenv('BITBUCKET_WORKSPACE', 'mit_dev'),
        repository=os.getenv('BITBUCKET_REPOSITORY', 'genw_new')
    )

    handler = EncodingHandler()

    # Step 1: 바이너리로 파일 읽기
    print("\n[Step 1] 바이너리로 파일 읽기...")
    content_bytes = api.get_file_content_raw(file_path, branch)

    if content_bytes is None:
        print("❌ 파일을 찾을 수 없습니다.")
        return

    print(f"✅ 읽기 완료: {len(content_bytes)} bytes")
    print(f"   첫 100 바이트 (hex): {content_bytes[:100].hex()}")
    print(f"   첫 100 바이트 (repr): {repr(content_bytes[:100])}")

    # Step 2: 인코딩 감지
    print("\n[Step 2] 인코딩 감지...")
    detected_encoding = handler.detect_encoding(content_bytes)
    print(f"✅ 감지된 인코딩: {detected_encoding}")

    # chardet로 직접 확인
    chardet_result = chardet.detect(content_bytes)
    print(f"   chardet 원본 결과: {chardet_result}")

    # Step 3: 디코딩
    print("\n[Step 3] 디코딩...")
    try:
        content_text, used_encoding = handler.decode_with_fallback(content_bytes, detected_encoding)
        print(f"✅ 디코딩 성공: {used_encoding}")
        print(f"   텍스트 길이: {len(content_text)} characters")
        print(f"   첫 200자:\n{content_text[:200]}")
    except Exception as e:
        print(f"❌ 디코딩 실패: {e}")
        return

    # Step 4: 재인코딩 (수정 없이)
    print("\n[Step 4] 재인코딩 (원본 인코딩으로)...")
    try:
        reencoded_bytes = handler.encode_preserving_original(content_text, used_encoding)
        print(f"✅ 재인코딩 완료: {len(reencoded_bytes)} bytes")
        print(f"   첫 100 바이트 (hex): {reencoded_bytes[:100].hex()}")
    except Exception as e:
        print(f"❌ 재인코딩 실패: {e}")
        return

    # Step 5: 비교
    print("\n[Step 5] 원본 vs 재인코딩 비교...")
    if content_bytes == reencoded_bytes:
        print("✅ 완벽히 일치! 인코딩 유지 성공")
    else:
        print("❌ 불일치 발견!")
        print(f"   원본 크기: {len(content_bytes)} bytes")
        print(f"   재인코딩 크기: {len(reencoded_bytes)} bytes")

        # 첫 번째 차이점 찾기
        for i, (b1, b2) in enumerate(zip(content_bytes, reencoded_bytes)):
            if b1 != b2:
                print(f"   첫 차이 위치: byte {i}")
                print(f"   원본: {content_bytes[max(0,i-10):i+10].hex()}")
                print(f"   재인코딩: {reencoded_bytes[max(0,i-10):i+10].hex()}")
                break

    # Step 6: 줄바꿈 문자 확인
    print("\n[Step 6] 줄바꿈 문자 분석...")
    lf_count = content_bytes.count(b'\n')
    crlf_count = content_bytes.count(b'\r\n')
    cr_count = content_bytes.count(b'\r') - crlf_count

    print(f"   LF (\\n) 개수: {lf_count}")
    print(f"   CRLF (\\r\\n) 개수: {crlf_count}")
    print(f"   CR (\\r) 개수: {cr_count}")

    if crlf_count > 0:
        print("   ⚠️ CRLF (Windows 스타일) 줄바꿈 감지")
    elif lf_count > 0:
        print("   ✅ LF (Unix 스타일) 줄바꿈")

    # 재인코딩된 줄바꿈 확인
    lf_count_re = reencoded_bytes.count(b'\n')
    crlf_count_re = reencoded_bytes.count(b'\r\n')
    cr_count_re = reencoded_bytes.count(b'\r') - crlf_count_re

    print(f"\n   재인코딩 후:")
    print(f"   LF (\\n) 개수: {lf_count_re}")
    print(f"   CRLF (\\r\\n) 개수: {crlf_count_re}")
    print(f"   CR (\\r) 개수: {cr_count_re}")

    if (lf_count, crlf_count, cr_count) != (lf_count_re, crlf_count_re, cr_count_re):
        print("   ❌ 줄바꿈 문자가 변경됨!")

    # Step 7: BOM 확인
    print("\n[Step 7] BOM (Byte Order Mark) 확인...")
    if content_bytes.startswith(b'\xef\xbb\xbf'):
        print("   ⚠️ UTF-8 BOM 발견")
    elif content_bytes.startswith(b'\xff\xfe'):
        print("   ⚠️ UTF-16 LE BOM 발견")
    elif content_bytes.startswith(b'\xfe\xff'):
        print("   ⚠️ UTF-16 BE BOM 발견")
    else:
        print("   ✅ BOM 없음")

    print("\n" + "="*80)
    print("분석 완료")
    print("="*80)

    return {
        'original_bytes': content_bytes,
        'reencoded_bytes': reencoded_bytes,
        'encoding': used_encoding,
        'match': content_bytes == reencoded_bytes
    }


def test_llm_handler_diff_application():
    """
    LLM Handler의 apply_diff_to_content가 인코딩을 변경하는지 확인
    """
    print("\n" + "="*80)
    print("LLM Handler Diff 적용 테스트")
    print("="*80)

    from app.llm_handler import LLMHandler

    # 테스트 케이스: CP949 인코딩 텍스트
    original_text = """// 한글 주석
void function() {
    int value = 100;
}"""

    # Diff 생성 (라인 추가)
    diffs = [
        {
            "line_start": 3,
            "line_end": 3,
            "action": "insert",
            "old_content": "",
            "new_content": "    int new_value = 200;",
            "description": "새 변수 추가"
        }
    ]

    llm_handler = LLMHandler()

    print("\n[테스트] apply_diff_to_content 실행...")
    modified_text = llm_handler.apply_diff_to_content(original_text, diffs)

    print(f"\n원본:\n{original_text}")
    print(f"\n수정:\n{modified_text}")

    # 인코딩 테스트
    print("\n[인코딩 테스트]")
    encoding = 'cp949'

    try:
        original_bytes = original_text.encode(encoding)
        modified_bytes = modified_text.encode(encoding)

        print(f"✅ 원본 인코딩 성공: {len(original_bytes)} bytes")
        print(f"✅ 수정 인코딩 성공: {len(modified_bytes)} bytes")

        # 줄바꿈 확인
        original_lines = original_text.splitlines(keepends=True)
        modified_lines = modified_text.splitlines(keepends=True)

        print(f"\n원본 줄바꿈 문자: {[repr(line[-1]) if line else '' for line in original_lines]}")
        print(f"수정 줄바꿈 문자: {[repr(line[-1]) if line else '' for line in modified_lines]}")

    except Exception as e:
        print(f"❌ 인코딩 실패: {e}")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='인코딩 문제 디버깅')
    parser.add_argument('--file', default='src/wg/db/MatlDB.cpp', help='분석할 파일 경로')
    parser.add_argument('--branch', default='master', help='브랜치')

    args = parser.parse_args()

    # 1. 파일 인코딩 분석
    result = analyze_file_encoding(args.file, args.branch)

    # 2. LLM Handler 테스트
    test_llm_handler_diff_application()

    # 3. 최종 결과
    if result and result['match']:
        print("\n✅ 인코딩 왕복 변환 성공!")
        print("   → 원본 인코딩이 유지됩니다.")
    else:
        print("\n❌ 인코딩 왕복 변환 실패!")
        print("   → 이것이 전체 파일 변경의 원인일 수 있습니다.")


if __name__ == "__main__":
    main()
