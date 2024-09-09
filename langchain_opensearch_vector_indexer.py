import os
from typing import Optional, List

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from langchain_community.document_loaders import UnstructuredPowerPointLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain_community.chat_models import BedrockChat
from langchain_aws import BedrockEmbeddings
from langchain.docstore.document import Document

from config import config


def get_bedrock_client(profile: str, region: str) -> Optional[boto3.client]:
    """
    AWS Bedrock 클라이언트를 생성합니다.

    :param profile: AWS 프로파일 이름
    :param region: AWS 리전 이름
    :return: Bedrock 클라이언트 객체, 실패 시 None
    """
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        return session.client("bedrock-runtime")
    except Exception as e:
        print(f"Bedrock 클라이언트 생성 중 오류 발생: {e}")
        return None

def create_bedrock_llm(bedrock_client: boto3.client, model_version_id: str) -> BedrockChat:
    """
    Bedrock LLM(대규모 언어 모델) 인스턴스를 생성합니다.

    :param bedrock_client: Bedrock 클라이언트 객체
    :param model_version_id: 사용할 모델의 버전 ID
    :return: BedrockChat 인스턴스
    """
    return BedrockChat(
        model_id=model_version_id, 
        client=bedrock_client,
        model_kwargs={'temperature': 0}
    )

def create_langchain_vector_embedding(bedrock_client: boto3.client, bedrock_embedding_model_id: str) -> BedrockEmbeddings:
    """
    Langchain 벡터 임베딩 인스턴스를 생성합니다.

    :param bedrock_client: Bedrock 클라이언트 객체
    :param bedrock_embedding_model_id: 사용할 임베딩 모델의 ID
    :return: BedrockEmbeddings 인스턴스
    """
    return BedrockEmbeddings(
        client=bedrock_client,
        model_id=bedrock_embedding_model_id
    )

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
        return AWS4Auth(credentials.access_key, credentials.secret_key,
                        region, service, session_token=credentials.token)
    except Exception as e:
        print(f"AWS 인증 정보 획득 중 오류 발생: {e}")
        return None

def create_opensearch_vector_index(
    docs: List[Document], 
    bedrock_embeddings_client: BedrockEmbeddings, 
    opensearch_endpoint: str, 
    index_name: str, 
    auth: AWS4Auth
) -> Optional[OpenSearchVectorSearch]:
    """
    OpenSearch 벡터 인덱스를 생성합니다.

    :param docs: 인덱싱할 문서 리스트
    :param bedrock_embeddings_client: Bedrock 임베딩 클라이언트
    :param opensearch_endpoint: OpenSearch 엔드포인트 URL
    :param index_name: 생성할 인덱스 이름
    :param auth: AWS 인증 객체
    :return: OpenSearchVectorSearch 객체, 실패 시 None
    """
    try:
        return OpenSearchVectorSearch.from_documents(
            documents=docs,
            embedding=bedrock_embeddings_client,
            opensearch_url=opensearch_endpoint,
            http_auth=auth,
            timeout=300,
            connection_class=RequestsHttpConnection,
            index_name=index_name,
        )
    except Exception as e:
        print(f"OpenSearch 벡터 저장소 생성 중 오류 발생: {e}")
        return None

def recursive_split(docs, max_tokens=7500):
    result = []
    for doc in docs:
        if len(doc.page_content) > max_tokens:
            mid = len(doc.page_content) // 2
            left = Document(page_content=doc.page_content[:mid], metadata=doc.metadata)
            right = Document(page_content=doc.page_content[mid:], metadata=doc.metadata)
            result.extend(recursive_split([left, right], max_tokens))
        else:
            result.append(doc)
    return result

def parse_txt_file(file_path, chunk_size=300, chunk_overlap=30):
    try:
        loader = TextLoader(file_path)
        documents = loader.load()

        text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        return recursive_split(chunks)

    except Exception as e:
        print(f"Error parsing TXT file: {e}")
        return []
    
def chunked(iterable, n):
    """Yield successive n-sized chunks from iterable."""
    for i in range(0, len(iterable), n):
        yield iterable[i:i + n]


def main():

    print (f'{config=}')
    
    bedrock_client = get_bedrock_client(config["profile"], config["region"])
    if not bedrock_client:
        return

    bedrock_embeddings_client = create_langchain_vector_embedding(bedrock_client, config["bedrock_embedding_model_id"])
    auth = get_auth(config["profile"], config["region"], "aoss")

    successful_files = []
    failed_files = []

    download_folder_path = os.path.join('.', config["local_download_path"])
    
    for root, dirs, files in os.walk(download_folder_path):
        for file in files:
            if file.endswith('.txt'):
                full_path = os.path.join(root, file)
                print(f"Processing {full_path}")
                try:
                    parsed_docs = parse_txt_file(full_path)
                    if parsed_docs:
                        for i, doc_batch in enumerate(chunked(parsed_docs, 100)):  # 100개씩 배치 처리
                            opensearch_vector_store = create_opensearch_vector_index(
                                doc_batch, bedrock_embeddings_client, config["opensearch_endpoint"], config["index_name"], auth
                            )
                            if not opensearch_vector_store:
                                raise Exception(f"Failed to create vector store for batch {i}")
                        successful_files.append(full_path)
                        print(f"Successfully processed {full_path}")
                        break
                    else:
                        raise Exception("No documents parsed")
                except Exception as e:
                    failed_files.append((full_path, str(e)))
                    print(f"Failed to process {full_path}: {e}")

    print("\nSuccessfully processed files:")
    for file in successful_files:
        print(file)

    print("\nFailed files:")
    for file, error in failed_files:
        print(f"{file}: {error}")

if __name__ == "__main__":
    main()