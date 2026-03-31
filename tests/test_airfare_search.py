import unittest
from datetime import date

from airfare_search import (
    build_discord_embeds,
    format_airlines,
    format_price,
    FlightSummary,
    generate_trip_windows,
    iter_search_queries,
    parse_destination_inputs,
    parse_target_month,
    ResolvedLocation,
    resolve_location,
)


class FakeClient:
    def search_locations(self, keyword):
        return [
            {"subType": "CITY", "name": "Tokyo", "iataCode": "TYO"},
            {"subType": "AIRPORT", "name": "Tokyo Haneda", "iataCode": "HND"},
        ]


class AirfareSearchTests(unittest.TestCase):
    def test_parse_destination_inputs_supports_bracket_string(self):
        self.assertEqual(
            parse_destination_inputs(["[오사카, 도쿄, 후쿠오카]"]),
            ["오사카", "도쿄", "후쿠오카"],
        )

    def test_parse_destination_inputs_supports_unquoted_shell_split_list(self):
        self.assertEqual(
            parse_destination_inputs(["[오사카,", "도쿄]"]),
            ["오사카", "도쿄"],
        )

    def test_parse_target_month_supports_short_month(self):
        self.assertEqual(parse_target_month("7", today=date(2026, 3, 31)), (2026, 7))

    def test_parse_target_month_rolls_to_next_year_for_past_month(self):
        self.assertEqual(parse_target_month("2", today=date(2026, 3, 31)), (2027, 2))

    def test_generate_trip_windows_keeps_every_departure_day_in_month(self):
        windows = generate_trip_windows("2026-07", 7)
        self.assertEqual(len(windows), 31)
        self.assertEqual(windows[0][0].isoformat(), "2026-07-01")
        self.assertEqual(windows[0][1].isoformat(), "2026-07-07")
        self.assertEqual(windows[-1][0].isoformat(), "2026-07-31")
        self.assertEqual(windows[-1][1].isoformat(), "2026-08-06")

    def test_iter_search_queries_stops_after_max_searches(self):
        origins = [ResolvedLocation("서울", "SEL", "서울", "ALIAS")]
        destinations = [
            ResolvedLocation("오사카", "OSA", "오사카", "ALIAS"),
            ResolvedLocation("도쿄", "TYO", "도쿄", "ALIAS"),
        ]
        windows = generate_trip_windows("2026-07", 7)

        queries = list(iter_search_queries(origins, destinations, windows, max_searches=10))

        self.assertEqual(len(queries), 10)
        self.assertEqual(queries[0][0], 1)
        self.assertEqual(queries[-1][0], 10)

    def test_format_price_adds_grouping(self):
        self.assertEqual(format_price("KRW", "183200"), "KRW 183,200")

    def test_format_airlines_uses_human_readable_names(self):
        self.assertEqual(format_airlines(["TW", "7C"]), "티웨이항공 (TW), 제주항공 (7C)")

    def test_build_discord_embeds_contains_requested_fields(self):
        result = FlightSummary(
            origin_query="서울",
            origin_code="SEL",
            origin_name="서울",
            destination_query="후쿠오카",
            destination_code="FUK",
            destination_name="후쿠오카",
            departure_date="2026-07-01",
            return_date="2026-07-07",
            price_total="183200",
            currency="KRW",
            validating_airlines=["TW"],
            outbound_stops=0,
            inbound_stops=0,
            outbound_departure_at="2026-07-01T10:00:00",
            outbound_arrival_at="2026-07-01T11:30:00",
            inbound_departure_at="2026-07-07T12:00:00",
            inbound_arrival_at="2026-07-07T13:30:00",
            last_ticketing_date="2026-06-29",
        )

        embed = build_discord_embeds([result], limit=1)[0]
        field_names = [field["name"] for field in embed["fields"]]

        self.assertEqual(embed["title"], "#1 서울 -> 후쿠오카")
        self.assertEqual(field_names, ["일정", "출발", "도착", "가격", "항공사"])

    def test_resolve_location_supports_korean_aliases(self):
        resolved = resolve_location("도쿄", FakeClient())
        self.assertEqual(resolved.iata_code, "TYO")
        self.assertEqual(resolved.display_name, "도쿄")

    def test_resolve_location_supports_explicit_manual_mapping(self):
        resolved = resolve_location("오사카=OSA", FakeClient())
        self.assertEqual(resolved.iata_code, "OSA")
        self.assertEqual(resolved.display_name, "오사카")


if __name__ == "__main__":
    unittest.main()
