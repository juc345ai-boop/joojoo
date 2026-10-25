#!/usr/bin/env bash
# TiVo Stream 4K (Android TV) 기본 앱 정리 도구 — macOS용
# macOS 기본 bash(3.2)에서도 동작하도록 작성했습니다.
#
# 사용법:
#   ./tivo.sh connect <TiVo IP>        TiVo에 ADB로 연결
#   ./tivo.sh scan                     설치된 앱 목록을 packages/ 에 저장
#   ./tivo.sh apply <목록파일> [--uninstall] [--yes]
#                                      목록의 앱을 끄기(기본) 또는 제거
#   ./tivo.sh restore [백업폴더]       apply 로 바꾼 것을 되돌리기 (기본: 가장 최근)
#   ./tivo.sh enable <패키지명>        앱 하나를 다시 켜기/복구

set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_ROOT="$DIR/backups"
SCAN_DIR="$DIR/packages"

# 건드리면 부팅·홈 화면·리모컨이 망가질 수 있는 패키지. 목록에 있어도 건너뜁니다.
PROTECTED_EXACT="android com.android.systemui com.android.shell com.android.phone
com.android.tv.settings com.android.settings com.android.vending
com.google.android.gms com.google.android.gsf com.android.packageinstaller
com.google.android.packageinstaller com.android.inputdevices com.android.keychain
com.google.android.tvlauncher com.google.android.apps.tv.launcherx
com.google.android.tungsten.setupwraith com.android.permissioncontroller
com.google.android.permissioncontroller com.google.android.leanbacklauncher"
# 이 문자열이 들어간 패키지도 보호합니다 (TiVo 런처, 시스템 프로바이더, 키보드 등).
PROTECTED_PATTERNS="launcher provider inputmethod bluetooth remote setupwizard"

die() { echo "오류: $*" >&2; exit 1; }

need_adb() {
  command -v adb >/dev/null 2>&1 || die "adb 가 없습니다. 먼저 'brew install --cask android-platform-tools' 를 실행하세요."
}

need_device() {
  need_adb
  local n
  n=$(adb devices | awk 'NR>1 && $2=="device"' | wc -l | tr -d ' ')
  [ "$n" = "0" ] && die "연결된 기기가 없습니다. './tivo.sh connect <IP>' 를 먼저 실행하고 TV 화면의 허용 창을 승인하세요."
  [ "$n" != "1" ] && die "기기가 ${n}대 연결되어 있습니다. TiVo 하나만 연결해 주세요 (adb disconnect)."
}

is_protected() {
  local pkg="$1" p
  for p in $PROTECTED_EXACT; do [ "$pkg" = "$p" ] && return 0; done
  for p in $PROTECTED_PATTERNS; do
    case "$pkg" in *"$p"*) return 0 ;; esac
  done
  return 1
}

list_pkgs() { adb shell pm list packages "$@" | tr -d '\r' | sed 's/^package://' | sort; }

cmd_connect() {
  need_adb
  [ $# -ge 1 ] || die "IP 주소가 필요합니다. 예: ./tivo.sh connect 192.168.0.23"
  local addr="$1"
  case "$addr" in *:*) ;; *) addr="$addr:5555" ;; esac
  adb connect "$addr"
  echo "TV 화면에 'USB 디버깅 허용' 창이 뜨면 '항상 허용' 후 확인을 누르세요."
  echo "그 다음 ./tivo.sh scan 을 실행하세요."
}

cmd_scan() {
  need_device
  mkdir -p "$SCAN_DIR"
  list_pkgs            > "$SCAN_DIR/all.txt"
  list_pkgs -s         > "$SCAN_DIR/system.txt"
  list_pkgs -3         > "$SCAN_DIR/user-installed.txt"
  list_pkgs -d         > "$SCAN_DIR/disabled.txt"
  adb shell getprop ro.product.model  | tr -d '\r' > "$SCAN_DIR/model.txt"
  adb shell getprop ro.build.version.release | tr -d '\r' >> "$SCAN_DIR/model.txt"
  echo "저장 완료: $SCAN_DIR"
  echo "  전체 $(wc -l < "$SCAN_DIR/all.txt" | tr -d ' ')개 / 시스템 $(wc -l < "$SCAN_DIR/system.txt" | tr -d ' ')개 / 직접 설치 $(wc -l < "$SCAN_DIR/user-installed.txt" | tr -d ' ')개 / 이미 꺼짐 $(wc -l < "$SCAN_DIR/disabled.txt" | tr -d ' ')개"
  echo "packages/all.txt 내용을 Claude 에게 붙여주면 지워도 되는 앱을 분류해 줍니다."
}

cmd_apply() {
  local file="" mode="disable" yes=0 a
  for a in "$@"; do
    case "$a" in
      --uninstall) mode="uninstall" ;;
      --yes) yes=1 ;;
      -*) die "알 수 없는 옵션: $a" ;;
      *) file="$a" ;;
    esac
  done
  [ -n "$file" ] || die "목록 파일이 필요합니다. 예: ./tivo.sh apply remove-list.txt"
  [ -f "$file" ] || die "파일이 없습니다: $file"
  need_device

  local installed targets="" skipped="" missing="" pkg
  installed=$(list_pkgs)
  # 주석(#)과 빈 줄을 무시하고 한 줄에 패키지 하나씩 읽습니다.
  while IFS= read -r pkg || [ -n "$pkg" ]; do
    pkg="${pkg%%#*}"; pkg="$(echo "$pkg" | tr -d '[:space:]')"
    [ -z "$pkg" ] && continue
    if is_protected "$pkg"; then skipped="$skipped $pkg"
    elif ! echo "$installed" | grep -qx "$pkg"; then missing="$missing $pkg"
    else targets="$targets $pkg"
    fi
  done < "$file"

  [ -n "$skipped" ] && { echo "보호 대상이라 건너뜀:"; for pkg in $skipped; do echo "  - $pkg"; done; }
  [ -n "$missing" ] && { echo "설치되어 있지 않아 건너뜀:"; for pkg in $missing; do echo "  - $pkg"; done; }
  [ -n "$targets" ] || { echo "처리할 앱이 없습니다."; return 0; }

  if [ "$mode" = "uninstall" ]; then echo "다음 앱을 제거합니다 (복구 가능):"; else echo "다음 앱을 끕니다 (복구 가능):"; fi
  for pkg in $targets; do echo "  * $pkg"; done
  if [ "$yes" != "1" ]; then
    printf "진행할까요? [y/N] "
    read -r a
    case "$a" in y|Y|yes) ;; *) echo "취소했습니다."; return 0 ;; esac
  fi

  local bdir out ok=0 fail=0
  bdir="$BACKUP_ROOT/$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$bdir"
  echo "$installed" > "$bdir/packages-before.txt"
  list_pkgs -d > "$bdir/disabled-before.txt"
  for pkg in $targets; do
    if [ "$mode" = "uninstall" ]; then
      out=$(adb shell pm uninstall -k --user 0 "$pkg" 2>&1 | tr -d '\r')
    else
      out=$(adb shell pm disable-user --user 0 "$pkg" 2>&1 | tr -d '\r')
    fi
    case "$out" in
      *Success*|*"new state: disabled-user"*)
        echo "$mode $pkg" >> "$bdir/actions.log"; ok=$((ok+1)); echo "  ✓ $pkg" ;;
      *)
        fail=$((fail+1)); echo "  ✗ $pkg — $out" ;;
    esac
  done
  echo "완료: 성공 ${ok}개, 실패 ${fail}개. 기록: $bdir"
  echo "문제가 생기면 './tivo.sh restore' 로 되돌릴 수 있습니다. 변경을 확인하려면 TiVo 를 재부팅하세요."
}

restore_one() {
  local pkg="$1" out
  # 제거된 앱은 다시 설치하고, 꺼진 앱은 켭니다. 둘 다 시도해도 해가 없습니다.
  adb shell cmd package install-existing --user 0 "$pkg" >/dev/null 2>&1
  out=$(adb shell pm enable --user 0 "$pkg" 2>&1 | tr -d '\r')
  case "$out" in
    *"new state: enabled"*) echo "  ✓ $pkg" ;;
    *) echo "  ✗ $pkg — $out" ;;
  esac
}

cmd_restore() {
  need_device
  local bdir="${1:-}"
  if [ -z "$bdir" ]; then
    bdir=$(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | sort | tail -1)
    [ -n "$bdir" ] || die "백업이 없습니다."
  fi
  [ -f "$bdir/actions.log" ] || die "되돌릴 기록이 없습니다: $bdir"
  echo "되돌리는 중: $bdir"
  local mode pkg
  while read -r mode pkg; do
    [ -n "$pkg" ] && restore_one "$pkg"
  done < "$bdir/actions.log"
  echo "완료. TiVo 를 재부팅하세요."
}

cmd_enable() {
  [ $# -ge 1 ] || die "패키지명이 필요합니다."
  need_device
  restore_one "$1"
}

case "${1:-}" in
  connect) shift; cmd_connect "$@" ;;
  scan)    shift; cmd_scan ;;
  apply)   shift; cmd_apply "$@" ;;
  restore) shift; cmd_restore "$@" ;;
  enable)  shift; cmd_enable "$@" ;;
  *) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//' ;;
esac
