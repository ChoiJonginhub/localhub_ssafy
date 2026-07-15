# 🌏 Seoul Connect - 공공데이터 기반 지역 정보 공유 커뮤니티

## 📌 프로젝트 소개

**Seoul Connect**는 공공데이터를 활용하여 지역 주민과 관광객이 지역 정보를 자유롭게 공유하고 소비할 수 있는 **익명 기반 지역 커뮤니티 서비스**입니다.

사용자는 별도의 회원가입 없이 게시글을 작성하고, 지역 관광지·축제·맛집 등의 정보를 공유할 수 있으며, AI 챗봇을 통해 지역 정보를 자연어로 검색할 수 있습니다.

본 프로젝트는 SSAFY 팀 프로젝트 과제로 진행되었으며, 공공데이터 기반 서비스 설계 및 AI 활용 경험을 목표로 개발되었습니다.

---

## 🎯 프로젝트 목표

* 공공데이터를 활용한 지역 정보 서비스 구축
* 회원가입 없는 간편한 익명 커뮤니티 제공
* AI 챗봇을 통한 지역 정보 검색 경험 제공
* 빠른 개발과 간단한 운영 환경 구축

---

## 🏙️ 서비스 대상 지역

> 전국 5개 권역 중 1개 권역 선택

* 서울

---

## ✨ 주요 기능

### 1. 익명 커뮤니티 게시판

* 게시글 작성
* 게시글 조회
* 게시글 수정
* 게시글 삭제
* 게시글 검색
* 조회수 기능
* 좋아요 기능

### 2. AI 지역 정보 챗봇

* 관광지 추천
* 축제 일정 조회
* 맛집 정보 조회
* 지역 정보 검색
* 커뮤니티 게시글 검색

### 3. 지도 시각화

* 선택 카테고리 위치 표시
* 마커 클러스터 지원
* 카테고리 필터링 지원

### 4. 데이터 시각화

* 카테고리 데이터 시각화
* 커뮤니티 통계 데이터 시각화

### 5. 모임 생성

* 관광지 모임 생성
* 모임 참가자 간 채팅

---

## 🛠 기술 스택

### Frontend

* Vue 3
* Vue Router
* Axios
* Leaflet.js

### Backend

* FastAPI
* SQLAlchemy
* SQLite

### AI

* OpenAI API

### Deployment

* Netlify (Frontend)
* Render (Backend)

### Development Environment

* VSCode
* Git
* GitLab
* GitHub Copilot

---

## 🏗 시스템 아키텍처

```text
사용자
   │
   ▼
Vue.js SPA
   │
   ├── 게시판 API 요청
   ├── 챗봇 API 요청
   └── 지도 데이터 조회
   │
   ▼
FastAPI REST API
   │
   ├── SQLite
   ├── JSON 공공데이터
   └── OpenAI API
```

---

## 📂 프로젝트 구조

```text
LocalHub
├── frontend
│   ├── src
│   │   ├── components
│   │   ├── pages
│   │   ├── router
│   │   ├── services
│   │   └── assets
│   └── public
│
├── backend
│   ├── app
│   │   ├── api
│   │   ├── models
│   │   ├── schemas
│   │   ├── services
│   │   └── database
│   └── main.py
│
├── data
│   └── region_data.json
│
└── README.md
```

---

## 🗄 데이터 구조

### Community Posts (SQLite)

| 컬럼명        | 타입       | 설명          |
| ---------- | -------- | ----------- |
| id         | INTEGER  | 게시글 ID      |
| title      | TEXT     | 게시글 제목      |
| content    | TEXT     | 게시글 내용      |
| password   | TEXT     | 수정/삭제용 비밀번호 |
| views      | INTEGER  | 조회수         |
| likes      | INTEGER  | 좋아요 수       |
| created_at | DATETIME | 생성일시        |
| updated_at | DATETIME | 수정일시        |

---

### Region Location Data (제공 JSON 데이터)

| 필드명           | 타입     | 설명             | 예시                   |
| ------------- | ------ | -------------- | -------------------- |
| contentid     | STRING | 관광 콘텐츠 고유 ID   | `2723499`            |
| contenttypeid | STRING | 콘텐츠 유형 ID      | `28`                 |
| title         | STRING | 관광지명           | `서울한양도성 백악구간`        |
| addr1         | STRING | 기본 주소          | `서울특별시 종로구 창의문로 118` |
| addr2         | STRING | 상세 주소 또는 부가 정보 | `창의문~혜화문`            |
| mapx          | DOUBLE | 경도(Longitude)  | `126.9664956513`     |
| mapy          | DOUBLE | 위도(Latitude)   | `37.5926044932`      |
| firstimage    | STRING | 대표 이미지 URL     | 관광지 대표 이미지           |
| firstimage2   | STRING | 보조 이미지 URL     | 추가 이미지               |
| tel           | STRING | 연락처            | `02-0000-0000`       |
| zipcode       | STRING | 우편번호           | `03020`              |
| createdtime   | STRING | 데이터 최초 생성일     | `20210625192622`     |
| modifiedtime  | STRING | 데이터 수정일        | `20260619093209`     |
| cpyrhtDivCd   | STRING | 저작권 유형         | `Type1`              |
| mlevel        | STRING | 지도 확대 레벨       | `6`                  |
| areacode      | STRING | 지역 코드          | `11`                 |
| sigungucode   | STRING | 시군구 코드         | `110`                |
| cat1          | STRING | 대분류 카테고리       | 관광/문화 등              |
| cat2          | STRING | 중분류 카테고리       | 세부 유형                |
| cat3          | STRING | 소분류 카테고리       | 세부 유형                |
| lDongRegnCd   | STRING | 법정동 지역 코드      | `11`                 |
| lDongSignguCd | STRING | 법정동 시군구 코드     | `110`                |
| lclsSystm1    | STRING | 관광 분류 체계 1     | `LS`                 |
| lclsSystm2    | STRING | 관광 분류 체계 2     | `LS01`               |
| lclsSystm3    | STRING | 관광 분류 체계 3     | `LS011900`           |

---

### 활용 예시

* **지도 시각화**

  * `mapx`, `mapy`
  * `title`
  * `firstimage`

* **챗봇 질의응답**

  * `title`
  * `addr1`
  * `cat1~cat3`

* **관광지 상세 페이지**

  * `title`
  * `firstimage`
  * `addr1`, `addr2`
  * `tel`

* **데이터 시각화 대시보드**

  * `contenttypeid`
  * `cat1~cat3`
  * `areacode`


---

## 🤖 챗봇 API

### Endpoint

```http
POST /api/chat
```

### Request

```json
{
  "message": "서울에서 추천할 만한 관광지는 어디야?"
}
```

### Response

```json
{
  "answer": "서울에서는 경복궁, 북촌한옥마을, 남산타워를 추천합니다."
}
```

---

## 🚀 실행 방법

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend

python -m venv venv

source venv/bin/activate
# Windows
# venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## 🔐 환경 변수

### Backend (.env)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
key_name=your_api_name
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5-mini
```

### Frontend (.env)

```env
VITE_API_BASE_URL=your_base_url
VITE_NAVER_MAP_CLIENT_ID=your_naver_api_key
```

---

## 🌐 배포 주소

### Frontend

* Netlify URL : https://44afy.netlify.app/

### Backend

* Render URL : https://localhub-ssafy-34ya.onrender.com

---

## 📋 산출물

* Git Repository : https://github.com/ChoiJonginhub/localhub_ssafy
* SQLite DB 파일
* 기능 명세서
* WBS
* 발표 자료
* 배포 URL

---

## 👥 팀원 역할

| 이름       | 역할              |
| -------- | --------------- |
| 최종인 | 기획 / 개발 / 배포 |
| 박기성 | 기획 / 개발 / 발표 |
| 이세진  | 기획 / 개발 / 발표자료 준비 |

---

## 📅 개발 일정

| 기간    | 작업               |
| ----- | ---------------- |
| Day 1 | DB 설계, 게시판 CRUD, 지도 시각화 |
| Day 2 | 챗봇 구현, 데이터 시각화 및 배포 |
| Day 3 | 버그 수정 및 발표 준비 |

---

## 📈 향후 개선 사항

* 실시간 알림 기능
* 다국어 지원
* 날씨 정보 연동
* 소셜 공유 기능
* 경로 안내 기능

---

## 📄 라이선스 및 데이터 출처

본 프로젝트는 공공데이터포털 및 제공된 JSON 데이터를 기반으로 제작되었습니다.

추가 데이터 사용 시 라이선스 및 공공누리 유형을 검토하여 활용하였습니다.
