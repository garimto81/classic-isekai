from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """모든 라이브러리 커넥터의 기반이 되는 추상 클래스"""
    
    def __init__(self, library_name):
        self.library_name = library_name

    @abstractmethod
    def search(self, query, max_results=10):
        """라이브러리에서 작품을 검색하고 표준화된 형식으로 반환합니다."""
        pass

    def get_details(self, work_id):
        """특정 작품의 상세 정보를 가져옵니다."""
        raise NotImplementedError
