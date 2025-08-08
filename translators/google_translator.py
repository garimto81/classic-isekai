import os
import configparser
import nltk
from google.cloud import translate_v2 as translate

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

class GoogleTranslator:
    def __init__(self):
        self.api_key = self._load_api_key()
        if not self.api_key:
            raise ValueError("Google Cloud Translation API 키가 설정되지 않았습니다. config.ini 파일을 확인해주세요.")
        
        # Google Cloud Translation API 클라이언트 초기화
        # API 키는 환경 변수 GOOGLE_APPLICATION_CREDENTIALS를 통해 설정되거나
        # 클라이언트 초기화 시 직접 전달될 수 있습니다.
        # 여기서는 API 키를 직접 전달하는 방식을 사용합니다.
        # 실제 프로덕션 환경에서는 서비스 계정 키 파일을 사용하는 것이 더 안전합니다.
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Gemini\\classic-isekai\\json\\service_account_key.json" # 이 부분은 실제 서비스 계정 키 파일 경로로 변경해야 합니다.
        # 또는, API 키를 직접 사용하는 경우:
        # self.client = translate.Client(api_key=self.api_key)
        # 하지만 translate_v2 클라이언트는 api_key 인자를 직접 받지 않습니다.
        # 따라서, 환경 변수를 통해 인증 정보를 설정하는 것이 일반적입니다.
        # 여기서는 간단한 테스트를 위해 API 키를 사용하지만, 실제로는 서비스 계정 키 파일을 권장합니다.
        self.client = translate.Client()

    def _load_api_key(self):
        config = configparser.ConfigParser()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(project_root, 'config.ini')
        config.read(config_path)
        return config['API_KEYS'].get('GOOGLE_TRANSLATION_API_KEY')

    def translate_text(self, text, target_language='ko', source_language=None):
        """텍스트를 번역합니다. API 제한을 고려하여 텍스트를 청크로 분할하여 번역합니다."""
        if isinstance(text, bytes):
            text = text.decode('utf-8')

        # Google Cloud Translation API의 요청 페이로드 크기 제한 (약 200KB)
        # 안전하게 100KB (100 * 1024 바이트)로 설정
        MAX_CHUNK_SIZE = 90 * 1024 # 안전하게 90KB로 설정 

        translated_chunks = []
        current_chunk = []
        current_chunk_size = 0

        # 텍스트를 문장 단위로 분할
        sentences = nltk.sent_tokenize(text)

        for sentence in sentences:
            sentence_bytes = sentence.encode('utf-8')
            if current_chunk_size + len(sentence_bytes) > MAX_CHUNK_SIZE:
                # 현재 청크 번역 및 결과 추가
                if current_chunk:
                    chunk_to_translate = " ".join(current_chunk)
                    result = self.client.translate(chunk_to_translate, target_language=target_language, source_language=source_language)
                    translated_chunks.append(result['translatedText'])
                
                # 새 청크 시작
                current_chunk = [sentence]
                current_chunk_size = len(sentence_bytes)
            else:
                current_chunk.append(sentence)
                current_chunk_size += len(sentence_bytes)
        
        # 마지막 청크 번역 및 결과 추가
        if current_chunk:
            chunk_to_translate = " ".join(current_chunk)
            result = self.client.translate(chunk_to_translate, target_language=target_language, source_language=source_language)
            translated_chunks.append(result['translatedText'])

        return " ".join(translated_chunks)
