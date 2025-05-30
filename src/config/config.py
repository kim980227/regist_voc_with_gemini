# config.py
import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai
import time

# .env 파일에서 환경변수 로드
load_dotenv()

# 환경 변수 로드
login_id = os.getenv("LOGIN_ID")
login_pwd = os.getenv("LOGIN_PWD")
login_type = os.getenv("LOGIN_TYPE")
login_url = os.getenv("LOGIN_URL")
voc_url = os.getenv("VOC_URL")
VOC_INSERT_URL = os.getenv("VOC_INSERT_URL")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

#VOC 작업자 정보
WORKER_EMPCD = os.getenv("WORKER_EMPCD") 
WORKER_NAME = os.getenv("WORKER_NAME")
WORKER_DEPTCD= os.getenv("WORKER_DEPTCD")
WORKER_DEPTNAME= os.getenv("WORKER_DEPTNAME")
WORKER_OFFICE_TEL= os.getenv("WORKER_OFFICE_TEL")
WORKER_MOBILE_TEL= os.getenv("WORKER_MOBILE_TEL")

#VOC 매핑 자료 위치
VOC_TYPE_FILE_PATH =os.getenv("VOC_TYPE_FILE_PATH")
VOC_RECV_TYPE_FILE_PATH = os.getenv("VOC_RECV_TYPE_FILE_PATH")
VOC_SERVICE_FILE_PATH = os.getenv("VOC_SERVICE_FILE_PATH")
# VOC 등록자료 위치
VOC_DATA_FILE_PATH = os.getenv("VOC_DATA_FILE_PATH")

#VOC 매핑 컬럼명
VOC_TYPE_KEY = os.getenv("VOC_TYPE_KEY")
VOC_RECV_TYPE_KEY = os.getenv("VOC_RECV_TYPE_KEY")
VOC_SERVICE_KEY = os.getenv("VOC_SERVICE_KEY")
VOC_TYPE_VALUE = os.getenv("VOC_TYPE_VALUE")
VOC_RECV_VALUE = os.getenv("VOC_RECV_TYPE_VALUE")
VOC_SERVICE_VALUE = os.getenv("VOC_SERVICE_VALUE")
# 환경변수 로드 끝

#SQL 파일 경로 설정
GET_INSA_INFO_SQL_PATH = "src/db/sql/insa.sql"
GET_AUTH_INFO_SQL_PATH = "src/db/sql/auth.sql"

# 로그인 데이터
login_data = {
    "swpid": login_id,
    "password": login_pwd,
    "loginType": login_type
}

# Google Generative AI 설정
try:
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
    else:
        print("경고: GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다. Gemini 기능이 제한될 수 있습니다.")
except Exception as e:
    print(f"오류: Gemini API 설정 중 문제가 발생했습니다: {e}")

GEMINI_MODEL = genai.GenerativeModel('gemini-1.5-flash')

# ✅ 프리티어 제한 모드 여부 설정
USE_FREE_TIER = True

# 제한 설정
MAX_RPM = 15
MAX_RPD = 1500
MAX_TPM = 1_000_000


# Requests 세션 초기화
session = requests.Session()