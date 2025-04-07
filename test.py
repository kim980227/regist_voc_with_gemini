import requests
import os
from dotenv import load_dotenv

# .env 파일에서 환경변수 로드
load_dotenv()
login_id = os.getenv("LOGIN_ID")
login_pwd = os.getenv("LOGIN_PWD")
login_type = os.getenv("LOGIN_TYPE")

session = requests.Session()

# 로그인 요청
login_url = "http://srms.poscomcm.com:8080/P010/member/loginchk"
login_data = {
    "swpid": login_id,         # ID 필드 name
    "password": login_pwd,         # 비밀번호 필드 name
    "loginType": login_type        # 히든 필드 값
}

response = session.post(login_url, data=login_data)

# 로그인 성공 여부 판단
try:
    # 로그인 요청
    response = session.post(login_url, data=login_data)

    # 로그인 성공 여부 확인
    if response.ok and "로그인" not in response.text:
        print("✅ 로그인 성공!")

        # (여기서 로그인 후 필요한 작업을 수행 가능)
        # VOC 페이지 호출
        voc_url = "http://srms.poscomcm.com:8080/P010/voc/voc-request-list"
        response = session.get(voc_url)

        if response.ok:
            print("📄 VOC 화면 불러오기 성공")
        else:
            print("❌ VOC 요청 실패")
            print(response.status_code)

    else:
        print("❌ 로그인 실패")
        print(response.text)

finally:
    # 세션 명시적 종료
    session.close()
    print("🔒 세션 종료 완료")