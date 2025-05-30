# gemini_api.py
import google.generativeai as genai
import time
import os
import pandas as pd
import src.ai.prompt_builder as prompt_builder
from src.ai.api_usage_limiter import rate_limit_guard

REASON_LOG_PATH = "log/"

# config.py에서 필요한 전역 변수들 임포트
from src.config.config import (
    GEMINI_MODEL, # GEMINI_MODEL은 여기서 사용하지만, config에서 초기화만 할 것
)

def infer_voc_type_with_gemini(df_voc, voc_type_map, ):
    """
    Gemini 모델을 사용하여 VOC유형이 NaN인 경우 내용 기반으로 추론합니다.
    이 함수는 GEMINI_MODEL을 직접 사용하며, config.py에서 미리 초기화되어 있어야 합니다.
    """
    print("\n🔍 Gemini를 이용한 VOC유형 추론 시작")

    valid_types = list(voc_type_map.keys())
    updated_count = 0
    reasons = []
    # 로그 파일 경로를 함수 호출 시점에서 동적으로 생성
    # 디렉토리가 없으면 생성
    os.makedirs(REASON_LOG_PATH, exist_ok=True)
    # 현재 날짜와 시간을 'YYYYMMDD_HHMMSS' 형식으로 포맷팅
    timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    reason_log_path = os.path.join(REASON_LOG_PATH, f"voc_infer_log_{timestamp}.txt")

    # 'VOC유형' 컬럼이 존재하지 않으면 추가 (DataFrame이 비어있을 경우를 대비)
    if 'VOC유형' not in df_voc.columns:
        df_voc['VOC유형'] = None # 또는 적절한 기본값

    # VOC 유형이 NaN인 행만 필터링하여 순회
    for idx, row in df_voc[df_voc['VOC유형'].isna()].iterrows():
        voc_content = str(row.get("VOC내용", "")).strip() # NaN이면 빈 문자열로
        voc_action = str(row.get("조치계획 및 진행상황", "")).strip() # NaN이면 빈 문자열로

        prompt = prompt_builder.build_voc_type_prompt(voc_content, voc_action, valid_types)

        try:
            # ✅ 사용량 제한 체크
            token_estimate = len(prompt) // 2 # 대략적인 토큰 수 계산 (보수적 추정)
            rate_limit_guard(tokens_used=token_estimate)

            # 🔍 Gemini API 호출
            response = GEMINI_MODEL.generate_content(prompt) # config에서 임포트한 GEMINI_MODEL 사용
            text = response.text.strip()

            # ✅ 결과 파싱
            predicted_type = next((t for t in valid_types if t in text), None)
            if predicted_type:
                df_voc.at[idx, 'VOC유형'] = predicted_type
                updated_count += 1
                reason_line = f"[Excel 행 {idx + 2}] 예측된 유형: {predicted_type} / 이유: {text}\n"
                reasons.append(reason_line)
                print(reason_line.strip())
            else:
                reason_line = f"[Excel 행 {idx + 2}] ❌ 유형 예측 실패 / 응답: {text}\n"
                reasons.append(reason_line)
                print(reason_line.strip())
            time.sleep(1) # API 호출 간 짧은 지연 추가 (과도한 요청 방지)

        except RuntimeError as e: # rate_limit_guard에서 발생시키는 예외
            reason_line = f"[Excel 행 {idx + 2}] ❌ Gemini 호출 제한: {e}\n"
            reasons.append(reason_line)
            print(reason_line.strip())
            break # 제한에 걸리면 더 이상 진행하지 않음
        except Exception as e:
            reason_line = f"[Excel 행 {idx + 2}] ❌ Gemini 호출 오류: {e}\n"
            reasons.append(reason_line)
            print(reason_line.strip())

    print(f"✅ VOC유형이 없는 {updated_count}건에 대해 유형을 추론하여 반영했습니다.")

    if reasons:
        with open(reason_log_path, "w", encoding="utf-8") as f:
            f.writelines(reasons)
        print(f"📁 추론 이유는 '{reason_log_path}'에 저장되었습니다.")

    return df_voc