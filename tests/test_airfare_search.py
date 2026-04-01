import unittest
from datetime import date

from airfare_search import (
    build_discord_embeds,
    describe_airlines,
    extract_airline_codes,
    format_schedule_line,
    format_airlines,
    format_price,
    FlightSummary,
    generate_trip_windows,
    group_results_by_route,
    iter_search_queries,
    parse_destination_inputs,
    parse_target_month,
    ResolvedLocation,
    resolve_location,
    select_offers_for_pricing,
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
            price_confirmed=True,
            source="GDS",
            validating_airlines=["TW"],
            marketing_airlines=["TW"],
            operating_airlines=["TW"],
            outbound_stops=0,
            inbound_stops=0,
            outbound_departure_at="2026-07-01T10:00:00",
            outbound_arrival_at="2026-07-01T11:30:00",
            inbound_departure_at="2026-07-07T12:00:00",
            inbound_arrival_at="2026-07-07T13:30:00",
            last_ticketing_date="2026-06-29",
        )

        embed = build_discord_embeds([result], limit=1)[0]
        self.assertEqual(embed["title"], "서울 -> 후쿠오카")
        self.assertIn("1. 2026-07-01 ~ 2026-07-07 / KRW 183,200 / 티웨이항공 (TW) / 확정가", embed["description"])

    def test_extract_airline_codes_prefers_operating_carrier_when_present(self):
        marketing, operating = extract_airline_codes(
            [
                {
                    "segments": [
                        {"carrierCode": "NH", "operating": {"carrierCode": "LJ"}},
                        {"carrierCode": "NH", "operating": {"carrierCode": "NH"}},
                    ]
                }
            ]
        )

        self.assertEqual(marketing, ["NH"])
        self.assertEqual(operating, ["LJ", "NH"])

    def test_describe_airlines_shows_operating_and_validating_when_they_differ(self):
        result = FlightSummary(
            origin_query="서울",
            origin_code="SEL",
            origin_name="서울",
            destination_query="다카마쓰",
            destination_code="TAK",
            destination_name="다카마쓰",
            departure_date="2026-07-01",
            return_date="2026-07-07",
            price_total="200000",
            currency="KRW",
            price_confirmed=True,
            source="GDS",
            validating_airlines=["NH"],
            marketing_airlines=["NH"],
            operating_airlines=["LJ"],
            outbound_stops=0,
            inbound_stops=0,
            outbound_departure_at="2026-07-01T10:00:00",
            outbound_arrival_at="2026-07-01T11:30:00",
            inbound_departure_at="2026-07-07T12:00:00",
            inbound_arrival_at="2026-07-07T13:30:00",
            last_ticketing_date="2026-06-29",
        )

        self.assertEqual(
            describe_airlines(result),
            "operating=진에어 (LJ) | validating=전일본공수 (NH)",
        )

    def test_group_results_by_route_groups_schedule_lines_under_one_route(self):
        result_one = FlightSummary(
            origin_query="서울",
            origin_code="SEL",
            origin_name="서울",
            destination_query="다카마쓰",
            destination_code="TAK",
            destination_name="다카마쓰",
            departure_date="2026-07-01",
            return_date="2026-07-07",
            price_total="200000",
            currency="KRW",
            price_confirmed=True,
            source="GDS",
            validating_airlines=["LJ"],
            marketing_airlines=["LJ"],
            operating_airlines=["LJ"],
            outbound_stops=0,
            inbound_stops=0,
            outbound_departure_at="2026-07-01T10:00:00",
            outbound_arrival_at="2026-07-01T11:30:00",
            inbound_departure_at="2026-07-07T12:00:00",
            inbound_arrival_at="2026-07-07T13:30:00",
            last_ticketing_date="2026-06-29",
        )
        result_two = FlightSummary(
            origin_query="서울",
            origin_code="SEL",
            origin_name="서울",
            destination_query="다카마쓰",
            destination_code="TAK",
            destination_name="다카마쓰",
            departure_date="2026-07-02",
            return_date="2026-07-08",
            price_total="210000",
            currency="KRW",
            price_confirmed=False,
            source="GDS",
            validating_airlines=["NH"],
            marketing_airlines=["NH"],
            operating_airlines=["NH"],
            outbound_stops=0,
            inbound_stops=0,
            outbound_departure_at="2026-07-02T10:00:00",
            outbound_arrival_at="2026-07-02T11:30:00",
            inbound_departure_at="2026-07-08T12:00:00",
            inbound_arrival_at="2026-07-08T13:30:00",
            last_ticketing_date="2026-06-30",
        )

        grouped = group_results_by_route([result_one, result_two], limit=10)

        self.assertEqual(list(grouped.keys()), ["서울 -> 다카마쓰"])
        self.assertEqual(len(grouped["서울 -> 다카마쓰"]), 2)
        self.assertEqual(
            format_schedule_line(grouped["서울 -> 다카마쓰"][0]),
            "2026-07-01 ~ 2026-07-07 / KRW 200,000 / 진에어 (LJ) / 확정가",
        )

    def test_select_offers_for_pricing_returns_lowest_price_candidates(self):
        offers = [
            {"price": {"grandTotal": "300.00"}, "id": "3"},
            {"price": {"grandTotal": "100.00"}, "id": "1"},
            {"price": {"grandTotal": "200.00"}, "id": "2"},
        ]

        selected = select_offers_for_pricing(offers, limit=2)

        self.assertEqual([offer["id"] for offer in selected], ["1", "2"])

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
