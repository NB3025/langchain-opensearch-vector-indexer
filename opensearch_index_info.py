import boto3
from typing import Optional, List

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

from config import config


def get_auth(profile: str, region: str, service: str) -> Optional[AWS4Auth]:
    """
    AWS 인증 객체를 생성합니다.

    :param profile: AWS 프로파일 이름
    :param region: AWS 리전 이름
    :param service: 인증이 필요한 AWS 서비스 이름
    :return: AWS4Auth 객체, 실패 시 None
    """
    try:
        session = boto3.Session(profile_name=profile)
        credentials = session.get_credentials()
        return AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            service,
            session_token=credentials.token
        )
    except Exception as e:
        print(f"AWS 인증 정보 획득 중 오류 발생: {e}")
        return None


def get_opensearch_client(auth: AWS4Auth, host: str) -> OpenSearch:
    """
    OpenSearch 클라이언트를 생성합니다.

    :param auth: AWS4Auth 객체
    :param host: OpenSearch 호스트
    :return: OpenSearch 클라이언트
    """
    return OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )


def print_indices_info(client: OpenSearch):
    """
    모든 인덱스의 정보를 출력합니다.

    :param client: OpenSearch 클라이언트
    """
    indices = client.indices.get('*')
    for index_name, index_info in indices.items():
        print(f"Index: {index_name}")
        print(f"Settings: {index_info['settings']}")
        print(f"Mappings: {index_info['mappings']}")
        print("\n")


def main():
    print(f'{config=}')
    
    auth = get_auth(config["profile"], config["region"], "aoss")
    if not auth:
        print("인증 객체 생성 실패")
        return

    host = config["opensearch_endpoint"].replace("https://", "")
    client = get_opensearch_client(auth, host)
    
    print_indices_info(client)


if __name__ == "__main__":
    main()