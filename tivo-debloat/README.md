# TiVo Stream 4K 기본 앱 정리 (macOS)

ADB로 TiVo Stream 4K(Android TV)의 쓸데없는 기본 앱을 **끄거나 제거**합니다.
루팅이 필요 없고, 모든 변경은 되돌릴 수 있습니다.

## 1. 준비 (처음 한 번)

1. **Mac에 adb 설치**
   ```sh
   brew install --cask android-platform-tools
   ```
   Homebrew가 없다면 https://brew.sh 에서 먼저 설치하세요.

2. **TiVo 개발자 모드 켜기**
   - 설정 → 기기 환경설정 → 정보 → **빌드**를 7번 누르기
   - 설정 → 기기 환경설정 → 개발자 옵션 → **USB 디버깅** 켜기

3. **TiVo IP 주소 확인**
   - 설정 → 네트워크 및 인터넷 → 연결된 와이파이 → IP 주소
   - Mac과 TiVo는 같은 와이파이에 있어야 합니다.

## 2. 사용법

```sh
cd tivo-debloat
./tivo.sh connect 192.168.0.23   # TiVo IP. TV에 뜨는 허용 창 승인
./tivo.sh scan                   # 설치된 앱 목록을 packages/ 에 저장
```

`packages/all.txt` 내용을 Claude에게 붙여주면, 지워도 되는 앱을 골라
`remove-list.txt`를 채워 줍니다. 그 다음:

```sh
./tivo.sh apply remove-list.txt              # 끄기 (권장, 가장 안전)
./tivo.sh apply remove-list.txt --uninstall  # 제거 (저장공간 일부 확보)
```

실행 전에 대상 목록을 보여주고 확인을 받습니다. 끝나면 TiVo를 재부팅하세요.

## 3. 되돌리기

```sh
./tivo.sh restore                      # 가장 최근 변경 전체 되돌리기
./tivo.sh restore backups/20261025-1530  # 특정 시점 되돌리기
./tivo.sh enable <패키지명>            # 앱 하나만 복구
```

그래도 문제가 있으면 설정 → 기기 환경설정 → 초기화(공장 초기화)로
완전히 원래대로 돌아갑니다.

## 안전장치

- 홈 화면(런처), 설정, 구글 플레이 서비스, 키보드, 블루투스/리모컨 관련
  패키지는 목록에 있어도 **자동으로 건너뜁니다** (`tivo.sh`의 `PROTECTED_*`).
- `--user 0` 방식이라 시스템 이미지는 그대로입니다. 공장 초기화하면 전부 복원됩니다.
- 매 실행마다 `backups/<시각>/`에 이전 상태와 변경 기록을 남깁니다.
