import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

# 이 파일 기준 backend/data/ 폴더를 바라봄
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 카테고리 이름 -> 파일명 매핑 (필요하면 다른 지역 파일도 여기에 추가)
FILE_MAP = {
    "관광지": "서울_관광지.json",
    "레포츠": "서울_레포츠.json",
    "문화시설": "서울_문화시설.json",
    "쇼핑": "서울_쇼핑.json",
    "숙박": "서울_숙박.json",
    "여행코스": "서울_여행코스.json",
    "축제공연행사": "서울_축제공연행사.json",
}


@lru_cache(maxsize=1)
def _load_all() -> dict:
    """카테고리별 items 리스트를 프로세스당 한 번만 메모리에 로드(lru_cache로 캐싱)"""
    data = {}
    for category, filename in FILE_MAP.items():
        path = DATA_DIR / filename
        if not path.exists():
            continue
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        data[category] = payload.get("items", [])
    return data


def search(
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    district: Optional[str] = None,
    limit: int = 10,
) -> list[dict]:
    """
    지역 정보 검색.

    category: 관광지/레포츠/문화시설/쇼핑/숙박/여행코스/축제공연행사 중 하나. 없으면 전체 카테고리 대상.
    keyword: title에 포함되어야 하는 검색어 (예: '한강', '박물관')
    district: addr1에 포함되어야 하는 구/동 이름 (예: '강남구', '홍대')
    """
    all_data = _load_all()
    categories = [category] if category in all_data else list(all_data.keys())

    results = []
    for cat in categories:
        for item in all_data.get(cat, []):
            if keyword and keyword not in (item.get("title") or ""):
                continue
            if district and district not in (item.get("addr1") or ""):
                continue
            results.append(
                {
                    "category": cat,
                    "title": item.get("title"),
                    "addr": item.get("addr1"),
                    "tel": item.get("tel") or None,
                    "mapx": item.get("mapx"),
                    "mapy": item.get("mapy"),
                }
            )
            if len(results) >= limit:
                return results
    return results