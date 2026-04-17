```bash
curl 'https://www.skyscanner.co.kr/g/radar/api/v2/web-unified-search/' \
  -H 'accept: application/json' \
  -H 'accept-language: en-US,en;q=0.9,ko-KR;q=0.8,ko;q=0.7' \
  -H 'content-type: application/json' \
  -b 'traveller_context=134e0fab-4a74-484a-b8a4-544799a7bc1a; __Secure-anon_token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6ImM3ZGZlYjI2LTlmZjUtNDY4OC1iYjc3LWRiNTY2NWUyNjFkZSJ9.eyJhenAiOiIyNWM3MGZmZDAwN2JkOGQzODM3NyIsImh0dHBzOi8vc2t5c2Nhbm5lci5uZXQvbG9naW5UeXBlIjoiYW5vbnltb3VzIiwiaHR0cHM6Ly9za3lzY2FubmVyLm5ldC91dGlkIjoiMTM0ZTBmYWItNGE3NC00ODRhLWI4YTQtNTQ0Nzk5YTdiYzFhIiwiaHR0cHM6Ly9za3lzY2FubmVyLm5ldC9jc3JmIjoiYjNlNGFlMDhiMzk3Y2Q1MGUwNWZiZDU3ZGU0YzVjYzgiLCJodHRwczovL3NreXNjYW5uZXIubmV0L2p0aSI6Ijk5NjA5ZTBjLTU3OTQtNDAxMC05MTAyLTAxNGRmOTEzMzQxMSIsImlhdCI6MTc2NjY0MDQzNCwiZXhwIjoxODI5NzEyNDM0LCJhdWQiOiJodHRwczovL2dhdGV3YXkuc2t5c2Nhbm5lci5uZXQvaWRlbnRpdHkiLCJpc3MiOiJodHRwczovL3d3dy5za3lzY2FubmVyLm5ldC9zdHRjL2lkZW50aXR5L2p3a3MvcHJvZC8ifQ.RaayPO1uQlCCYQYyzRqlzvxmI1J-coVMteSILiH1x0ImD-mDGOfgsKBNOLHQYryj6ExdwPC9Qh2EhgsFCVvlbBStLDxdMFTCFJZUd5lmuSrh2YdFf9yC-XBIFouKGo2XknNuZ-sfDPh1ANrrWCZA9nua6KHTqzH17pIyorp6JPKth5QOSSHvAV3zaVqFFjcaI1g5qfTDz76HiJ0QihlRabDowFzINWJ1yOxBu9wlCqMxfwRjTxWSimj7evvqtPFO6JSTNb70IAuIana_Kud3PScI1S4wCZ4-i_WguhRMLTtoreQr0qAFdiTNyow-SUDeZxplR1n13by9AVKR7z3lNg; __Secure-anon_csrf_token=b3e4ae08b397cd50e05fbd57de4c5cc8; ssculture=locale:::ko-KR&market:::KR&currency:::KRW; __Secure-ska=a1d407bd-2fe2-4e0f-9747-223e362ee5a1; device_guid=a1d407bd-2fe2-4e0f-9747-223e362ee5a1; _pxvid=5f00bed6-e152-11f0-b5bf-a1fe6c85d1cf; _ga=GA1.1.330212516.1766640436; FPID=FPID2.3.OHbamA5se2ucLyfhBJ4CJhVweajJtbvTwGwxSfxGXZs%3D.1766640436; _fbp=fb.2.1766640435852.1158137013; preferences=134e0fab4a74484ab8a4544799a7bc1a; _pxhd=Y4khMgxkarBvC1wpdYLtXXAzmk/KmqP7gw/rtlkYIvfDa46siNkzDWx0dj4z9NckL-M-8JAGBLlXOxQkTNM93w==:3ARTPQ3Qx/NQINx66iQl-CG/fA7Ccd2pmJtd8em5qe-HeUN2yRO4WL7WZ-7oUk0TyeJCuZQ32z3Wiv2rPeuUCpWjYHEobCQVwEA6Kg1LS-k=; ssaboverrides=; abgroup=74349880; pxcts=f5142fe2-2cec-11f1-986d-90839068b73c; _gcl_gs=2.1.k1$i1774953165$u188590762; _gcl_au=1.1.1503119254.1774953167; FPGCLAW=2.1.kCj0KCQjwm6POBhCrARIsAIG58CKQrE2XJK7SW4n0mRH-LNbnxZRtviLJs2GhX-jWA1OFd3N47oC4xAMaAsCHEALw_wcB$i1774953167; FPGCLDC=2.1.kCj0KCQjwm6POBhCrARIsAIG58CKQrE2XJK7SW4n0mRH-LNbnxZRtviLJs2GhX-jWA1OFd3N47oC4xAMaAsCHEALw_wcB$i1774953167; FPGCLGS=2.1.k1$i1774953165$u188590762; FPAU=1.1.1503119254.1774953167; FPLC=W%2BUYAtI9NnH3w2HxATQx%2BuFr41FJK1SYQPxAhtCMqy7WpVC%2BFOP3WNt0wpao5t0Ioi%2FnYQYrTCDg%2FDOxXTr7YtZl8KdwFVQUxmF5hc7P2Ug%2BaQxTfRvPcX%2FNDSD8Mg%3D%3D; QSI_S_ZN_0VDsL2Wl8ZAlxlA=v:0:0; Lda_aKUr6BGRn=duertry.com/r/v2?; Lda_aKUr6BGRr=0; Fm_kZf8ZQvmX=1; Ac_aqK8DtrDS=1; X-Gateway-Servedby=gw54.skyscanner.net; QSI_S_ZN_8fcHUNchqVNRM4S=v:0:0; __Secure-session_id=eyJhbGciOiJSUzI1NiIsImtpZCI6InNlc3Npb24tc2VydmljZS1rZXktMjAyNi0wMyIsInR5cCI6IkpXVCJ9.eyJzaWQiOiIwMTlkNDM3My1mMjUzLTgwMDQtYmFlMC1hY2M0NzI5NGU3M2QiLCJjcnQiOjE3NzQ5NTMxNjUsImV4cCI6MTc3NDk1NTAyOCwiaWF0IjoxNzc0OTUzMjI4fQ.yX2dDnrS2amuwNyPOnBQmga8x0WKeOE2evUTKYd1PzF7MS3LeqAwm2_CRGfC3QGp56FKN32ZTr0sLWtighVvs8SqbNMEBDy8_TL1-hLRfcz0KCHmFX5AGYLXLh1ds215WzG8o6tnO2YRQ-S3G50DXDcF6aN3_0bCy4VSALOmCN56XbX2YwLwb8AsEtpB7QXZ6AKUr2JViaWdSS1Fz3eUAOIOgV-USQuHTi75xz4PB0WnpA_0u-XP7hL3RcowswZe-3OnNmBUZsokYbtLj93aDLndVVDyr9Fzd9h7McoxwnQ5QPDKkoSKq_wMcFnXqgInyjAeWZ9lggLXlcmWEWkDVw; FPGSID=1.1774953167.1774953230.G-XEEM7L2YCB.5K9UmxKkIIDXQ93IGDm6tg; _gcl_aw=GCL.1774953233.Cj0KCQjwm6POBhCrARIsAIG58CKQrE2XJK7SW4n0mRH-LNbnxZRtviLJs2GhX-jWA1OFd3N47oC4xAMaAsCHEALw_wcB; _gcl_dc=GCL.1774953233.Cj0KCQjwm6POBhCrARIsAIG58CKQrE2XJK7SW4n0mRH-LNbnxZRtviLJs2GhX-jWA1OFd3N47oC4xAMaAsCHEALw_wcB; _px3=07ac42fc3dc54f810b8bf764726c56e36954b5227ea3f1a7a739352adcbdc7c4:OvgbRKHpHiYfkhBZziRLs+XakdJRIEWhwQBGYi52X1ag8MIBVehoirfj4P7NApvxZc92wifZgyWC4OQwYPpuZQ==:1000:u1f2aMAdXUmuRr4mXO1oa8biHxT/oHEuziFvRCNus/gu/7adjF8h/vI0r8WxQL46YimbjGJKtuOzi4mPY8MHBqArC3bTyjV3aEiHJ0eLMmnWneVUUgAMkuNGq3WEUw0x4/vlKI2EU8RMQb1gz2mgKn7c4hIPvLtEkc7O5/l5pXtl7UejWQTfU0JW/EvdkaMdD6/UMVr+3seTSCaCeVzDVUORvX1+a/xjpXA3uzWaGAQlXCeKy3z07cfLlKvJ8AbhEeUpYUnSQp5ITaC1gV7ZymvRjs0GC/wicoDmqu3tTeXtP3qWQ3Av0gTUpeVPRIC8GG8blf6Z+5EmgLSti/79i1iQtSx4n5uGmEGFyQV3SWj8+G3/YEfMh7K2IiEDGaJksluDtjH73IkAAYcm5HqVVwgVOLbWyeGYEYebOSnPlS3qJvtZiJisJEMUHLLWCvDeN8o/vvQAnsfyxTBWZbF0YWS0ifBpmLMqwa/YY6CddK+tzS/FN/YFCbegvEhmOR9AfHQkYqMPTz5ZY7IxdE911UhA8p9EfXCZE2hToSlP6nY=; g_state={"i_l":0,"i_ll":1774953251955,"i_b":"CwfOPSFDI6NbyAhPAURi1hhhyZR7ZTX7K6vZak3NUZA","i_e":{"enable_itp_optimization":1}}; cto_bundle=P_5Ed19mYmxGS3pIZFd4UW9BWEZJS1pQV3ZLYmhscUkwb01WNVJsTm5VaU9LMFhETmI5UFJiWGlQSm9kS0w3N2dYS2gwNUtlRnlLRjY1Y25RbmdqRCUyRlczdTJDN2olMkYwZVdUS1RvRW92c01EZ3glMkJNN1VOJTJCS2ZBb3VvMFppb0pFRGdrRnBCQ0YyMDlSV3ZzQ0VISnIwQUtsY1BqN0xNODlYdzlTYlJZN1JETm9kNEljSjJrelVBcXZiQVU5blZDblJTOXpPJTJCa1VJUDNFdDdMZ241V0p0SmwlMkJGSXd3JTNEJTNE; cto_bidid=z427519TJTJGN3Q2NzBXTXppRWlUbWRZaFpxUlU2SFNNNSUyQnlVUGdaTTdBOFVJemd5eUNPb2tGeUlDOHpBM2xNTGxESWhEUGtsZWx1Z1MzU0lJTGU0UmhOQ1J0TSUyRm5RQjMlMkJSRnplWXVyVmI5TzJXT3clMkZuUUdSTmlReE1HQ1dXaVpVc1IxbHNwaXhtdUdTbTdtU1E3azJzQktIZk5RJTNEJTNE; jha=CAISeQiTxa7OBhIINzQzNDk4ODAYt8auzgYgACoCS1IyBWtvLUtSOABCA0tSV1IHdW5rbm93bloXZmxpZ2h0cy1kYXktdmlldy1yZXR1cm5gAWgAcAB4AIABAIgBAJIBBWNvLmtymgEUd3d3LnNreXNjYW5uZXIuY28ua3I=; experiment_allocation_id=8581e63128b489d7a16cab347210f0e68e063b2e449dc258479be91fcf44ba2f; _ga_XEEM7L2YCB=GS2.1.s1774953166$o4$g1$t1774953272$j17$l0$h299317886' \
  -H 'origin: https://www.skyscanner.co.kr' \
  -H 'priority: u=1, i' \
  -H 'referer: https://www.skyscanner.co.kr/transport/flights/sela/kix/260701/260707/?adultsv2=1&cabinclass=economy&childrenv2=&ref=home&rtn=1&preferdirects=false&outboundaltsenabled=false&inboundaltsenabled=false' \
  -H 'sec-ch-ua: "Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-model: ""' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36' \
  -H 'x-skyscanner-ads-sponsored-view-type: ADS_SPONSORED_VIEW_DAY_VIEW' \
  -H 'x-skyscanner-channelid: website' \
  -H 'x-skyscanner-combined-results-rail: true' \
  -H 'x-skyscanner-consent-adverts: true' \
  -H 'x-skyscanner-currency: KRW' \
  -H 'x-skyscanner-locale: ko-KR' \
  -H 'x-skyscanner-market: KR' \
  -H 'x-skyscanner-skip-accommodation-carhire: true' \
  -H 'x-skyscanner-traveller-context: 134e0fab-4a74-484a-b8a4-544799a7bc1a' \
  -H 'x-skyscanner-trustedfunnelid: abdc18de-807f-4b3b-ad00-7585466d822d' \
  -H 'x-skyscanner-viewid: abdc18de-807f-4b3b-ad00-7585466d822d' \
  --data-raw '{"cabinClass":"ECONOMY","childAges":[],"adults":1,"legs":[{"legOrigin":{"@type":"entity","entityId":"27538638"},"legDestination":{"@type":"entity","entityId":"128667802"},"dates":{"@type":"date","year":"2026","month":"07","day":"01"},"placeOfStay":"27542908"},{"legOrigin":{"@type":"entity","entityId":"128667802"},"legDestination":{"@type":"entity","entityId":"27538638"},"dates":{"@type":"date","year":"2026","month":"07","day":"07"}}]}'
```

## 구분 | #1 | #2 | #3 | #4

일정 | 06-22~06-25 | 06-21~06-24 | 06-28~07-01 | 07-05~07-08
최저가 | W258,700 | W265,600 | W265,600 | W265,600
시간 | 08:00/11:35 | 07:10/16:30 | 07:10/11:00 | 08:10/09:00
항공사 | TW | 7C | 7C | 7C

| no. | 일정       | 최저가   | 시간        | 항공사 |
| --- | ---------- | -------- | ----------- | ------ |
| 1   | 06/22 ~ 25 | W258,700 | 08:00/11:35 | TW     |
