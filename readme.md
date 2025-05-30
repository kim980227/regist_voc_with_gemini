# VOC 자동 등록 프로그램

이 프로그램은 VOC(고객의 소리) 데이터를 읽고 검증하며, 필요한 경우 Gemini API를 사용하여 VOC 유형을 추론하고, 최종적으로 VOC 시스템에 데이터를 자동 등록하는 Python 애플리케이션입니다.

---

## 🚀 시작하기

### 📋 사전 준비 사항

이 프로그램을 실행하기 전에 다음 사항을 준비해야 합니다.

* **Python 3.x**: 시스템에 Python이 설치되어 있어야 합니다.
* **.env 파일 설정**: 프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 환경 변수들을 설정해야 합니다.

    ```ini
    # 로그인 데이터
    LOGIN_ID=
    LOGIN_PWD=
    LOGIN_TYPE=default

    # 접근 URL
    LOGIN_URL=
    VOC_URL=
    VOC_INSERT_URL=

    # DB 접속 정보
    DB_HOST=
    DB_PORT=
    DB_NAME=
    DB_USER=
    DB_PASSWORD=

    # Google Gemini API 키 (VOC 유형 추론 시 필요)
    GOOGLE_API_KEY=

    # VOC 작업자 정보
    WORKER_EMPCD=
    WORKER_NAME=
    WORKER_DEPTCD=
    WORKER_DEPTNAME=
    WORKER_OFFICE_TEL=
    WORKER_MOBILE_TEL=

    # 코드 매핑 자료 위치
    VOC_TYPE_FILE_PATH=
    VOC_RECV_TYPE_FILE_PATH=
    VOC_SERVICE_FILE_PATH=

    # VOC 등록 자료 위치
    VOC_DATA_FILE_PATH=

    # 코드 매핑 컬럼명
    VOC_TYPE_KEY=
    VOC_TYPE_VALUE=
    VOC_RECV_TYPE_KEY=
    VOC_RECV_TYPE_VALUE=
    VOC_SERVICE_KEY=
    VOC_SERVICE_VALUE=
    ```

### 📦 의존성 설치

프로젝트에 필요한 Python 라이브러리들은 **`requirements.txt`** 파일에 정리되어 있습니다. 다음 명령어를 사용하여 모든 의존성을 한 번에 설치할 수 있습니다.

```bash
pip install -r requirements.txt
```

### ⚙️ 프로그램 동작 방식
main.py는 다음과 같은 단계를 거쳐 VOC 데이터를 처리합니다.

1. 세션 및 인증
SessionManager를 통해 세션을 관리하고 AuthService를 사용하여 VOC 시스템에 로그인 인증을 시도합니다.

2. 인사 정보 로딩
데이터베이스에서 직원 인사 정보를 불러옵니다. 이는 '제기자'와 같은 필드를 검증하는 데 사용됩니다. 현재 동명이인 처리 기능은 구현되어 있지 않습니다.

3. 코드 매핑 로딩
VOC 유형, 접수 유형, 소분류 등에 대한 코드 매핑 파일을 로드합니다.

4. VOC 데이터 로딩
등록할 VOC 데이터가 포함된 CSV 파일을 로드합니다.

5. 데이터 검증
필수 필드 확인: VOC 데이터에 필요한 모든 필드가 존재하는지 확인합니다.

6. 코드 유효성 검사
로드된 코드 매핑을 기반으로 '접수유형', '소분류' 등의 값이 유효한지 검증합니다.

7. 인사 정보 유효성 검사
'제기자' 정보가 인사 정보에 존재하는지 확인합니다. 동명이인 처리 기능은 현재 구현되어 있지 않습니다.
validate_voc_data 함수: 이 함수는 데이터의 전반적인 유효성을 검사하며, 필요에 따라 해당 호출을 주석 처리하여 검증 단계를 건너뛸 수 있습니다. (예: 데이터 유효성이 이미 확보된 경우)

8. 유효한 행 필터링
검증 과정에서 유효하지 않다고 판단된 행들은 최종 등록 목록에서 제외됩니다.

10. VOC 유형 추론 (선택 사항)
infer_voc_type_with_gemini 함수를 사용하여 VOC 내용으로부터 VOC 유형을 자동으로 추론할 수 있습니다. 이 기능은 GOOGLE_API_KEY가 .env 파일에 설정되어 있어야 작동합니다.

12. 추론된 VOC 유형 재검증
Gemini API를 통해 추론된 VOC 유형 코드가 유효한지 다시 한번 검증합니다.

14. API 전송 데이터 준비
유효성 검사를 통과한 VOC 데이터를 VOC 시스템의 API 요구 사항에 맞는 형태로 변환합니다.

16. VOC 데이터 전송
준비된 데이터를 VOC 시스템의 등록 API로 전송합니다.

### 📝 실행 방법
모든 사전 준비 사항을 완료하고 의존성을 설치했는지 확인합니다.

명령 프롬프트 또는 터미널에서 main.py 파일이 있는 디렉토리로 이동합니다.

다음 명령어를 실행하여 프로그램을 시작합니다.

```bash
python main.py
```
프로그램이 실행되면 콘솔에 진행 상황이 출력되며, 필요한 경우 메시지가 표시됩니다.
