# main.py
import pandas as pd
import os

from src.valid_voc_data import (
    load_voc_code_mappings,
    validate_voc_data,
    validate_voc_type_only,
    filter_valid_voc_rows
)
from src.config.config import (
    VOC_TYPE_FILE_PATH, VOC_RECV_TYPE_FILE_PATH, VOC_SERVICE_FILE_PATH, VOC_DATA_FILE_PATH
)
from src.insert_voc import set_qry_params 

from src.db.repository import Repository 
from src.ai.gemini_api import infer_voc_type_with_gemini 
from src.auth import AuthService 
from src.session_manager import SessionManager 
from src.insert_voc import send_voc_data_to_api

def main():
    # SessionManager 인스턴스 가져오기 (싱글톤)
    session_manager = SessionManager()
    
    # 이 애플리케이션의 주 세션 생성
    main_session = session_manager.create_session()
    auth_service = AuthService(main_session) # 인증서비스 인스턴스 생성
    AuthService.authenticate(auth_service) # 인증 시도

    # 📋 인사 정보 조회: DatabaseRepository 클래스의 인스턴스를 생성하여 사용
    db_repo = Repository() # 클래스의 인스턴스 생성
    insa_info_map = db_repo.get_insa_info() # 인스턴스의 메서드 호출
    if not insa_info_map:
        print("❌ 인사 정보를 불러오지 못했습니다. 프로그램을 종료합니다.")
        return

    # 📁 파일 경로 설정
    voc_type_file_path = VOC_TYPE_FILE_PATH
    voc_recv_type_file_path = VOC_RECV_TYPE_FILE_PATH
    voc_service_file_path = VOC_SERVICE_FILE_PATH
    voc_data_dir = VOC_DATA_FILE_PATH

    # ✅ 필수 필드 정의
    required_fields = [
        '제기자', '접수유형', '소분류',
        '요청일시/등록일시', '완료일시', '작업시간', 'VOC내용'
    ]

    # 🔄 코드 매핑 로딩
    try:
        voc_type_map, voc_recv_map, voc_service_map = load_voc_code_mappings(
            voc_type_file_path,
            voc_recv_type_file_path,
            voc_service_file_path
        )
    except Exception as e:
        print(f"❌ 코드 매핑 로딩 실패, 프로그램을 종료합니다.: {e}")
        return

    # 📄 VOC CSV 파일 탐색 및 로딩
    try:
        csv_files = [f for f in os.listdir(voc_data_dir) if f.lower().endswith('.csv')]

        if len(csv_files) == 0:
            print(f"❌ '{voc_data_dir}' 디렉토리에 CSV 파일이 없습니다. 프로그램을 종료합니다.")
            exit()
        elif len(csv_files) > 1:
            print(f"❌ '{voc_data_dir}' 디렉토리에 CSV 파일이 2개 이상 존재합니다. 하나만 존재해야 합니다. 프로그램을 종료합니다.")
            exit()

        voc_data_file_path = os.path.join(voc_data_dir, csv_files[0])
        df_voc = pd.read_csv(voc_data_file_path)

    except Exception as e:
        print(f"❌ VOC 데이터 파일 로딩 실패, 프로그램을 종료합니다.: {e}")
        exit()

    # 🔍 데이터 검증
    invalid_indexes = validate_voc_data(df_voc, required_fields, voc_recv_map, voc_service_map, voc_type_map, insa_info_map)

    # ❗ 유효하지 않은 행 출력
    if invalid_indexes:
        print("\n❗ 제외된 유효하지 않은 행들:")
        invalid_rows = df_voc.loc[list(invalid_indexes)].copy()
        invalid_rows.index = invalid_rows.index + 2
        print(invalid_rows)
    else:
        print("\n✅ 모든 VOC 행이 유효합니다.")

    # ✅ 유효한 행만 남기기
    df_voc = filter_valid_voc_rows(df_voc, invalid_indexes)

    # 🔍 VOC유형 추론 (Gemini API 사용, 필요시 주석 해제)
    # df_voc = infer_voc_type_with_gemini(df_voc, voc_type_map)

    # ❗ VOC유형만 검증 (추론 이후 VOC 유형 코드가 유효한지 확인)
    invalid_voc_type_indexes = validate_voc_type_only(df_voc, voc_type_map)
    df_voc = filter_valid_voc_rows(df_voc, invalid_voc_type_indexes)

    # 📊 API 전송을 위한 폼 데이터 추출
    voc_form_data_list = set_qry_params(df_voc, voc_type_map, voc_recv_map, voc_service_map, insa_info_map)
    print(f"\n✅ 입력 준비 완료된 VOC 목록: {len(voc_form_data_list)}건")

    # 웹 로그인 및 VOC 페이지 요청 (AuthService 인스턴스 생성 및 사용)
    successful_session = auth_service.login_and_fetch_voc_page() 
    input("계속하려면 Enter를 누르세요...")
    send_voc_data_to_api(voc_form_data_list, successful_session)

    session_manager.close_all_sessions()


if __name__ == "__main__":
    main()