# src/session_manager.py

import requests
import threading # 여러 스레드에서 세션을 사용할 경우를 대비

class SessionManager:
    """
    requests.Session 객체들을 생성하고 관리하며, 필요 시 모든 세션을 종료하는 클래스.
    싱글톤 패턴으로 구현하여 애플리케이션 전체에서 하나의 Manager 인스턴스만 사용하도록 합니다.
    """
    _instance = None
    _lock = threading.Lock() # 스레드 안전성을 위해 Lock 사용

    def __new__(cls):
        # 싱글톤 패턴 구현
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SessionManager, cls).__new__(cls)
                cls._instance._active_sessions = [] # 활성 세션 리스트
        return cls._instance

    def create_session(self) -> requests.Session:
        """
        새로운 requests.Session 객체를 생성하고 관리 리스트에 추가하여 반환합니다.
        """
        session = requests.Session()
        with self._lock:
            self._active_sessions.append(session)
        print(f"새 requests 세션 생성 및 관리 목록에 추가됨. 현재 활성 세션 수: {len(self._active_sessions)}")
        return session

    def close_session(self, session: requests.Session):
        """
        특정 requests.Session 객체를 종료하고 관리 리스트에서 제거합니다.
        """
        with self._lock:
            if session in self._active_sessions:
                session.close()
                self._active_sessions.remove(session)
                print(f"requests 세션이 닫히고 관리 목록에서 제거됨. 현재 활성 세션 수: {len(self._active_sessions)}")
            else:
                print("경고: 해당 세션은 관리 목록에 없거나 이미 닫혔습니다.")

    def close_all_sessions(self):
        """
        관리 중인 모든 requests.Session 객체들을 종료합니다.
        """
        with self._lock:
            if not self._active_sessions:
                print("현재 관리 중인 requests 세션이 없습니다.")
                return

            print(f"모든 requests 세션 ({len(self._active_sessions)}개)을 닫습니다...")
            for session in list(self._active_sessions): # 반복 중 리스트 변경 방지를 위해 사본 사용
                try:
                    session.close()
                    print(f"세션 {id(session)} 닫힘.")
                except Exception as e:
                    print(f"세션 {id(session)} 닫는 중 오류 발생: {e}")
            self._active_sessions.clear() # 모든 세션 제거
            print("✅ 모든 requests 세션이 닫혔습니다.")

    def get_active_session_count(self) -> int:
        """
        현재 관리 중인 활성 세션의 수를 반환합니다.
        """
        with self._lock:
            return len(self._active_sessions)