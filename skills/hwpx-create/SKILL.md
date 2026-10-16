---
name: hwpx-create
description: "양식 없이 새 한글(HWPX) 문서를 만든다. 기획서·보고서·계획서·공문 생성 요청에서 양식 유무를 확인하고 public-report-style 기준으로 생성·검증한다. 기존 파일 수정은 hwpx-edit를 사용한다."
---

<!-- Copyright 2026 6aneffy (upstream material). Modified by Soonlee, 2026-10-15: renamed/rerouted skills and report layout or portable distribution references. SPDX-License-Identifier: Apache-2.0. See LICENSE and NOTICE in the containing skill directory. -->


# hwpx-create: 백지에서 한글 문서 만들기

원본: [6aneffy/hwpx-kit](https://github.com/6aneffy/hwpx-kit)의 `doc-create`.
로컬 수정: 2026-10-15 — 스킬명·역할 설명·상호 참조 변경 및 공통 문서 스타일 연결.

문서 생성 요청이면 **다른 무엇보다 먼저 — 파일 탐색·폴더 뒤지기 전에 —
AskUserQuestion으로 확인** (탐색은 토큰 낭비, 답이 "있음"일 때만 찾는다):

> "참고할 양식(hwpx/hwp) 파일이 있나요?"
> 1. 있음 — 파일 경로를 알려주거나 대화에 끌어다 놓기
> 2. 없음 — 백지에서 새로 만들기

이 질문에 hwpx-edit의 정보 게이트 질문(제목·주최기관·**장소**·일시·대상·정원·
구성)을 같이 묶어서 물으면 왕복이 준다 — **장소를 빼먹지 말 것** (실사용
테스트에서 누락된 항목).

## 공유본 실행 환경

먼저 public-report-style 스킬 디렉터리의 `scripts/setup_runtime.py --check`로 설치 상태를 확인한다.
사용자가 이 묶음의 설치/준비를 요청했으면 `scripts/setup_runtime.py`로 고정 버전 런타임을 설치한다.
런타임은 public-report-style/runtime 아래에 격리된다. Python CLI 호출은
`<runtime>/python/bin/python -m hwpx_kit.cli ...`(Windows: `python/Scripts/python.exe`)를 사용한다.
kordoc CLI는 `node <runtime>/node/node_modules/kordoc/dist/cli.js ...`로 호출할 수 있다.
공유본은 hwpx-kit-cli 0.13.1·python-hwpx 2.29.2·kordoc 4.9.0 조합을 기준으로 하며,
기능이 없다고 임의 최신 버전으로 올리지 말고 명령의 --help와 한계를 먼저 확인한다.

## 양식이 있다면 → hwpx-edit 흐름

경로를 받아 hwpx-edit 스킬의 흐름(신작이면 정보 게이트부터)으로 진행.
.hwp면 먼저 `hwpx-kit convert`.

## 양식이 없다면 → 새 문서 생성

이 공유본에는 기관/번들 HWPX 템플릿이 없다. 없는 템플릿을 찾거나 요구하지 않는다.
[공통 문단 규칙](../public-report-style/references/paragraph-layout.md)을 읽고 구조화한 Markdown을 작성한 뒤
`python3 ../public-report-style/scripts/generate_numbered.py <초안.md> --out <새문서.hwpx> --preset report`
로 생성한다(경로는 이 스킬 디렉터리 기준). 번호 체계, 제목 셀 높이 24mm, 본문 160%,
묶음 경계별 앞 여백 3·9·15pt를 적용한다. 기관 지정 양식이 있으면 hwpx-edit로 전환한다.
생성 후 validate → read → 렌더 확인. kordoc SVG는 근사이며 한글 실물 확인과 구분한다.

어느 경로든 내용 작성 전에 hwpx-edit의 정보 게이트(제목·기관·일시·장소·
대상·구성)를 그대로 적용 — 최소 충족 후 시작. 글머리 위계·표기는
public-report-style 스킬, 금액·날짜는 [format-convert 안내](../public-report-style/references/format-convert.md)을 따른다.

## 주의

- 사용자에게 특정 폴더 구조(incoming/ 등)를 가정하지 말 것 — 파일 위치는
  항상 물어서 받는다
- 백지 생성물도 원본 개념이 없을 뿐 결과물 관리는 동일: 사용자가 지정한
  위치에 저장하고 경로를 알려준다

## 디자인 선택

문서 종류와 별개로 public-report-style의 디자인 선택을 따른다. 미지정 시 기존
**기본 보고서형**을 유지한다. **섹션 구분형**을 선택하면
[섹션 구분형 명세](../public-report-style/references/sectioned-layout.md)의 생성·편집 경로를 쓴다.
기존 generate_numbered.py는 기본형 경로이며 섹션형에 기본형의 번호·24mm 제목 높이
후처리를 강제하지 않는다. 이미 제공된 양식이나 디자인 선택을 다시 묻지 않는다.
