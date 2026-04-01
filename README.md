# Lowest Fare Search With Amadeus

서울/청주에서 여러 목적지로 가는 왕복 항공권을 한 달 동안 슬라이딩 윈도우로 조회해서 최저가를 찾는 CLI입니다.

예를 들어 `trip-days=7`, `month=7` 이면 아래처럼 모든 출발일을 조회합니다.

- 7/1 ~ 7/7
- 7/2 ~ 7/8
- ...
- 7/31 ~ 8/6

기본 출발지는 `서울(SEL)` 과 `청주(CJJ)` 입니다.

주의:

- Amadeus Self-Service Flight Offers는 공식 문서 기준으로 저가항공사(LCC)를 반환하지 않습니다.
- 기본 테스트 환경(`test.api.amadeus.com`)은 제한적이고 cached 된 데이터입니다.
- 더 실제에 가까운 결과를 보려면 production 환경과 `travel-class=ECONOMY` 기준으로 확인하는 것이 좋습니다.
- 검색 결과 가격은 기본적으로 `Flight Offers Price`로 한 번 더 확인해서 확정가에 가깝게 정리합니다.

## 왜 Flight Offers Search를 썼나

Amadeus 공식 문서에 따르면 `Flight Cheapest Date Search` 는 캐시 기반이라 모든 노선을 보장하지 않습니다. 반면 `Flight Offers Search` 는 실시간 가격/재고 조회용이라 현재 요구사항에 더 잘 맞습니다.

공식 문서:

- Authorization: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/API-Keys/
- Flights tutorial: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/
- Rate limits: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/api-rate-limits/

## 준비

1. [Amadeus for Developers](https://developers.amadeus.com/) 에서 앱을 만들고 API Key / Secret 을 발급받습니다.
2. `.env.example` 를 참고해서 `.env` 를 만듭니다.

```bash
cp .env.example .env
```

3. `.env` 에 값을 채웁니다.

```dotenv
AMADEUS_CLIENT_ID=your_api_key
AMADEUS_CLIENT_SECRET=your_api_secret
AMADEUS_BASE_URL=https://test.api.amadeus.com
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token
DISCORD_WEBHOOK_USERNAME=Airfare Bot
DISCORD_USER_AGENT=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 AirfareBot/1.0
```

테스트 환경 대신 운영 환경을 쓰려면 `AMADEUS_BASE_URL=https://api.amadeus.com` 으로 바꾸면 됩니다.

## 실행 예시

가장 단순한 형태:

```bash
python3 airfare_search.py \
  --destinations 오사카 도쿄 \
  --trip-days 7 \
  --month 7 \
  --max-searches 10
```

리스트 문자열처럼 넘겨도 됩니다:

```bash
python3 airfare_search.py \
  --destinations "[오사카, 도쿄]" \
  --trip-days 7 \
  --month 2026-07 \
  --output july_fares.json
```

직항만 보고 싶으면:

```bash
python3 airfare_search.py \
  --destinations 오사카 도쿄 \
  --trip-days 7 \
  --month 7 \
  --non-stop
```

Discord로 깔끔한 카드 메시지를 보내려면:

```bash
python3 airfare_search.py \
  --destinations "사가=HSG" "후쿠오카=FUK" "기타규슈=KKJ" \
  --trip-days 7 \
  --month 7 \
  --max-searches 10 \
  --discord-results-limit 10
```

`.env` 에 `DISCORD_WEBHOOK_URL` 이 있으면 `--discord-webhook-url` 없이도 자동 전송됩니다.

Discord 메시지에는 각 결과별로 아래 필드가 들어갑니다.

- `서울 -> 다카마쓰` 같은 경로 제목
- 경로 아래에 `일정 / 가격 / 항공사 / 확정가 여부` 줄 목록

샘플 출력:

```text
 1. KRW  183200 | 서울(SEL) -> 오사카(OSA) | 2026-07-02 ~ 2026-07-08 | airline=TW | stops=0/0
 2. KRW  191400 | 청주(CJJ) -> 오사카(OSA) | 2026-07-09 ~ 2026-07-15 | airline=7C | stops=0/0
```

## 입력 규칙

- `--destinations`: 공백 구분 목록 또는 `"[오사카, 도쿄]"` 같은 문자열
- `--trip-days`: 여행 일수. `7` 이면 `7/1~7/7` 패턴
- `--month`: `YYYY-MM` 또는 `MM`
- `--origins`: 기본값은 `서울 청주`
- `--travel-class`: 기본값 `ECONOMY`
- `--max-results`: Amadeus 한 번 호출 시 받을 오퍼 수
- `--confirm-top-offers`: 최종가 확인할 상위 후보 수. 기본값 `6`
- `--skip-price-confirmation`: Flight Offers Price 재확인 생략
- `--limit`: 화면에 보여줄 상위 결과 수
- `--max-searches`: 실제 실행할 검색 조합 수 제한. 테스트할 때 `10` 추천
- `--output`: 전체 결과를 JSON으로 저장
- `--discord-webhook-url`: Discord webhook URL
- `--discord-results-limit`: Discord에 보낼 상위 결과 수
- `--discord-username`: Discord 메시지 발신 이름
- `--discord-user-agent`: Discord 전송 시 사용할 User-Agent

## 한글 도시명 주의

Amadeus Airport & City Search 는 라틴 문자 키워드 기준으로 동작합니다. 그래서 이 스크립트는 자주 쓰는 한글 도시명을 내장 별칭으로 먼저 처리합니다.

내장 별칭에 없는 도시를 한글로 넣고 싶으면 직접 IATA 코드를 붙여 주세요.

```bash
python3 airfare_search.py \
  --destinations "부다페스트=BUD" "프라하=PRG" \
  --trip-days 7 \
  --month 7
```

## 테스트

```bash
python3 -m unittest discover -s tests
```

## destination example

사가 : 15만
후쿠오카: 16만
기타규슈: 16만
오이타: 16.6만
다카마쓰: 17.4만
