#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from calendar import monthrange
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from collections import OrderedDict
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://test.api.amadeus.com"
DEFAULT_ORIGINS = ["서울", "청주"]
DEFAULT_REQUEST_DELAY = 0.12
DISCORD_EMBED_BATCH_SIZE = 10
DEFAULT_DISCORD_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36 AirfareBot/1.0"
)

# Amadeus Airport & City Search only accepts Latin keywords, so common Korean aliases
# are resolved locally before falling back to the API.
LOCATION_ALIASES = {
    "서울": ("SEL", "서울"),
    "김포": ("GMP", "김포"),
    "인천": ("ICN", "인천"),
    "청주": ("CJJ", "청주"),
    "도쿄": ("TYO", "도쿄"),
    "오사카": ("OSA", "오사카"),
    "사가": ("HSG", "사가"),
    "삿포로": ("SPK", "삿포로"),
    "후쿠오카": ("FUK", "후쿠오카"),
    "기타규슈": ("KKJ", "기타규슈"),
    "오이타": ("OIT", "오이타"),
    "다카마쓰": ("TAK", "다카마쓰"),
    "오키나와": ("OKA", "오키나와"),
    "나고야": ("NGO", "나고야"),
    "방콕": ("BKK", "방콕"),
    "다낭": ("DAD", "다낭"),
    "나트랑": ("CXR", "나트랑"),
    "세부": ("CEB", "세부"),
    "마닐라": ("MNL", "마닐라"),
    "타이베이": ("TPE", "타이베이"),
    "홍콩": ("HKG", "홍콩"),
    "상하이": ("SHA", "상하이"),
    "베이징": ("BJS", "베이징"),
    "싱가포르": ("SIN", "싱가포르"),
    "쿠알라룸푸르": ("KUL", "쿠알라룸푸르"),
    "하노이": ("HAN", "하노이"),
    "호치민": ("SGN", "호치민"),
    "파리": ("PAR", "파리"),
    "런던": ("LON", "런던"),
    "뉴욕": ("NYC", "뉴욕"),
    "로마": ("ROM", "로마"),
    "바르셀로나": ("BCN", "바르셀로나"),
    "다낭": {"DAD", "다낭"}
}

AIRLINE_ALIASES = {
    "7C": "제주항공",
    "BX": "에어부산",
    "KE": "대한항공",
    "LJ": "진에어",
    "MM": "피치항공",
    "NH": "전일본공수",
    "OZ": "아시아나항공",
    "RF": "플라이강원",
    "RS": "에어서울",
    "TW": "티웨이항공",
    "ZE": "이스타항공",
    "JL": "일본항공",
    "GK": "젯스타 재팬",
    "BC": "스카이마크",
    "6E": "인디고",
}

IATA_INPUT_PATTERN = re.compile(r"^(?P<label>.+?)\s*[:=]\s*(?P<code>[A-Za-z]{3})$")


class AmadeusApiError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedLocation:
    query: str
    iata_code: str
    display_name: str
    sub_type: str


@dataclass(frozen=True)
class FlightSummary:
    origin_query: str
    origin_code: str
    origin_name: str
    destination_query: str
    destination_code: str
    destination_name: str
    departure_date: str
    return_date: str
    price_total: str
    currency: str
    price_confirmed: bool
    source: str | None
    validating_airlines: list[str]
    marketing_airlines: list[str]
    operating_airlines: list[str]
    outbound_stops: int
    inbound_stops: int
    outbound_departure_at: str
    outbound_arrival_at: str
    inbound_departure_at: str
    inbound_arrival_at: str
    last_ticketing_date: str | None

    def price_decimal(self) -> Decimal:
        return Decimal(self.price_total)


class AmadeusClient:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        request_delay: float = DEFAULT_REQUEST_DELAY,
        timeout: int = 30,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip("/")
        self.request_delay = max(request_delay, 0.1)
        self.timeout = timeout
        self._access_token: str | None = None
        self._token_expires_at = 0.0
        self._last_request_at = 0.0

    def search_locations(self, keyword: str) -> list[dict[str, Any]]:
        response = self._request_json(
            "GET",
            "/v1/reference-data/locations",
            params={
                "subType": "CITY,AIRPORT",
                "keyword": keyword,
                "sort": "analytics.travelers.score",
                "view": "LIGHT",
                "page[limit]": 10,
            },
        )
        return response.get("data", [])

    def search_flight_offers(
        self,
        *,
        origin_code: str,
        destination_code: str,
        departure_date: date,
        return_date: date,
        adults: int,
        currency: str,
        max_results: int,
        non_stop: bool,
        travel_class: str | None,
    ) -> list[dict[str, Any]]:
        params = {
            "originLocationCode": origin_code,
            "destinationLocationCode": destination_code,
            "departureDate": departure_date.isoformat(),
            "returnDate": return_date.isoformat(),
            "adults": adults,
            "currencyCode": currency.upper(),
            "max": max_results,
            "nonStop": str(non_stop).lower(),
        }
        if travel_class:
            params["travelClass"] = travel_class.upper()

        response = self._request_json(
            "GET",
            "/v2/shopping/flight-offers",
            params=params,
        )
        return response.get("data", [])

    def price_flight_offers(
        self,
        flight_offers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not flight_offers:
            return []

        response = self._request_json(
            "POST",
            "/v1/shopping/flight-offers/pricing",
            json_body={
                "data": {
                    "type": "flight-offers-pricing",
                    "flightOffers": flight_offers,
                }
            },
            extra_headers={"X-HTTP-Method-Override": "POST"},
        )
        data = response.get("data")
        if isinstance(data, dict):
            offers = data.get("flightOffers")
            return offers if isinstance(offers, list) else []
        return data if isinstance(data, list) else []

    def _get_access_token(self) -> str:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token

        response = self._request_json(
            "POST",
            "/v1/security/oauth2/token",
            auth=False,
            form_body={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )
        access_token = response.get("access_token")
        expires_in = response.get("expires_in", 0)
        if not access_token:
            raise AmadeusApiError("Amadeus access token was not returned.")

        self._access_token = access_token
        self._token_expires_at = time.time() + int(expires_in)
        return access_token

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        auth: bool = True,
        form_body: dict[str, Any] | None = None,
        json_body: dict[str, Any] | list[Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        retry_on_401: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params, doseq=True)}"

        headers = {"Accept": "application/json"}
        body: bytes | None = None
        if auth:
            headers["Authorization"] = f"Bearer {self._get_access_token()}"
        if form_body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
            body = urlencode(form_body).encode("utf-8")
        if json_body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        if extra_headers:
            headers.update(extra_headers)

        request = Request(url, data=body, headers=headers, method=method)
        self._wait_for_rate_limit()

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401 and auth and retry_on_401:
                self._access_token = None
                self._token_expires_at = 0.0
                return self._request_json(
                    method,
                    path,
                    params=params,
                    auth=auth,
                    form_body=form_body,
                    retry_on_401=False,
                )
            raise AmadeusApiError(format_http_error(exc.code, payload)) from exc
        except URLError as exc:
            raise AmadeusApiError(f"Network error while calling Amadeus: {exc}") from exc

        if not raw:
            return {}

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AmadeusApiError(f"Invalid JSON returned by Amadeus: {raw[:200]}") from exc

    def _wait_for_rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_at
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_at = time.monotonic()


def format_http_error(status_code: int, payload: str) -> str:
    detail = payload
    try:
        parsed = json.loads(payload)
        errors = parsed.get("errors")
        if errors:
            primary = errors[0]
            detail = primary.get("detail") or primary.get("title") or payload
        else:
            detail = parsed.get("error_description") or parsed.get("detail") or payload
    except json.JSONDecodeError:
        detail = payload
    return f"Amadeus API error {status_code}: {detail}".strip()


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cleaned = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), cleaned)


def parse_destination_inputs(values: list[str]) -> list[str]:
    if not values:
        return []

    if len(values) == 1:
        raw = values[0].strip()
        if raw.startswith("[") and raw.endswith("]"):
            body = raw[1:-1].strip()
            if not body:
                return []
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = [part.strip() for part in body.split(",")]
            values = [str(item) for item in parsed]
        elif "," in raw:
            values = [part.strip() for part in raw.split(",")]

    cleaned_values = []
    for value in values:
        cleaned = value.strip().strip('"').strip("'")
        cleaned = cleaned.strip("[]")
        if cleaned.endswith(","):
            cleaned = cleaned[:-1].strip()
        if cleaned:
            cleaned_values.append(cleaned)
    return cleaned_values


def parse_target_month(value: str, *, today: date | None = None) -> tuple[int, int]:
    if today is None:
        today = date.today()

    value = value.strip()
    if re.fullmatch(r"\d{4}-\d{1,2}", value):
        year_text, month_text = value.split("-", 1)
        year = int(year_text)
        month = int(month_text)
    elif re.fullmatch(r"\d{1,2}", value):
        month = int(value)
        year = today.year if month >= today.month else today.year + 1
    else:
        raise ValueError("month는 YYYY-MM 또는 MM 형식이어야 합니다. 예: 2026-07, 7")

    if month < 1 or month > 12:
        raise ValueError("month 값은 1~12 범위여야 합니다.")
    return year, month


def generate_trip_windows(month_value: str, trip_days: int) -> list[tuple[date, date]]:
    if trip_days < 1:
        raise ValueError("trip-days는 1 이상이어야 합니다.")

    year, month = parse_target_month(month_value)
    last_day = monthrange(year, month)[1]
    windows = []
    for day in range(1, last_day + 1):
        departure_date = date(year, month, day)
        return_date = departure_date + timedelta(days=trip_days - 1)
        windows.append((departure_date, return_date))
    return windows


def resolve_location(query: str, client: AmadeusClient) -> ResolvedLocation:
    manual_match = IATA_INPUT_PATTERN.match(query)
    if manual_match:
        label = manual_match.group("label").strip()
        code = manual_match.group("code").upper()
        return ResolvedLocation(
            query=query,
            iata_code=code,
            display_name=label,
            sub_type="MANUAL",
        )

    stripped = query.strip()
    if re.fullmatch(r"[A-Za-z]{3}", stripped):
        code = stripped.upper()
        return ResolvedLocation(query=query, iata_code=code, display_name=code, sub_type="IATA")

    alias = LOCATION_ALIASES.get(stripped)
    if alias:
        return ResolvedLocation(
            query=query,
            iata_code=alias[0],
            display_name=alias[1],
            sub_type="ALIAS",
        )

    if any(ord(char) > 127 for char in stripped):
        raise ValueError(
            f"'{query}' 는 내장 별칭에 없어서 자동 해석할 수 없습니다. "
            "Amadeus 위치 검색은 라틴 문자 키워드만 지원하므로 `도시명=IATA` 형식으로 입력해 주세요."
        )

    candidates = client.search_locations(stripped)
    if not candidates:
        raise ValueError(f"'{query}' 에 해당하는 공항/도시를 찾지 못했습니다.")

    preferred = pick_location_candidate(candidates)
    return ResolvedLocation(
        query=query,
        iata_code=preferred.get("iataCode", "").upper(),
        display_name=preferred.get("name") or stripped,
        sub_type=str(preferred.get("subType", "UNKNOWN")).upper(),
    )


def pick_location_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if not candidates:
        raise ValueError("No location candidates available.")

    city_candidates = [candidate for candidate in candidates if str(candidate.get("subType")).upper() == "CITY"]
    return city_candidates[0] if city_candidates else candidates[0]


def build_flight_summary(
    *,
    origin: ResolvedLocation,
    destination: ResolvedLocation,
    departure_date: date,
    return_date: date,
    offers: list[dict[str, Any]],
    price_confirmed: bool,
) -> FlightSummary | None:
    cheapest_offer = find_cheapest_offer(offers)
    if cheapest_offer is None:
        return None

    price = cheapest_offer.get("price", {})
    itineraries = cheapest_offer.get("itineraries", [])
    if len(itineraries) < 2:
        return None

    outbound = itineraries[0]
    inbound = itineraries[1]
    outbound_segments = outbound.get("segments", [])
    inbound_segments = inbound.get("segments", [])
    if not outbound_segments or not inbound_segments:
        return None

    marketing_airlines, operating_airlines = extract_airline_codes(itineraries)

    return FlightSummary(
        origin_query=origin.query,
        origin_code=origin.iata_code,
        origin_name=origin.display_name,
        destination_query=destination.query,
        destination_code=destination.iata_code,
        destination_name=destination.display_name,
        departure_date=departure_date.isoformat(),
        return_date=return_date.isoformat(),
        price_total=str(price.get("grandTotal") or price.get("total")),
        currency=str(price.get("currency", "")),
        price_confirmed=price_confirmed,
        source=cheapest_offer.get("source"),
        validating_airlines=list(cheapest_offer.get("validatingAirlineCodes", [])),
        marketing_airlines=marketing_airlines,
        operating_airlines=operating_airlines,
        outbound_stops=max(len(outbound_segments) - 1, 0),
        inbound_stops=max(len(inbound_segments) - 1, 0),
        outbound_departure_at=str(outbound_segments[0].get("departure", {}).get("at", "")),
        outbound_arrival_at=str(outbound_segments[-1].get("arrival", {}).get("at", "")),
        inbound_departure_at=str(inbound_segments[0].get("departure", {}).get("at", "")),
        inbound_arrival_at=str(inbound_segments[-1].get("arrival", {}).get("at", "")),
        last_ticketing_date=cheapest_offer.get("lastTicketingDate"),
    )


def find_cheapest_offer(offers: list[dict[str, Any]]) -> dict[str, Any] | None:
    cheapest_offer: dict[str, Any] | None = None
    cheapest_total: Decimal | None = None

    for offer in offers:
        price = offer.get("price", {})
        total = price.get("grandTotal") or price.get("total")
        if total is None:
            continue
        try:
            total_decimal = Decimal(str(total))
        except (InvalidOperation, TypeError):
            continue
        if cheapest_total is None or total_decimal < cheapest_total:
            cheapest_total = total_decimal
            cheapest_offer = offer

    return cheapest_offer


def extract_airline_codes(itineraries: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    marketing_codes: list[str] = []
    operating_codes: list[str] = []

    for itinerary in itineraries:
        for segment in itinerary.get("segments", []):
            marketing_code = segment.get("carrierCode")
            operating_code = segment.get("operating", {}).get("carrierCode") or marketing_code
            if marketing_code and marketing_code not in marketing_codes:
                marketing_codes.append(str(marketing_code))
            if operating_code and operating_code not in operating_codes:
                operating_codes.append(str(operating_code))

    return marketing_codes, operating_codes


def rank_offers_by_price(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked: list[tuple[Decimal, dict[str, Any]]] = []
    for offer in offers:
        total = offer.get("price", {}).get("grandTotal") or offer.get("price", {}).get("total")
        if total is None:
            continue
        try:
            total_decimal = Decimal(str(total))
        except (InvalidOperation, TypeError):
            continue
        ranked.append((total_decimal, offer))
    ranked.sort(key=lambda item: item[0])
    return [offer for _, offer in ranked]


def select_offers_for_pricing(offers: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    if limit < 1:
        return []
    return rank_offers_by_price(offers)[:limit]


def iter_search_queries(
    origins: list[ResolvedLocation],
    destinations: list[ResolvedLocation],
    windows: list[tuple[date, date]],
    *,
    max_searches: int | None = None,
):
    query_index = 0
    for origin in origins:
        for destination in destinations:
            for departure_date, return_date in windows:
                if max_searches is not None and query_index >= max_searches:
                    return
                query_index += 1
                yield query_index, origin, destination, departure_date, return_date


def search_lowest_fares(args: argparse.Namespace) -> tuple[list[FlightSummary], list[str]]:
    load_dotenv()
    client_id = os.getenv("AMADEUS_CLIENT_ID") or os.getenv("AMADEUS_API_KEY")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET") or os.getenv("AMADEUS_API_SECRET")
    if not client_id or not client_secret:
        raise ValueError("AMADEUS_CLIENT_ID / AMADEUS_CLIENT_SECRET 환경변수가 필요합니다.")

    client = AmadeusClient(
        client_id,
        client_secret,
        base_url=args.base_url,
        request_delay=args.request_delay,
    )

    raw_destinations = parse_destination_inputs(args.destinations)
    raw_origins = parse_destination_inputs(args.origins)
    if not raw_destinations:
        raise ValueError("최소 1개의 destination이 필요합니다.")

    destinations = [resolve_location(destination, client) for destination in raw_destinations]
    origins = [resolve_location(origin, client) for origin in raw_origins]
    windows = generate_trip_windows(args.month, args.trip_days)
    max_searches = args.max_searches
    if max_searches is not None and max_searches < 1:
        raise ValueError("max-searches는 1 이상이어야 합니다.")

    results: list[FlightSummary] = []
    errors: list[str] = []
    total_queries = len(origins) * len(destinations) * len(windows)
    planned_queries = min(total_queries, max_searches) if max_searches is not None else total_queries

    for query_index, origin, destination, departure_date, return_date in iter_search_queries(
        origins,
        destinations,
        windows,
        max_searches=max_searches,
    ):
        if not args.quiet:
            print(
                f"[{query_index}/{planned_queries}] "
                f"{origin.display_name}({origin.iata_code}) -> "
                f"{destination.display_name}({destination.iata_code}) "
                f"{departure_date.isoformat()} ~ {return_date.isoformat()}",
                file=sys.stderr,
            )

        try:
            offers = client.search_flight_offers(
                origin_code=origin.iata_code,
                destination_code=destination.iata_code,
                departure_date=departure_date,
                return_date=return_date,
                adults=args.adults,
                currency=args.currency,
                max_results=args.max_results,
                non_stop=args.non_stop,
                travel_class=args.travel_class,
            )
        except AmadeusApiError as exc:
            errors.append(
                f"{origin.iata_code}->{destination.iata_code} "
                f"{departure_date.isoformat()}~{return_date.isoformat()}: {exc}"
            )
            continue

        priced_offers = offers
        price_confirmed = False
        if offers and not args.skip_price_confirmation:
            pricing_candidates = select_offers_for_pricing(
                offers,
                limit=args.confirm_top_offers,
            )
            if pricing_candidates:
                try:
                    confirmed_offers = client.price_flight_offers(pricing_candidates)
                    if confirmed_offers:
                        priced_offers = confirmed_offers
                        price_confirmed = True
                except AmadeusApiError as exc:
                    errors.append(
                        f"pricing {origin.iata_code}->{destination.iata_code} "
                        f"{departure_date.isoformat()}~{return_date.isoformat()}: {exc}"
                    )

        summary = build_flight_summary(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            offers=priced_offers,
            price_confirmed=price_confirmed,
        )
        if summary is not None:
            results.append(summary)

    results.sort(key=lambda item: item.price_decimal())
    return results, errors


def print_results(results: list[FlightSummary], *, limit: int) -> None:
    if not results:
        print("조건에 맞는 항공권을 찾지 못했습니다.")
        return

    grouped_results = group_results_by_route(results, limit=limit)
    total_groups = len(grouped_results)
    for group_index, (route_title, route_results) in enumerate(grouped_results.items(), start=1):
        print(route_title)
        for index, result in enumerate(route_results, start=1):
            print(f"  {index}. {format_schedule_line(result)}")
        if group_index < total_groups:
            print()


def write_output(path: str, results: list[FlightSummary], errors: list[str]) -> None:
    payload = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "results": [asdict(result) for result in results],
        "errors": errors,
    }
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def format_price(currency: str, amount: str) -> str:
    try:
        decimal_value = Decimal(amount)
    except InvalidOperation:
        return f"{currency} {amount}".strip()

    normalized = decimal_value.quantize(Decimal("1")) if decimal_value == decimal_value.to_integral() else decimal_value
    return f"{currency} {normalized:,.0f}" if normalized == normalized.to_integral() else f"{currency} {normalized:,}"


def format_airlines(codes: list[str]) -> str:
    if not codes:
        return "-"
    labels = []
    for code in codes:
        name = AIRLINE_ALIASES.get(code)
        labels.append(f"{name} ({code})" if name else code)
    return ", ".join(labels)


def describe_airlines(result: FlightSummary) -> str:
    operating = format_airlines(result.operating_airlines)
    validating = format_airlines(result.validating_airlines)
    if validating != "-" and result.operating_airlines and result.validating_airlines != result.operating_airlines:
        return f"operating={operating} | validating={validating}"
    return operating if operating != "-" else validating


def route_title_for_result(result: FlightSummary) -> str:
    return f"{result.origin_name} -> {result.destination_name}"


def format_schedule_line(result: FlightSummary) -> str:
    confirmation_label = "확정가" if result.price_confirmed else "검색가"
    return (
        f"{result.departure_date} ~ {result.return_date} / "
        f"{format_price(result.currency, result.price_total)} / "
        f"{describe_airlines(result)} / {confirmation_label}"
    )


def group_results_by_route(
    results: list[FlightSummary],
    *,
    limit: int,
) -> "OrderedDict[str, list[FlightSummary]]":
    grouped: "OrderedDict[str, list[FlightSummary]]" = OrderedDict()
    for result in results[:limit]:
        route_title = route_title_for_result(result)
        grouped.setdefault(route_title, []).append(result)
    return grouped


def build_discord_embeds(results: list[FlightSummary], *, limit: int) -> list[dict[str, Any]]:
    embeds = []
    for route_title, route_results in group_results_by_route(results, limit=limit).items():
        description_lines = [
            f"{index}. {format_schedule_line(result)}"
            for index, result in enumerate(route_results, start=1)
        ]
        embed = {
            "title": route_title,
            "color": 3447003,
            "description": "\n".join(description_lines),
            "footer": {
                "text": (
                    f"source={route_results[0].source or '-'} | "
                    f"첫 일정 발권일 {route_results[0].last_ticketing_date or '-'}"
                )
            },
        }
        embeds.append(embed)
    return embeds


def chunked(values: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    timeout: int = 30,
    user_agent: str = DEFAULT_DISCORD_USER_AGENT,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        payload_text = exc.read().decode("utf-8", errors="replace")
        if exc.code == 403 and "browser_signature_banned" in payload_text:
            raise RuntimeError(
                "Discord webhook error 403: Cloudflare가 현재 User-Agent를 차단했습니다. "
                "기본 User-Agent를 추가했으니 다시 시도해 보고, 계속 실패하면 .env에 "
                "DISCORD_USER_AGENT를 넣어 다른 값으로 바꿔 보세요. "
                f"원본 응답: {payload_text}"
            ) from exc
        raise RuntimeError(f"Discord webhook error {exc.code}: {payload_text}") from exc
    except URLError as exc:
        raise RuntimeError(f"Discord webhook network error: {exc}") from exc

    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def send_discord_results(
    webhook_url: str,
    results: list[FlightSummary],
    *,
    max_results: int,
    username: str = "Airfare Bot",
    errors: list[str] | None = None,
    user_agent: str = DEFAULT_DISCORD_USER_AGENT,
) -> None:
    embeds = build_discord_embeds(results, limit=max_results)
    if not embeds:
        content = "조건에 맞는 항공권을 찾지 못했습니다."
        if errors:
            content += f" 실패한 검색 {len(errors)}건"
        post_json(
            webhook_url,
            {"username": username, "content": content, "allowed_mentions": {"parse": []}},
            user_agent=user_agent,
        )
        return

    total_embed_count = len(embeds)
    for batch_index, embed_batch in enumerate(chunked(embeds, DISCORD_EMBED_BATCH_SIZE), start=1):
        summary = f"항공권 검색 결과 {min(max_results, len(results))}건 중 {len(embed_batch)}건"
        if total_embed_count > DISCORD_EMBED_BATCH_SIZE:
            summary += f" ({batch_index}/{(total_embed_count - 1) // DISCORD_EMBED_BATCH_SIZE + 1})"
        if batch_index == 1 and errors:
            summary += f" | 실패한 검색 {len(errors)}건"

        post_json(
            webhook_url,
            {
                "username": username,
                "content": summary,
                "embeds": embed_batch,
                "allowed_mentions": {"parse": []},
            },
            user_agent=user_agent,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search lowest round-trip flight fares in a month using Amadeus Flight Offers Search.",
    )
    parser.add_argument(
        "--destinations",
        nargs="+",
        required=True,
        help="목적지 목록. 예: 오사카 도쿄 또는 '[오사카, 도쿄]'",
    )
    parser.add_argument(
        "--trip-days",
        type=int,
        required=True,
        help="여행 일수. 7이면 7/1~7/7, 7/2~7/8 방식으로 검색합니다.",
    )
    parser.add_argument(
        "--month",
        required=True,
        help="검색 기준 출발 월. YYYY-MM 또는 MM 형식. 예: 2026-07, 7",
    )
    parser.add_argument(
        "--origins",
        nargs="+",
        default=DEFAULT_ORIGINS,
        help="출발지 목록. 기본값은 서울, 청주",
    )
    parser.add_argument("--adults", type=int, default=1, help="성인 승객 수")
    parser.add_argument(
        "--travel-class",
        default="ECONOMY",
        choices=["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
        help="좌석 등급. 기본값 ECONOMY",
    )
    parser.add_argument("--currency", default="KRW", help="통화 코드. 기본값 KRW")
    parser.add_argument(
        "--max-results",
        type=int,
        default=250,
        help="Amadeus에서 한 번에 가져올 최대 오퍼 수. 기본값 250",
    )
    parser.add_argument(
        "--confirm-top-offers",
        type=int,
        default=6,
        help="Flight Offers Price로 최종가 확인할 상위 후보 수. 기본값 6",
    )
    parser.add_argument(
        "--skip-price-confirmation",
        action="store_true",
        help="Flight Offers Price 재확인을 건너뛰고 검색가만 사용",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="표시할 최종 상위 결과 수. 기본값 20",
    )
    parser.add_argument(
        "--max-searches",
        type=int,
        help="실행할 최대 검색 조합 수. 테스트용으로 10처럼 제한할 때 사용",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("AMADEUS_BASE_URL", DEFAULT_BASE_URL),
        help="Amadeus base URL. 테스트 환경 기본값: https://test.api.amadeus.com",
    )
    parser.add_argument(
        "--request-delay",
        type=float,
        default=float(os.getenv("AMADEUS_REQUEST_DELAY", DEFAULT_REQUEST_DELAY)),
        help="Amadeus rate limit 보호용 요청 간격(초). 기본값 0.12",
    )
    parser.add_argument("--non-stop", action="store_true", help="직항만 검색")
    parser.add_argument("--quiet", action="store_true", help="진행 로그 숨기기")
    parser.add_argument("--output", help="전체 결과를 JSON으로 저장할 경로")
    parser.add_argument(
        "--discord-webhook-url",
        default=os.getenv("DISCORD_WEBHOOK_URL"),
        help="Discord webhook URL. 지정하면 결과를 embed 메시지로 전송합니다.",
    )
    parser.add_argument(
        "--discord-results-limit",
        type=int,
        default=10,
        help="Discord로 보낼 상위 결과 수. 기본값 10",
    )
    parser.add_argument(
        "--discord-username",
        default=os.getenv("DISCORD_WEBHOOK_USERNAME", "Airfare Bot"),
        help="Discord webhook 표시 이름",
    )
    parser.add_argument(
        "--discord-user-agent",
        default=os.getenv("DISCORD_USER_AGENT", DEFAULT_DISCORD_USER_AGENT),
        help="Discord webhook 요청 시 사용할 User-Agent",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.discord_webhook_url:
        args.discord_webhook_url = (
            os.getenv("DISCORD_WEBHOOK_URL")
            or os.getenv("DISCORD_WEBHOOK")
        )
    if not args.discord_username:
        args.discord_username = (
            os.getenv("DISCORD_WEBHOOK_USERNAME")
            or os.getenv("DISCORD_USERNAME")
            or "Airfare Bot"
        )
    if not args.discord_user_agent:
        args.discord_user_agent = os.getenv("DISCORD_USER_AGENT") or DEFAULT_DISCORD_USER_AGENT

    if "test.api.amadeus.com" in args.base_url:
        print(
            "warning: 현재 Amadeus test 환경을 사용 중입니다. test 환경 데이터는 제한적이고 cached 입니다.",
            file=sys.stderr,
        )
    print(
        "note: Current Amadeus API is using Production keys",
        file=sys.stderr,
    )

    try:
        results, errors = search_lowest_fares(args)
    except (ValueError, AmadeusApiError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print_results(results, limit=args.limit)
    if args.output:
        write_output(args.output, results, errors)
        print(f"\nJSON saved to {args.output}")

    if args.discord_results_limit < 1:
        print("discord-results-limit는 1 이상이어야 합니다.", file=sys.stderr)
        return 1

    if args.discord_webhook_url:
        try:
            send_discord_results(
                args.discord_webhook_url,
                results,
                max_results=args.discord_results_limit,
                username=args.discord_username,
                errors=errors,
                user_agent=args.discord_user_agent,
            )
            print("Discord webhook sent.")
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if errors:
        print(f"\nwarning: {len(errors)} queries failed. Use --output to inspect details.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
