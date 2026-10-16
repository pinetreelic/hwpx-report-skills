# 문서 스타일 추가

기존 `sectioned` 폴더를 새 이름으로 복사하고 `style.json`의 `id`를 폴더명과 같게 설정한다.
원본 디자인 자산인 `components.json`도 함께 복사한다.
`name`, `description`, `title_color`, `section_color`, `section_fill`을 수정하면
`generate_numbered.py --list-styles`에 나타나며 `--style <id>`로 생성할 수 있다.
색상은 `#RRGGBB`로 작성한다. 폴더에 `preview.png`를 넣으면 사용자 선택 때 함께 보여준다.
기본형은 `engine: basic`, 섹션형은 `engine: sectioned`를 사용한다.
현재 기본형은 기존 외형 유지용이며 색상 오버라이드는 섹션 엔진에서 지원한다.

예: `sectioned`를 `green-sections`로 복사하고 세 색상을 녹색 계열로 변경한다.
이름·설명·색상 변형에는 Python 코드를 추가하지 않는다.

현재 두 엔진으로 표현할 수 없는 구성(예: 별도 표지·다단 본문)은 새 엔진 구현과 검증이
필요하다. JSON만으로 임의의 문서 구성을 만들 수 있다고 안내하지 않는다.
추가할 때는 가상 내용의 HWPX와 미리보기를 생성하고 validate·렌더를 확인한다.
개인·기관 문서의 내용이나 글꼴 파일을 스타일 폴더에 복사하지 않는다.
