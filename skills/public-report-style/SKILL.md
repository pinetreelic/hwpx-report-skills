---
name: public-report-style
description: "공공기관 보고서·계획서의 번호·표기·제목·문단 배치를 맞춘다. 기본 보고서형과 섹션 구분형 디자인을 지원한다. 새 문서의 디자인 미지정 시 선택을 안내하고 기본 추천은 기본 보고서형이다. 새 파일 생성은 hwpx-create, 기존 파일 수정은 hwpx-edit와 연결하며 기관 지정 양식과 사용자 지정 형식을 우선한다."
---

<!-- Copyright 2026 6aneffy (upstream material). Modified by Soonlee, 2026-10-15: renamed/rerouted skills and report layout or portable distribution references. SPDX-License-Identifier: Apache-2.0. See LICENSE and NOTICE in the containing skill directory. -->


# public-report-style: 공공기관 보고서·계획서 스타일

원본: [6aneffy/hwpx-kit](https://github.com/6aneffy/hwpx-kit)의 `gongmun-format`.
로컬 수정: 2026-10-15 — 스킬명·역할 설명·상호 참조 변경 및 공통 문서 스타일 연결.

공공기관 보고서 작성 관행을 따른 기본 서식이다. 보고서·계획서의 번호·표기·제목·문단 배치를
일관되게 맞춘다. 행정문서의 표기 규칙을 함께 참고하되, 정부 전체의 단일 의무 양식을 뜻하지 않는다.

## 공유본 실행 환경

먼저 public-report-style 스킬 디렉터리의 `scripts/setup_runtime.py --check`로 설치 상태를 확인한다.
사용자가 이 묶음의 설치/준비를 요청했으면 `scripts/setup_runtime.py`로 고정 버전 런타임을 설치한다.
런타임은 public-report-style/runtime 아래에 격리된다. Python CLI 호출은
`<runtime>/python/bin/python -m hwpx_kit.cli ...`(Windows: `python/Scripts/python.exe`)를 사용한다.
kordoc CLI는 `node <runtime>/node/node_modules/kordoc/dist/cli.js ...`로 호출할 수 있다.
공유본은 hwpx-kit-cli 0.13.1·python-hwpx 2.29.2·kordoc 4.9.0 조합을 기준으로 하며,
기능이 없다고 임의 최신 버전으로 올리지 말고 명령의 --help와 한계를 먼저 확인한다.

## 디자인 선택

문서 종류와 디자인은 별개다. 새 문서에서 사용자가 스타일을 지정하지 않았고
기관 양식도 없다면 아래 두 가지를 미리보기와 함께 한 번 묻는다.

- **기본 보고서형** (`basic-report`): 파란 제목 띠와 번호 중심 구성
- **섹션 구분형** (`sectioned`): 로마숫자 섹션 상자와 소제목·글머리표 구성
- **알아서 선택**: 짧고 연속적인 항목은 기본형, 큰 주제가 나뉘면 섹션형을 추천

선택 UI가 없으면 같은 내용을 짧은 번호 목록으로 묻는다. 사용자가 이미 선택했거나
기존 양식을 제공하면 다시 묻지 않는다. 기본 추천값은 기존 기본 보고서형이다.
`generate_numbered.py --list-styles`로 설치된 스타일 목록을 읽고 각 `styles/<id>/preview.png`를
보여줄 수 있다. 명시한 형식은 생성·후처리·검증까지 유지한다.
기관 양식·기존 문서 내용 수정에는 디자인을 자동 변경하지 않는다.

- [기본 보고서형 생성 규칙](references/paragraph-layout.md)
- [섹션 구분형 생성 규칙](references/sectioned-layout.md)
- [새 스타일 추가 방법](styles/README.md)

## 글머리 위계와 문단 배치

기본 보고서형의 새 공문·보고서·계획서 위계는 `1. → 가. → 1) → 가) → (1) → (가) → ① → ㉮`다.
이는 사용자가 선택한 공통 기본값이며, 모든 보고서에 법적으로 강제되는 체계라는 뜻은 아니다.
`※`와 `*`는 위계 밖 참고·주석이다. 기존 문서·기관 지정 양식·사용자 지정 형식은 보존한다.

새 문서 생성이나 승인된 서식 정규화 때 [공통 문단 규칙](references/paragraph-layout.md)을
읽고 입력 구조·생성 경로·검증을 따른다. 번호를 본문에 중복 입력하거나 공백으로
내어쓰기를 흉내 내지 않는다. 기존 문서의 내용 교체만 요청되면 번호/서식을 바꾸지 않는다.

## 표기 규약

- **날짜**: `2026.1.1.(목)` — 0 없음, 일 뒤 마침표, 요일 괄호. 기간은 `~`로:
  `26. 7. 6.(월) ~ 9. 4.(금)`. 요일 계산은 `hwpx-kit fmt --date` (암산 금지)
- **금액**: 법정 병기 `금12,340원(금일만이천삼백사십원)` — `hwpx-kit fmt --amount`
  ([format-convert 안내](references/format-convert.md) 참고. 민간 서류는 ilgeum 스타일)
- **법령·문서명**: 홑낫표 `「」` 로 감싼다 — `「행정 효율과 협업 촉진에 관한 규정」`
- **증감·비율**: [table-calc 안내](references/table-calc.md)의 표기 관습(△·%p 등) 따름

## 제출 전 검수 — "검토해줘" (기계 검사 먼저, 판단은 그 위에)

`hwpx-kit inspect <문서.hwpx> --json` — 결정론 검사 3종 (fmt와 같은 "암산 금지" 원칙):
- **residue**: 채우다 만 {{마커}}·○○○ 자리표시·"(예시)" 안내문 잔존
- **gongmun**: 날짜 하이픈 표기(2026-07-10 → `2026. 7. 10.`), 오전/오후 시각(→ 24시각제)
- **pii**: 주민번호·휴대전화·이메일 잔존 (공개 배포 문서면 특히)

종료코드 2 = 위반 있음. `issues[]`의 code·context를 **사람 말로 요약**해 보여주고,
수정할 항목을 확정받아 fill(text:/delete:)로 고친 뒤 재검사. 기계 검사가 못 보는
것(위계 건너뜀, 어색한 문장, 내용 누락)은 read 출력을 직접 읽고 이 스킬 규약으로 판단.

## 텍스트 정리 (재작성 계열 — 우리가 범피스보다 잘하는 것)

한글 문서에서 read로 뽑은 텍스트나 사용자가 붙여넣은 텍스트가 깨져 있으면:

- **어절정리**: 엔터로 어절이 중간에 잘린 문장(`...체계 구\n축 필요`)을 문맥으로
  이어붙여 복구. 원문 의미 변경 금지 — 줄바꿈·공백만 복구
- **붙여넣기 정리**: PDF/엑셀 복붙 산물(불필요한 줄바꿈, 이중 공백, 페이지 번호
  찌꺼기, 하이픈 분절)을 자연 문장으로 복원
- 정리 결과를 문서에 반영할 땐 `text:<깨진 원문>` → 복구문 교체 (hwpx-edit 흐름)

## 강조 (굵게·밑줄)

fill의 서식 키로 적용한다 (hwpx-edit 흐름 그대로):
`{"bold:<원문>": ""}` — 원문을 품은 런을 굵게. `{"underline:<원문>": ""}` — 밑줄.

- **런 단위 적용**: 원문이 문장 일부면 그 부분이 별도 런일 때만 정밀 강조됨 —
  런이 더 크면 그 런 전체가 굵어진다. read로 원문 확인 후 고유한 구 단위로 지정
- 배경색(연노란) 강조는 미지원 — 필요하면 한글에서 마무리 안내

## 신구대조표 (규정·법령 개정 대비표)

규정/지침/법령을 개정할 때 "현행 → 개정"을 나란히 보이는 신구대조표는
`diff` 명령으로 자동 생성한다 ("규정 뭐 바뀌었는지 대조표 만들어줘" 류):

- `hwpx-kit diff <현행.hwpx> <개정.hwpx> --out <신구대조표.hwpx>` →
  현행|개정 2열 표(가운데 제목 + 파란 헤더), **변경 조항만** 행으로. 순수
  파이썬 비교(difflib) — 한글 불필요
- 리포트만: `hwpx-kit diff <현행> <개정> --json` → 변경 요약(equal/insert/
  delete/replace 개수) + 블록. 표 안 만들고 무엇이 바뀌었는지 먼저 확인용
- `--full`이면 변경 없는 조항도 표에 포함(전문 대조), 기본은 변경분만
- **비교 단위 = 본문 최상위 문단** (조항 한 줄 = 한 문단 전제). 표 안 내용
  diff·어절 단위 밑줄은 아직 미지원 — 어절 강조는 위 `underline:` 키로 수동
- 생성 후 `validate` + (조판 의심 시) `render`로 확인
