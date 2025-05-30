# utils.py
import pandas as pd
import os # 파일 경로 등을 다룰 때 필요할 수 있으므로 유지
from src.config.config import (
    VOC_TYPE_KEY, VOC_RECV_TYPE_KEY, VOC_SERVICE_KEY, VOC_TYPE_VALUE, VOC_RECV_VALUE, VOC_SERVICE_VALUE
    )

# 유효성 검증을 위한 VOC 코드 매핑 : CSV 파일을 로딩하여 '이름 → 코드' 딕셔너리로 반환
def load_voc_code_mappings(voc_type_path, voc_recv_path, voc_service_path):
    """
    VOC 코드 매핑 CSV 파일들을 로드하여 딕셔너리 형태로 반환합니다.
    """
    print("🔄 VOC 코드 매핑 시작")
    try:
        voc_type_mapping = pd.read_csv(voc_type_path).set_index(VOC_TYPE_KEY)[VOC_TYPE_VALUE].to_dict()
        voc_recv_mapping = pd.read_csv(voc_recv_path).set_index(VOC_RECV_TYPE_KEY)[VOC_RECV_VALUE].to_dict()
        voc_service_mapping = pd.read_csv(voc_service_path).set_index(VOC_SERVICE_KEY)[VOC_SERVICE_VALUE].to_dict()
        print("✅ VOC 코드 매핑 완료")
        return voc_type_mapping, voc_recv_mapping, voc_service_mapping

    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e.filename}")
        raise
    except KeyError as e:
        print(f"❌ 컬럼 누락 오류: {e} - CSV 파일의 컬럼 이름을 확인하세요.")
        raise
    except pd.errors.EmptyDataError as e:
        print(f"❌ CSV 파일이 비어 있습니다: {e.filename}")
        raise
    except Exception as e:
        print(f"❌ 매핑 로딩 중 예상치 못한 오류 발생: {e}")
        raise

def validate_voc_data(df, required_fields, recv_type_map, service_map, voc_type_map, insa_info_map):
    """VOC 데이터에 대한 필수항목 및 코드 매핑 유효성 검증 (단일 루프 + 유효하지 않은 인덱스 반환)"""
    print("📋 VOC 데이터 유효성 검증 시작")

    null_errors = []
    code_errors = []
    insa_name_errors = []  # 인사 정보 불일치 에러 저장
    invalid_indexes = set()

    # insa_info_map에서 유효한 hname(한글 이름)들을 set으로 미리 준비
    valid_insa_hnames = {info['hname'] for info in insa_info_map if 'hname' in info}
    print(f"로드된 유효한 인사 이름 (일부): {list(valid_insa_hnames)[:5]}{'...' if len(valid_insa_hnames) > 5 else ''}")

    for idx, row in df.iterrows():
        excel_row = idx + 2  # Excel 기준 행 번호
        row_errors = []

        # 1. 필수값 누락 체크
        missing_fields = [col for col in required_fields if pd.isna(row.get(col, '')) or (isinstance(row.get(col, ''), str) and not row.get(col, '').strip())]
        if missing_fields:
            row_errors.append(f"누락된 필드 -> {', '.join(missing_fields)}")

        # 2. 코드 유효성 검사
        recv_type = row.get('접수유형')
        service_type = row.get('소분류')
        voc_type = row.get('VOC유형')
        제기자 = row.get('제기자')

        if pd.notna(recv_type) and recv_type not in recv_type_map:
            row_errors.append(f"접수유형 '{recv_type}'이(가) 유효하지 않음")

        if pd.notna(service_type) and service_type not in service_map:
            row_errors.append(f"소분류 '{service_type}'이(가) 유효하지 않음")

        # voc_type은 NaN인 경우 OK, 값이 있는데 voc_type_map에 없으면 오류
        if pd.notna(voc_type) and voc_type not in voc_type_map:
            row_errors.append(f"VOC유형 '{voc_type}'이(가) 유효하지 않음")

        # 3. 제기자 인사 정보 일치 여부 검사
        if pd.notna(제기자) and 제기자 not in valid_insa_hnames:
            row_errors.append(f"제기자 '{제기자}'이(가) 인사 정보에 없음")

        # 에러 저장
        if row_errors:
            invalid_indexes.add(idx)
            if any('누락된' in e for e in row_errors):
                null_errors.append((excel_row, [e for e in row_errors if '누락된' in e]))
            if any("유효하지 않음" in e for e in row_errors):
                code_errors.append((excel_row, [e for e in row_errors if '유효하지 않음' in e]))
            if any("인사 정보에 없음" in e for e in row_errors):
                insa_name_errors.append((excel_row, [e for e in row_errors if '인사 정보에 없음' in e]))

    # 결과 출력
    if null_errors:
        print("\n❗ 필수 항목 누락:")
        for row_num, issues in null_errors:
            print(f" - Excel 행 {row_num}: {'; '.join(issues)}")
    else:
        print("\n✅ 모든 행에 필수 항목이 입력되었습니다.")

    if code_errors:
        print("\n❗ 코드 매핑 유효성 오류:")
        for row_num, issues in code_errors:
            print(f" - Excel 행 {row_num}: {'; '.join(issues)}")
    else:
        print("\n✅ 접수유형, 소분류 및 VOC유형 코드 모두 유효합니다.")

    if insa_name_errors:
        print("\n❗ 제기자 인사 정보 불일치 오류:")
        # `insa_ofname_errors`는 정의되지 않았으므로 `insa_name_errors`를 사용
        for row_num, issues in insa_name_errors:
            print(f" - Excel 행 {row_num}: {'; '.join(issues)}")
    else:
        print("\n✅ 모든 제기자가 인사 정보에 존재합니다.")

    print("\n📋 VOC 데이터 유효성 검증 완료")
    
    return invalid_indexes

def validate_voc_type_only(df, voc_type_map):
    """
    VOC유형 컬럼만 대상으로 null 또는 유효하지 않은 값을 검사.
    - null: 입력되지 않음
    - 유효하지 않음: voc_type_map에 정의되지 않은 값

    Returns:
        invalid_indexes: 유효하지 않은 VOC유형을 가진 행의 DataFrame 인덱스 집합
    """
    print("\n📋 VOC유형 컬럼 유효성 검증 시작")
    null_errors = []
    invalid_errors = []
    invalid_indexes = set()

    valid_types = set(voc_type_map.keys())

    for idx, row in df.iterrows():
        excel_row = idx + 2  # Excel 기준 행 번호
        voc_type = row.get('VOC유형')

        if pd.isna(voc_type) or (isinstance(voc_type, str) and not voc_type.strip()):
            null_errors.append(f" - Excel 행 {excel_row}: VOC유형이 입력되지 않음")
            invalid_indexes.add(idx)
        elif voc_type not in valid_types:
            invalid_errors.append(f" - Excel 행 {excel_row}: VOC유형 '{voc_type}'이(가) 유효하지 않음")
            invalid_indexes.add(idx)

    if null_errors:
        print("\n❗ VOC유형 누락:")
        for e in null_errors:
            print(e)
    else:
        print("\n✅ VOC유형 누락 없음")

    if invalid_errors:
        print("\n❗ VOC유형 유효하지 않음:")
        for e in invalid_errors:
            print(e)
    else:
        print("\n✅ 모든 VOC유형이 유효합니다")

    print("\n📋 VOC유형 유효성 검증 완료")
    return invalid_indexes

# ✅ 유효한 행만 남기기
def filter_valid_voc_rows(df, invalid_indexes):
    """
    유효하지 않은 인덱스를 제거하여 유효한 VOC 데이터만 반환합니다.

    Args:
        df (pd.DataFrame): 원본 VOC 데이터프레임
        invalid_indexes (set or list): 제거할 인덱스 목록

    Returns:
        pd.DataFrame: 유효한 VOC 데이터프레임 (인덱스 reset됨)
    """
    valid_df = df.drop(index=list(invalid_indexes)).reset_index(drop=True)
    print(f"\n📦 유효한 VOC 데이터 {len(valid_df)}건만 남김.")
    return valid_df
