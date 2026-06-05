# CinePick TMDb 백엔드 연동 버전

이 버전은 기존 프론트 화면을 유지하면서 Flask 백엔드가 TMDb API에서 영화 데이터를 가져오도록 수정한 파일입니다.

## 1. 설치

```bash
cd webapp_v2
pip install -r requirements.txt
```

## 2. TMDb API 키 설정

`.env.example` 파일을 복사해서 `.env` 파일을 만드세요.

```bash
copy .env.example .env
```

macOS/Linux라면:

```bash
cp .env.example .env
```

그리고 `.env` 파일 안에 본인 TMDb API 키를 넣으세요.

```env
TMDB_API_KEY=본인_API_KEY
```

Bearer Access Token을 쓰고 싶으면 아래처럼 넣어도 됩니다.

```env
TMDB_ACCESS_TOKEN=본인_ACCESS_TOKEN
```

## 3. 실행

```bash
python app.py
```

브라우저에서 아래 주소로 접속하세요.

```text
http://127.0.0.1:5000
```

## 4. 추가된 주요 기능

- `/` : TMDb 인기 영화 + 추천 영화 표시
- `/movies` : 인기 영화 목록
- `/movies?q=검색어` : 영화 검색
- `/movie/<movie_id>` : 영화 상세 정보, 출연진, 제작진, OTT 제공처, 추천 영화
- `/recommend` : 추천 영화 목록
- `/ranking` : 평점 높은 영화 목록
- `/api/movies/popular` : JSON API, 인기 영화
- `/api/movies/search?q=검색어` : JSON API, 검색
- `/api/movies/<movie_id>` : JSON API, 상세 정보
- `/api/movies/<movie_id>/recommend` : JSON API, 관련 추천 영화
- `/api/genres` : JSON API, 장르 목록

## 5. 참고

API 키가 없어도 화면 확인은 가능하도록 fallback 예시 데이터가 뜹니다. 하지만 실제 TMDb 데이터를 보려면 `.env` 파일에 API 키를 넣어야 합니다.
