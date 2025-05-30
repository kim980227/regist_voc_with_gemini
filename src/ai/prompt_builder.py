# prompt_builder.py

def build_voc_type_prompt(voc_content, voc_action, valid_types):
    """
    VOC 내용과 조치계획을 기반으로 VOC 유형 분류를 위한 프롬프트를 생성합니다.

    Parameters:
        voc_content (str): VOC 본문의 내용 (예: 고객 불만, 요청 등)
        voc_action (str): 조치 계획 및 처리 상황 내용
        valid_types (List[str]): 분류 가능한 VOC 유형 목록

    Returns:
        str: LLM에게 전달할 프롬프트 문자열
    """
    voc_content = voc_content.strip() if voc_content else ""
    voc_action = voc_action.strip() if voc_action else ""

    prompt = (
        "다음은 고객 VOC 내용입니다.\n"
        f"- 내용: {voc_content}\n"
        f"- 조치계획: {voc_action}\n\n"
        "VOC 유형은 아래 목록 중에서 가장 적절한 것을 하나만 선택하세요:\n"
        f"{', '.join(valid_types)}\n"
        "선택한 VOC 유형과 그 이유를 설명해주세요.\n\n"
        "형식:\n"
        "VOC 유형: [여기에 유형]\n"
        "이유: [여기에 이유]\n"
    )

    return prompt
