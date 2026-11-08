# 부산 9월 시네마틱 릴스 편집

## 스타일 1 — `edit/render.py`

레퍼런스 릴스(@rovivor, `Dew0LBIqDu2`, 41.3초)의 컷 타이밍 77개를 그대로 따라
구글 드라이브 `부산9월` 폴더 영상(DJI 4K)으로 다시 편집하는 스크립트입니다.

- 컷 위치: 레퍼런스 장면 전환 검출값(24fps 프레임 단위)
- 구성: 2프레임 플래시 인트로 → 박자 컷 → 4프레임 버스트 2회 → 3초 쉬어가는 컷 2회(바다, 시장 골목 0.8배속)
- 색감: 채도↓, 하이라이트 롤오프, 따뜻한 미드톤, 비네트, 필름 그레인
- 출력: 1920x1080, 24fps, H.264 7Mbps, 레퍼런스 원본 오디오

## 폴더 구조 (원본·결과물은 git 제외)

```
busan-reel/
  footage/   0001.mp4 … 0088.mp4, p18.jpg p19.jpg p20.jpg  (부산9월 원본)
  reel/      reel.mp4  (레퍼런스 릴스)
  edit/      render.py
```

## 실행

```
python3 edit/render.py preview    # 컷별 구도 확인용 썸네일 (edit/preview.jpg)
python3 edit/render.py segments   # 컷 74개 렌더
python3 edit/render.py final      # 합치기 + 그레인 + 오디오 → edit/busan_like_reel.mp4
```

## 스타일 2 — `edit/render2.py`

두 번째 레퍼런스 릴스(@its_danielliu, `DeUKheQiq16`, 38.0초) 스타일.

- 컷 42개, 레퍼런스 컷 타이밍 그대로 (112BPM)
- 청록 야간톤 + 블룸, 비네트, 그레인
- 자막: 필기체 "Busan" 타이틀(커지며 등장) + "2026"/"in september", "SHOT ON DJI Osmo Pocket 4",
  빨간 "BUSAN", 손글씨 "돼지국밥???", 타자 효과 "B U S A N / 35.1°N 129.0°E", "끝." → "The End..."
- 효과: 화이트 플래시, 네거티브 2프레임, 네온 휩, 펀치 줌
- 폰트: `edit/make_fonts.py`로 `fonts/`에 NanumPen.ttf, DancingScript.ttf 생성 (OFL)
- 레퍼런스 영상은 `reel2/reel.mp4`, 출력은 `edit2/busan_style2.mp4`

```
python3 edit/render2.py preview && python3 edit/render2.py segments && python3 edit/render2.py final
```
