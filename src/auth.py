# src/auth/auth.py
import requests
from src.db.repository import Repository 
from src.config.config import (
    login_url, login_data, voc_url
)

class AuthService:
    """
    웹 사이트 로그인 및 VOC 페이지 접근 관련 서비스를 제공하는 클래스입니다.
    """
    def __init__(self, session: requests.Session):
        """
        AuthService 인스턴스를 초기화합니다.

        Args:
            session (requests.Session): 로그인에 사용할 requests 세션 객체입니다.
            login_url (str): 로그인 요청을 보낼 URL입니다.
            login_data (dict): 로그인에 필요한 사용자 이름, 비밀번호 등의 데이터입니다.
            voc_url (str): VOC 페이지의 URL입니다.
        """
        self.session = session
        self.login_url = login_url
        self.login_data = login_data
        self.voc_url = voc_url

    def authenticate(self) -> bool:
        """
        제공된 login_id가 시스템의 승인된(SM, ADMIN) 사용자 목록에 있는지 확인합니다.
        
        Args:
            login_id (str): 인증을 시도하는 사용자의 로그인 ID (empcd에 해당).

        Returns:
            bool: login_id가 승인된 사용자 목록에 있으면 True, 그렇지 않으면 False.
        """
        db_repo = Repository() # Repository 클래스의 인스턴스 생성
        auth_info_list = db_repo.get_auth_info() # 시스템 담당자 정보 조회

        if not auth_info_list:
            print("❗ 경고: 데이터베이스에서 인증 정보를 가져오지 못했습니다. 인증 실패로 처리합니다.")
            return False

        # 조회된 인증 정보 리스트를 순회하며 login_id와 일치하는 member_id가 있는지 확인
        # auth_info_list의 각 딕셔너리는 {'member_id': '...', 'empcd': '...', ...} 형태일 것임
        for auth_record in auth_info_list:
            # get_auth_info SQL 쿼리 결과를 보면 member_id 컬럼을 조회하고 있으므로,
            # auth_record.get('member_id')를 사용하여 비교합니다.
            if auth_record.get('member_id') == self.login_data['swpid']:
                print(f"✅ 인증 성공: {self.login_data['swpid']} (권한: {auth_record.get('auth', 'N/A')})")
                return True
        
        print(f"❌ 인증 실패: {self.login_data['swpid']}는 승인된 사용자 목록에 없습니다.")
        return False

    def login_and_fetch_voc_page(self) -> requests.Session | None: # 반환 타입 힌트 변경
        """
        웹 사이트에 로그인하고 VOC 페이지를 가져옵니다.
        요청 실패 시 None을 반환하며, 성공 시 VOC 페이지를 불러온 세션을 반환합니다.
        (세션은 이 함수 내에서 닫지 않고 외부에서 관리하도록 변경)

        Returns:
            requests.Session | None: VOC 페이지를 성공적으로 불러온 requests.Session 객체 또는 실패 시 None.
        """
        try:
            # 로그인 요청
            print(f"로그인 URL: {self.login_url}")
            # print(f"로그인 데이터: {self.login_data['id']}") # 비밀번호 노출 주의
            response = self.session.post(self.login_url, data=self.login_data)

            # 로그인 성공 여부 확인
            if response.ok and "로그인" not in response.text: # '로그인' 문자열이 응답에 없으면 성공으로 간주
                print("✅ 로그인 성공!")
                # VOC 페이지 요청
                print(f"VOC 페이지 요청 URL: {self.voc_url}")
                response = self.session.get(self.voc_url)
                if response.ok:
                    print("📄 VOC 화면 불러오기 성공")
                    # VOC 화면을 불러온 세션을 반환
                    return self.session
                else:
                    print(f"❌ VOC 요청 실패: 상태 코드 {response.status_code}")
                    print(f"응답 내용 일부: {response.text[:200]}...")
                    return None # 실패 시 None 반환

            else:
                print("❌ 로그인 실패")
                print(f"응답 상태: {response.status_code}, 응답 내용 일부: {response.text[:200]}...")
                return None # 실패 시 None 반환

        except requests.exceptions.ConnectionError as e:
            print(f"❌ 연결 오류 발생: {e}")
            return None
        except requests.exceptions.Timeout:
            print("❌ 요청 시간 초과 오류 발생")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 요청 중 알 수 없는 오류 발생: {e}")
            return None
        finally:
            # 이곳에서는 세션을 닫지 않습니다.
            # 세션 관리는 이 함수를 호출하는 외부(main.py)에서 책임집니다.
            print("🔒 로그인 및 VOC 페이지 요청 절차 완료 (세션은 닫지 않음).")
        