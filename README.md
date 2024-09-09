# Langchain OpenSearch 벡터 인덱서

이 프로젝트는 AWS Bedrock과 OpenSearch를 사용하여 문서를 벡터화하고 인덱싱하는 도구입니다. Langchain 라이브러리를 활용하여 텍스트 처리와 벡터 저장소 생성을 수행합니다.

**Amazon OpenSearch Serverless, Amazon Titan Text Embeddings v2(amazon.titan-embed-text-v2:0)를 사용하였습니다.**

## 주요 기능

1. 텍스트 파일 처리 및 청크 분할
2. AWS Bedrock을 사용한 텍스트 임베딩
3. OpenSearch에 벡터 인덱스 생성
4. OpenSearch 인덱스 정보 조회

## 파일 구조

- `langchain_opensearch_vector_indexer.py`: 메인 인덱싱 스크립트
- `opensearch_index_info.py`: OpenSearch 인덱스 정보 조회 스크립트
- `config.py`: 설정 정보 파일

## 설정

`config.py` 파일에 다음과 같은 설정 정보를 입력합니다:

```python
config = {
        "region": "us-east-1",
        "profile": "aws configure profile",
        "bedrock_model_id": "anthropic.claude-3-haiku-20240229-v1:0",
        "bedrock_embedding_model_id":"amazon.titan-embed-text-v2:0",
        "opensearch_endpoint": "https://your.us-east-1.aoss.amazonaws.com",
        "index_name": "your_index",
        "local_download_path" : 'data/',
    }

```

주요 설정 항목:
- `region`: AWS 리전
- `profile`: AWS 프로파일 이름
- `bedrock_model_id`: 사용할 Bedrock 모델 ID
- `bedrock_embedding_model_id`: 텍스트 임베딩에 사용할 Bedrock 모델 ID
- `opensearch_endpoint`: OpenSearch 엔드포인트 URL
- `index_name`: 생성할 OpenSearch 인덱스 이름
- `local_download_path`: 처리할 로컬 파일 경로

## 사용 방법

1. 필요한 라이브러리 설치:
   ```
   pip install boto3 opensearch-py requests-aws4auth langchain
   ```

2. `config.py` 파일의 설정을 필요에 따라 수정합니다.

3. 텍스트 파일 인덱싱 실행:
   ```
   python langchain_opensearch_vector_indexer.py
   ```

4. OpenSearch 인덱스 정보 조회:
   ```
   python opensearch_index_info.py
   ```

## 주의사항

- AWS 자격 증명이 올바르게 설정되어 있어야 합니다.
- OpenSearch 엔드포인트에 대한 적절한 접근 권한이 필요합니다.
- 대용량 파일 처리 시 메모리 사용량에 주의하세요.
- `config.py` 파일에 민감한 정보가 포함되어 있으므로 버전 관리 시스템에 직접 추가하지 않도록 주의하세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
