"""TMDb API helper functions for CinePick.

이 파일은 TMDb에서 영화 데이터를 가져온 뒤 기존 템플릿에서 쓰기 편한 형태로 정리합니다.
API 키가 없을 때도 화면 확인이 가능하도록 fallback 데이터를 제공합니다.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"
DEFAULT_LANGUAGE = "ko-KR"
DEFAULT_REGION = "KR"
PLACEHOLDER_POSTER = "https://placehold.co/500x750/111827/ffffff?text=No+Poster"
PLACEHOLDER_BACKDROP = "https://placehold.co/1280x720/111827/ffffff?text=CinePick"
PLACEHOLDER_PROFILE = "https://placehold.co/160x160/111827/ffffff?text=No+Image"


FALLBACK_MOVIES: List[Dict[str, Any]] = [
    {
        "id": 693134,
        "title": "듄: 파트 2",
        "original_title": "Dune: Part Two, 2024",
        "rating": 4.8,
        "rating_count": "32,456",
        "genres": ["SF", "액션", "드라마"],
        "runtime": "166분",
        "age_rating": "12세 관람가",
        "director": "드니 빌뇌브",
        "cast": ["티모시 샬라메", "젠데이아", "오스틴 버틀러"],
        "backdrop": "https://image.tmdb.org/t/p/original/xOMo8BRK7PfcJv9JCnx7s5hj0PX.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/8b8R8l88Qje9dn9OE8PY05Nxl1X.jpg",
        "synopsis": "황제의 모략으로 모든 것을 잃은 폴 아트레이데스. 복수를 위한 여정이 시작된다. 운명을 넘어서, 새로운 미래를 향한 그의 선택은 사막의 전설로 이어진다.",
    },
    {
        "id": 1022789,
        "title": "인사이드 아웃 2",
        "original_title": "Inside Out 2, 2024",
        "rating": 4.6,
        "rating_count": "18,921",
        "genres": ["애니메이션", "코미디", "가족"],
        "runtime": "96분",
        "age_rating": "전체 관람가",
        "director": "켈시 만",
        "cast": ["에이미 포러", "마야 호크", "필리스 스미스"],
        "backdrop": "https://image.tmdb.org/t/p/original/stKGOm8wPL8wt48Dki6Z6b68bXm.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg",
        "synopsis": "머릿속 감정 컨트롤 본부에 찾아온 새로운 감정들! 사춘기를 맞이한 라일리의 일상은 예상치 못한 방향으로 흘러간다.",
    },
    {
        "id": 533535,
        "title": "데드풀과 울버린",
        "original_title": "Deadpool & Wolverine, 2024",
        "rating": 4.6,
        "rating_count": "21,482",
        "genres": ["액션", "코미디", "SF"],
        "runtime": "128분",
        "age_rating": "15세 관람가",
        "director": "숀 레비",
        "cast": ["라이언 레이놀즈", "휴 잭맨", "엠마 코린"],
        "backdrop": "https://image.tmdb.org/t/p/original/yDHYTfA3R0jFYba16jBB1ef8oIt.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg",
        "synopsis": "데드풀과 울버린이 만나 벌어지는 예측 불가능한 액션 코미디.",
    },
    {
        "id": 157336,
        "title": "인터스텔라",
        "original_title": "Interstellar, 2014",
        "rating": 4.5,
        "rating_count": "45,211",
        "genres": ["SF", "드라마", "모험"],
        "runtime": "169분",
        "age_rating": "12세 관람가",
        "director": "크리스토퍼 놀란",
        "cast": ["매튜 맥커너히", "앤 해서웨이", "제시카 차스테인"],
        "backdrop": "https://image.tmdb.org/t/p/original/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "synopsis": "인류의 미래를 찾기 위해 우주로 떠나는 탐사대의 이야기.",
    },
    {
        "id": 27205,
        "title": "인셉션",
        "original_title": "Inception, 2010",
        "rating": 4.6,
        "rating_count": "50,302",
        "genres": ["액션", "SF", "스릴러"],
        "runtime": "148분",
        "age_rating": "12세 관람가",
        "director": "크리스토퍼 놀란",
        "cast": ["레오나르도 디카프리오", "조셉 고든 레빗", "엘리엇 페이지"],
        "backdrop": "https://image.tmdb.org/t/p/original/s3TBrRGB1iav7gFOCNx3H31MoES.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg",
        "synopsis": "타인의 꿈속에 들어가 생각을 훔치는 전문가가 마지막 임무에 도전한다.",
    },
    {
        "id": 155,
        "title": "다크 나이트",
        "original_title": "The Dark Knight, 2008",
        "rating": 4.6,
        "rating_count": "57,114",
        "genres": ["액션", "범죄", "드라마"],
        "runtime": "152분",
        "age_rating": "15세 관람가",
        "director": "크리스토퍼 놀란",
        "cast": ["크리스찬 베일", "히스 레저", "아론 에크하트"],
        "backdrop": "https://image.tmdb.org/t/p/original/hkBaDkMWbLaf8B1lsWsKX7Ew3Xq.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "synopsis": "고담을 혼돈에 빠뜨리는 조커와 배트맨의 대결.",
    },
    {
        "id": 299536,
        "title": "어벤져스: 인피니티 워",
        "original_title": "Avengers: Infinity War, 2018",
        "rating": 4.4,
        "rating_count": "42,102",
        "genres": ["액션", "모험", "SF"],
        "runtime": "149분",
        "age_rating": "12세 관람가",
        "director": "앤서니 루소, 조 루소",
        "cast": ["로버트 다우니 주니어", "크리스 헴스워스", "마크 러팔로"],
        "backdrop": "https://image.tmdb.org/t/p/original/lmZFxXgJE3vgrciwuDib0N8CfQo.jpg",
        "poster": "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
        "synopsis": "우주를 위협하는 타노스에 맞서는 히어로들의 전쟁.",
    },
]


FALLBACK_PROVIDERS = [
    {"name": "Netflix", "logo": "https://image.tmdb.org/t/p/original/pbpMk2JmcoNnQwx5JGpXngfoWtp.jpg", "url": "https://www.netflix.com/kr/"},
    {"name": "Disney+", "logo": "https://image.tmdb.org/t/p/original/97yvRBw1GzX7fXprcF80er19ot.jpg", "url": "https://www.disneyplus.com/ko-kr"},
]


FALLBACK_CAST = [
    {"name": "티모시 샬라메", "role": "폴 아트레이데스", "img": "https://placehold.co/160x160/111827/ffffff?text=Cast"},
    {"name": "젠데이아", "role": "차니", "img": "https://placehold.co/160x160/111827/ffffff?text=Cast"},
    {"name": "오스틴 버틀러", "role": "페이드-로타", "img": "https://placehold.co/160x160/111827/ffffff?text=Cast"},
]


def has_credentials() -> bool:
    """TMDb API 인증 정보가 있는지 확인합니다."""
    return bool(os.getenv("TMDB_ACCESS_TOKEN") or os.getenv("TMDB_API_KEY"))


def image_url(path: Optional[str], size: str = "w500", fallback: str = PLACEHOLDER_POSTER) -> str:
    if not path:
        return fallback
    if path.startswith("http"):
        return path
    return f"{TMDB_IMAGE_BASE_URL}/{size}{path}"


def five_star_rating(vote_average: Any) -> float:
    """TMDb의 10점 만점 평점을 사이트 UI에 맞게 5점 만점으로 변환합니다."""
    try:
        return round(float(vote_average) / 2, 1)
    except (TypeError, ValueError):
        return 0.0


def estimate_rating_dist(rating: float) -> Dict[str, int]:
    """TMDb는 별점 분포를 제공하지 않으므로 화면용 분포를 평점 기반으로 추정합니다."""
    rating = max(0.0, min(5.0, float(rating or 0)))
    five = int(20 + rating * 13)
    four = int(45 - rating * 3)
    three = int(24 - rating * 3)
    two = max(1, int(8 - rating))
    one = max(1, 100 - (five + four + three + two))
    total = five + four + three + two + one
    return {
        "5": round(five / total * 100),
        "4": round(four / total * 100),
        "3": round(three / total * 100),
        "2": round(two / total * 100),
        "1": max(1, 100 - (round(five / total * 100) + round(four / total * 100) + round(three / total * 100) + round(two / total * 100))),
    }


def tmdb_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """TMDb v3 API를 호출합니다. API Key와 Bearer Token 방식을 모두 지원합니다."""
    params = dict(params or {})
    params.setdefault("language", DEFAULT_LANGUAGE)

    headers: Dict[str, str] = {}
    access_token = os.getenv("TMDB_ACCESS_TOKEN")
    api_key = os.getenv("TMDB_API_KEY")

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif api_key:
        params["api_key"] = api_key
    else:
        raise RuntimeError("TMDb API 키가 없습니다. .env 파일에 TMDB_API_KEY 또는 TMDB_ACCESS_TOKEN을 넣어주세요.")

    response = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def normalize_movie_card(item: Dict[str, Any], rank: Optional[int] = None, poster_size: str = "w500") -> Dict[str, Any]:
    """TMDb 원본 영화 데이터를 카드 UI에서 쓰는 형태로 바꿉니다."""
    if "poster" in item and "rating" in item:
        card = dict(item)
        if rank is not None:
            card["rank"] = rank
        return card

    title = item.get("title") or item.get("name") or item.get("original_title") or "제목 없음"
    card = {
        "id": item.get("id"),
        "rank": rank,
        "title": title,
        "rating": five_star_rating(item.get("vote_average")),
        "poster": image_url(item.get("poster_path"), poster_size),
        "backdrop": image_url(item.get("backdrop_path"), "original", PLACEHOLDER_BACKDROP),
        "overview": item.get("overview") or "줄거리 정보가 없습니다.",
    }
    return card


def normalize_movie_list(data: Dict[str, Any], limit: int = 10, poster_size: str = "w500") -> List[Dict[str, Any]]:
    items = [item for item in data.get("results", []) if item.get("overview", "").strip()]
    items = items[:limit]
    return [normalize_movie_card(item, rank=i + 1, poster_size=poster_size) for i, item in enumerate(items)]

def fallback_cards(limit: int = 10, poster_size: str = "w500") -> List[Dict[str, Any]]:
    return [normalize_movie_card(movie, rank=i + 1, poster_size=poster_size) for i, movie in enumerate(FALLBACK_MOVIES[:limit])]


def get_popular_movies(limit: int = 7) -> List[Dict[str, Any]]:
    if not has_credentials():
        return fallback_cards(limit, "w500")
    try:
        data = tmdb_get("/movie/popular", {"page": 1, "region": DEFAULT_REGION, "with_original_language": "ko|en"})
        return normalize_movie_list(data, limit, "w500")
    except Exception:
        return fallback_cards(limit, "w500")


def get_top_rated_movies(limit: int = 20) -> List[Dict[str, Any]]:
    if not has_credentials():
        return fallback_cards(limit, "w342")
    try:
        data = tmdb_get("/movie/top_rated", {"page": 1, "region": DEFAULT_REGION})
        return normalize_movie_list(data, limit, "w342")
    except Exception:
        return fallback_cards(limit, "w342")


def search_movies(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    query = (query or "").strip()
    if not query:
        return []
    if not has_credentials():
        result = [movie for movie in FALLBACK_MOVIES if query.lower() in movie["title"].lower()]
        return [normalize_movie_card(movie, rank=i + 1, poster_size="w342") for i, movie in enumerate(result[:limit])]
    try:
        data = tmdb_get("/search/movie", {"query": query, "page": 1, "include_adult": "false", "region": DEFAULT_REGION})
        return normalize_movie_list(data, limit, "w342")
    except Exception:
        return []


def discover_movies(with_genres: Optional[str] = None, sort_by: str = "popularity.desc", limit: int = 10) -> List[Dict[str, Any]]:
    if not has_credentials():
        return fallback_cards(limit, "w342")
    params: Dict[str, Any] = {
        "page": 1,
        "region": DEFAULT_REGION,
        "include_adult": "false",
        "sort_by": sort_by,
        "vote_count.gte": 100,
    }
    if with_genres:
        params["with_genres"] = with_genres
    try:
        data = tmdb_get("/discover/movie", params)
        return normalize_movie_list(data, limit, "w342")
    except Exception:
        return fallback_cards(limit, "w342")


def get_recommendations(movie_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    if not has_credentials():
        return fallback_cards(limit, "w342")
    try:
        data = tmdb_get(f"/movie/{movie_id}/recommendations", {"page": 1, "region": DEFAULT_REGION})
        return normalize_movie_list(data, limit, "w342")
    except Exception:
        return discover_movies(limit=limit)


def get_genres() -> List[Dict[str, Any]]:
    if not has_credentials():
        return [
            {"id": 28, "name": "액션"},
            {"id": 35, "name": "코미디"},
            {"id": 18, "name": "드라마"},
            {"id": 878, "name": "SF"},
            {"id": 16, "name": "애니메이션"},
        ]
    try:
        data = tmdb_get("/genre/movie/list")
        return data.get("genres", [])
    except Exception:
        return []


def extract_director(credits: Dict[str, Any]) -> str:
    directors = [person.get("name") for person in credits.get("crew", []) if person.get("job") == "Director"]
    return ", ".join([d for d in directors if d]) or "정보 없음"


def extract_crew(credits: Dict[str, Any]) -> List[Dict[str, str]]:
    role_map = {
        "Director": "감독",
        "Screenplay": "각본",
        "Writer": "각본",
        "Original Music Composer": "음악",
        "Director of Photography": "촬영",
        "Producer": "제작",
    }
    grouped: Dict[str, List[str]] = {}
    for person in credits.get("crew", []):
        job = person.get("job")
        name = person.get("name")
        if job in role_map and name:
            grouped.setdefault(role_map[job], [])
            if name not in grouped[role_map[job]]:
                grouped[role_map[job]].append(name)

    return [{"role": role, "name": ", ".join(names[:3])} for role, names in grouped.items()] or [
        {"role": "감독", "name": extract_director(credits)},
    ]


def extract_cast_list(credits: Dict[str, Any], limit: int = 8) -> List[Dict[str, str]]:
    cast = credits.get("cast", [])[:limit]
    result = []
    for person in cast:
        result.append(
            {
                "name": person.get("name") or "이름 없음",
                "role": person.get("character") or "역할 정보 없음",
                "img": image_url(person.get("profile_path"), "w185", PLACEHOLDER_PROFILE),
            }
        )
    return result or FALLBACK_CAST


def extract_age_rating(release_dates: Dict[str, Any]) -> str:
    for country in release_dates.get("results", []):
        if country.get("iso_3166_1") == "KR":
            for release in country.get("release_dates", []):
                certification = (release.get("certification") or "").strip()
                if certification:
                    if certification.upper() in {"ALL", "G"}:
                        return "전체 관람가"
                    if certification.isdigit():
                        return f"{certification}세 관람가"
                    return certification
    return "등급 정보 없음"


def extract_providers(watch_provider_data: Dict[str, Any]) -> List[Dict[str, str]]:
    kr_data = watch_provider_data.get("results", {}).get(DEFAULT_REGION, {})
    link = kr_data.get("link") or "https://www.themoviedb.org/"
    merged: List[Dict[str, Any]] = []
    for key in ("flatrate", "rent", "buy"):
        merged.extend(kr_data.get(key, []))

    providers: List[Dict[str, str]] = []
    seen = set()
    for provider in merged:
        name = provider.get("provider_name")
        if not name or name in seen:
            continue
        seen.add(name)
        providers.append(
            {
                "name": name,
                "logo": image_url(provider.get("logo_path"), "original", PLACEHOLDER_PROFILE),
                "url": link,
            }
        )
    return providers[:5]


def fallback_detail(movie_id: int) -> Dict[str, Any]:
    movie = next((m for m in FALLBACK_MOVIES if int(m["id"]) == int(movie_id)), FALLBACK_MOVIES[0])
    rating = movie.get("rating", 0)
    related = [normalize_movie_card(m, rank=i + 1, poster_size="w342") for i, m in enumerate(FALLBACK_MOVIES) if m["id"] != movie["id"]][:6]
    return {
        **movie,
        "rating_dist": estimate_rating_dist(rating),
        "providers": FALLBACK_PROVIDERS,
        "cast_list": FALLBACK_CAST,
        "crew": [
            {"role": "감독", "name": movie.get("director", "정보 없음")},
            {"role": "제작", "name": "TMDb 연동 전 예시 데이터"},
        ],
        "related": related,
    }


def normalize_movie_detail(data: Dict[str, Any]) -> Dict[str, Any]:
    rating = five_star_rating(data.get("vote_average"))
    release_year = (data.get("release_date") or "")[:4]
    credits = data.get("credits", {})
    cast_list = extract_cast_list(credits)
    recommendations = data.get("recommendations", {})

    return {
        "id": data.get("id"),
        "title": data.get("title") or "제목 없음",
        "original_title": f"{data.get('original_title') or data.get('title') or ''}{', ' + release_year if release_year else ''}",
        "rating": rating,
        "rating_count": f"{int(data.get('vote_count') or 0):,}",
        "genres": [genre.get("name") for genre in data.get("genres", []) if genre.get("name")],
        "runtime": f"{data.get('runtime')}분" if data.get("runtime") else "러닝타임 정보 없음",
        "age_rating": extract_age_rating(data.get("release_dates", {})),
        "director": extract_director(credits),
        "cast": [person["name"] for person in cast_list[:5]],
        "cast_list": cast_list,
        "crew": extract_crew(credits),
        "backdrop": image_url(data.get("backdrop_path"), "original", PLACEHOLDER_BACKDROP),
        "poster": image_url(data.get("poster_path"), "w500", PLACEHOLDER_POSTER),
        "synopsis": data.get("overview") or "줄거리 정보가 없습니다.",
        "rating_dist": estimate_rating_dist(rating),
        "providers": extract_providers(data.get("watch/providers", {})),
        "related": normalize_movie_list(recommendations, 6, "w342") or discover_movies(limit=6),
    }


def get_movie_detail(movie_id: int) -> Dict[str, Any]:
    if not has_credentials():
        return fallback_detail(movie_id)
    try:
        data = tmdb_get(
            f"/movie/{movie_id}",
            {
                "append_to_response": "credits,watch/providers,recommendations,release_dates",
                "region": DEFAULT_REGION,
            },
        )
        return normalize_movie_detail(data)
    except Exception:
        return fallback_detail(movie_id)
