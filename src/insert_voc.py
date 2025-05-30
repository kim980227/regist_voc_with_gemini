import pandas as pd
import os
import csv
import datetime 
from src.config.config import (
    VOC_INSERT_URL,
    WORKER_EMPCD, WORKER_NAME, WORKER_DEPTCD, WORKER_DEPTNAME, WORKER_OFFICE_TEL, WORKER_MOBILE_TEL
)
import requests

def set_qry_params(df_voc, voc_type_map: dict, voc_recv_map: dict, voc_service_map: dict, insa_info_map: list) -> list[dict]:
    """
    DataFrame에서 VOC 데이터를 API 전송을 위한 폼 데이터 딕셔너리 리스트로 추출합니다.
    각 딕셔너리의 키는 API의 폼 필드 이름에 맞게 설정해야 합니다.
    """
    form_data_list = []
    # insa_info_map의 각 딕셔너리에서 'hname'을 키로 사용하여 딕셔너리 생성
    # TODO: 동명이인 예외처리
    insa_emp_to_info = {d['hname']: d for d in insa_info_map}
    worker_info = {
        "register_empno": WORKER_EMPCD.strip(),  
        "register_empnm": WORKER_NAME.strip(),
        "register_deptcd": WORKER_DEPTCD.strip(),
        "register_deptnm": WORKER_DEPTNAME.strip(),
        "register_office_phone": WORKER_OFFICE_TEL,
        "register_mobile_phone": WORKER_MOBILE_TEL,
        "work_empno": WORKER_EMPCD.strip(),  # 작업자 정보는 등록자와 동일하게 설정
        "work_empnm": WORKER_NAME.strip(),
        "work_deptcd": WORKER_DEPTCD.strip(),
        "work_deptnm": WORKER_DEPTNAME.strip(),
        "work_office_phone": WORKER_OFFICE_TEL,
        "work_mobile_phone": WORKER_MOBILE_TEL,
    }

    for _, row in df_voc.iterrows():
        # 데이터프레임에서 원본 값 추출
        voc_type_name = str(row.get('VOC유형', '')).strip()
        recv_type_name = str(row.get('접수유형', '')).strip()
        service_type_name = str(row.get('소분류', '')).strip()
        requester_name = str(row.get('제기자', '')).strip()

        # 매핑을 통해 코드값 추출
        voc_type_code = voc_type_map.get(voc_type_name, '')
        recv_type_code = voc_recv_map.get(recv_type_name, '')
        service_type_code = voc_service_map.get(service_type_name, '')

        # 인사 정보 매핑
        req_info = insa_emp_to_info.get(requester_name, {})

        # --- 날짜/시간 필드 처리 ---
        # 1. '요청일시/등록일시'
        request_datetime_str = ''
        raw_request_date = row.get('요청일시/등록일시')
        if pd.notna(raw_request_date) and str(raw_request_date).strip() != '':
            try:
                dt_obj = pd.to_datetime(str(raw_request_date).strip())
                request_datetime_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"경고: '요청일시/등록일시' 필드 '{raw_request_date}' 형식 오류. 빈 문자열로 처리합니다.")
                request_datetime_str = ''

        # 2. '완료일시'
        completion_datetime_str = ''
        raw_completion_date = row.get('완료일시')
        if pd.notna(raw_completion_date) and str(raw_completion_date).strip() != '':
            try:
                dt_obj = pd.to_datetime(str(raw_completion_date).strip())
                completion_datetime_str = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"경고: '완료일시' 필드 '{raw_completion_date}' 형식 오류. 빈 문자열로 처리합니다.")
                completion_datetime_str = ''

        # 현재 시간 가져오기
        current_time_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # API가 기대하는 폼 필드 이름에 맞춰 딕셔너리 키 설정
        form_data = {
            "voc_no" : "",
            "voc_date": "",
            "voc_seq": "",
            "service_cd": service_type_code,
            "receive_cd": recv_type_code,
            "voc_cd": voc_type_code,
            "request_empno": req_info.get('empcd', ''),
            "request_empnm": requester_name,
            "request_deptcd": req_info.get('deptcd', ''),
            "request_deptnm": req_info.get('deptcd_disp', ''),
            "request_office_phone": req_info.get('office_phone', ''),
            "request_mobile_phone": req_info.get('handpon', ''),
            # VOC 등록자 정보 (현재 알 수 없으므로 빈 값으로 처리)
            "register_empno": worker_info.get('register_empno', ''),
            "register_empnm": worker_info.get('register_empnm', ''),
            "register_deptcd": worker_info.get('register_deptcd', ''),
            "register_deptnm": worker_info.get('register_deptnm', ''),
            "register_office_phone": worker_info.get('register_office_phone', ''),
            "register_mobile_phone": worker_info.get('register_mobile_phone', ''),
            # 작업자 정보 (현재 알 수 없으므로 빈 값으로 처리)
            "work_empno": worker_info.get('work_empno', ''),
            "work_empnm": worker_info.get('work_empnm', ''),
            "work_deptcd": worker_info.get('work_deptcd', ''),
            "work_deptnm": worker_info.get('work_deptnm', ''),
            "work_office_phone": worker_info.get('work_office_phone', ''),
            "work_mobile_phone": worker_info.get('work_mobile_phone', ''),
            "work_yn": str(row.get('조치가능여부', 'Y')).strip(),
            "work_status": str(row.get('조치여부', 'Y')).strip(),
            "work_minute": str(row.get('작업시간', '0')).strip(),
            "fail_minute": "0",
            "insert_date": request_datetime_str,
            "request_date": request_datetime_str,
            "finish_date": completion_datetime_str,
            "update_date": current_time_str,
            "voc_contents": f"<p>{str(row.get('VOC내용', '')).strip()}</p>",
            "work_contents": f"<p>{str(row.get('조치계획 및 진행상황', '')).strip()}</p>",
        }
        form_data_list.append(form_data)

    return form_data_list

def send_voc_data_to_api(voc_form_data_list: list[dict], active_session):
    """
    VOC 폼 데이터 리스트를 주어진 URL로 POST 요청을 통해 API에 전송합니다.

    Args:
        voc_form_data_list (list[dict]): API에 전송할 VOC 폼 데이터 딕셔너리 리스트.
        voc_insert_url (str): VOC 데이터를 전송할 API 엔드포인트 URL.
        active_session (requests.Session): 로그인 상태를 유지하는 requests 세션 객체.
    """
    print("\n🚀 VOC 데이터를 API로 전송합니다...")
    voc_insert_url = VOC_INSERT_URL.strip()  # URL 공백 제거
    if not voc_form_data_list:
        print("❗ 전송할 VOC 데이터가 없습니다.")
        return

    for i, voc_data in enumerate(voc_form_data_list):
        print(f"--- 전송 중: 레코드 {i+1}/{len(voc_form_data_list)} ---")
        # 디버깅을 위해 전송할 데이터 출력
        # print(f"전송 데이터: {voc_data}") 
        try:
            # 전달받은 active_session을 사용하여 POST 요청
            response = active_session.post(voc_insert_url, data=voc_data) 
            
            if response.ok:
                print(f"✅ 레코드 {i+1} 전송 성공! 응답: {response.status_code}")
            else:
                print(f"❌ 레코드 {i+1} 전송 실패! 상태 코드: {response.status_code}")
                print(f"응답 내용: {response.text}") # 서버에서 받은 에러 페이지 내용 출력
        except requests.exceptions.RequestException as e:
            print(f"❌ 레코드 {i+1} 전송 중 연결/요청 오류 발생: {e}")
            # 오류 발생 시 나머지 데이터 전송 중단 여부는 정책에 따라 결정
            # 현재는 계속 시도하도록 되어 있음. 중단하려면 여기서 break 또는 return

    print("\n🎉 모든 VOC 데이터 전송 시도 완료.")