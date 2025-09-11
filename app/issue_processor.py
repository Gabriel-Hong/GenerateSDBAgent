"""
이슈 처리 프로세서 - Jira 이슈를 받아서 전체 워크플로우 실행
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class IssueProcessor:
    """Jira 이슈 처리 프로세서"""
    
    def __init__(self, bitbucket_api, llm_handler):
        self.bitbucket_api = bitbucket_api
        self.llm_handler = llm_handler
    
    def process_issue(self, issue: Dict) -> Dict[str, Any]:
        """
        Jira 이슈를 처리하는 메인 워크플로우
        
        Args:
            issue: Jira 이슈 정보
            
        Returns:
            처리 결과
        """
        result = {
            'status': 'started',
            'issue_key': issue.get('key'),
            'branch_name': None,
            'pr_url': None,
            'modified_files': [],
            'errors': []
        }
        
        try:
            # 1. 이슈 내용 요약
            logger.info("Step 1: 이슈 내용 요약 중...")
            issue_summary = self.llm_handler.summarize_issue(issue)
            
            # 2. 브랜치 생성
            branch_name = self._generate_branch_name(issue)
            logger.info(f"Step 2: 브랜치 생성 중: {branch_name}")
            
            try:
                self.bitbucket_api.create_branch(branch_name)
                result['branch_name'] = branch_name
            except Exception as e:
                logger.error(f"브랜치 생성 실패: {str(e)}")
                result['errors'].append(f"브랜치 생성 실패: {str(e)}")
                return result
            
            # 3. 프로젝트 구조 분석
            logger.info("Step 3: 프로젝트 구조 분석 중...")
            project_structure = self.bitbucket_api.analyze_project_structure(branch_name)
            
            # 4. LLM을 통한 수정 필요 파일 분석
            logger.info("Step 4: 수정 필요 파일 분석 중...")
            analysis_result = self.llm_handler.analyze_project_structure(
                project_structure, 
                issue_summary
            )
            
            # 5. 파일 수정 및 커밋
            logger.info("Step 5: 파일 수정 및 커밋 중...")
            modified_files = []
            
            # 5-1. 기존 파일 수정
            for file_path in analysis_result.get('files_to_modify', []):
                try:
                    # 현재 파일 내용 가져오기
                    current_content = self.bitbucket_api.get_file_content(file_path, branch_name)
                    if current_content is None:
                        logger.warning(f"파일을 찾을 수 없음: {file_path}")
                        continue
                    
                    # LLM을 통한 코드 수정
                    modified_content = self.llm_handler.generate_code_modification(
                        file_path,
                        current_content,
                        issue_summary,
                        {'structure': project_structure}
                    )
                    
                    # 파일 커밋
                    commit_message = f"[{issue.get('key')}] {file_path} 수정 - SDB 기능 추가"
                    self.bitbucket_api.commit_file(
                        branch_name,
                        file_path,
                        modified_content,
                        commit_message
                    )
                    
                    modified_files.append({
                        'path': file_path,
                        'action': 'modified'
                    })
                    
                except Exception as e:
                    logger.error(f"파일 수정 실패 ({file_path}): {str(e)}")
                    result['errors'].append(f"파일 수정 실패 ({file_path}): {str(e)}")
            
            # 5-2. 새 파일 생성
            for file_path in analysis_result.get('new_files_needed', []):
                try:
                    # LLM을 통한 새 파일 생성
                    new_content = self.llm_handler.generate_new_file(
                        file_path,
                        issue_summary,
                        {'structure': project_structure, 'related_files': modified_files}
                    )
                    
                    # 파일 커밋
                    commit_message = f"[{issue.get('key')}] {file_path} 생성 - SDB 기능 추가"
                    self.bitbucket_api.commit_file(
                        branch_name,
                        file_path,
                        new_content,
                        commit_message
                    )
                    
                    modified_files.append({
                        'path': file_path,
                        'action': 'created'
                    })
                    
                except Exception as e:
                    logger.error(f"파일 생성 실패 ({file_path}): {str(e)}")
                    result['errors'].append(f"파일 생성 실패 ({file_path}): {str(e)}")
            
            result['modified_files'] = modified_files
            
            # 6. Pull Request 생성
            if modified_files:
                logger.info("Step 6: Pull Request 생성 중...")
                pr_title = f"[{issue.get('key')}] {issue.get('fields', {}).get('summary', 'SDB 기능 추가')}"
                pr_description = self._generate_pr_description(issue, modified_files, analysis_result)
                
                try:
                    pr_data = self.bitbucket_api.create_pull_request(
                        branch_name,
                        'master',
                        pr_title,
                        pr_description
                    )
                    
                    result['pr_url'] = pr_data.get('links', {}).get('html', {}).get('href')
                    result['status'] = 'completed'
                    logger.info(f"PR 생성 완료: {result['pr_url']}")
                    
                except Exception as e:
                    logger.error(f"PR 생성 실패: {str(e)}")
                    result['errors'].append(f"PR 생성 실패: {str(e)}")
                    result['status'] = 'failed'
            else:
                logger.warning("수정된 파일이 없어 PR을 생성하지 않았습니다.")
                result['status'] = 'no_changes'
            
            return result
            
        except Exception as e:
            logger.error(f"이슈 처리 중 예기치 않은 오류: {str(e)}", exc_info=True)
            result['errors'].append(f"예기치 않은 오류: {str(e)}")
            result['status'] = 'failed'
            return result
    
    def _generate_branch_name(self, issue: Dict) -> str:
        """이슈 정보를 바탕으로 브랜치 이름 생성"""
        issue_key = issue.get('key', 'UNKNOWN')
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # 브랜치 이름에서 사용할 수 없는 문자 제거
        safe_key = issue_key.replace(' ', '-').replace('/', '-')
        
        return f"feature/sdb-{safe_key}-{timestamp}"
    
    def _generate_pr_description(self, issue: Dict, modified_files: List[Dict], 
                                analysis_result: Dict) -> str:
        """Pull Request 설명 생성"""
        issue_key = issue.get('key')
        issue_summary = issue.get('fields', {}).get('summary', '')
        issue_description = issue.get('fields', {}).get('description', '')
        
        # 수정된 파일 목록
        file_list = "\n".join([
            f"- {file['path']} ({file['action']})" 
            for file in modified_files
        ])
        
        description = f"""## 개요
Jira 이슈: [{issue_key}]
요약: {issue_summary}

## 변경 사항
{analysis_result.get('modification_strategy', 'SDB 기능 구현')}

### 수정된 파일:
{file_list}

## 상세 설명
{issue_description}

## 테스트 방법
1. 이 브랜치를 체크아웃합니다: `git checkout {self._generate_branch_name(issue)}`
2. 프로젝트를 빌드합니다
3. SDB 기능이 정상적으로 추가되었는지 확인합니다

## 체크리스트
- [ ] 코드가 정상적으로 컴파일됩니다
- [ ] 기존 기능에 영향을 주지 않습니다
- [ ] SDB 기능이 요구사항대로 구현되었습니다

---
이 PR은 자동으로 생성되었습니다.
"""
        
        return description
