#!/usr/bin/env bash

# Script Author: Samiullah Dilsuz
# Description: Videolar/müzikler üzerinde iki mod sunar:
#   1) Prefix ekleme
#   2) Metin kaldırma
# Version: Added custom directory option as choice 6 + fixed counters with process substitution + log + stats + color

# Renkler
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; MAGENTA='\033[0;35m'; CYAN='\033[0;36m'; RESET='\033[0m'

while true; do
  # 1) Klasör Seçimi
  echo -e "\n${CYAN}========================================${RESET}"
  echo -e "${CYAN}       Klasör Seçimi Menüsü${RESET}"
  echo -e "${CYAN}========================================${RESET}"
  echo -e "${YELLOW}1) VidMate indirilenleri işle${RESET}"
  echo -e "${YELLOW}2) SnapTube indirilenleri işle${RESET}"
  echo -e "${YELLOW}3) VidMate & SnapTube birlikte${RESET}"
  echo -e "${YELLOW}4) Telegram videolarını işle${RESET}"
  echo -e "${YELLOW}5) Tüm müzikler (Android/data & obb atla)${RESET}"
  echo -e "${YELLOW}6) Özel dizin belirt ve işle${RESET}"
  echo -e "${YELLOW}0) Çıkış${RESET}"
  read -p "Seçiminiz [0-6]: " choice
  case "$choice" in
    1) DIRS=("/storage/emulated/0/VidMate/download"); MODE_TYPE="video" ;;
    2) DIRS=("/storage/emulated/0/snaptube/download/SnapTube Video"); MODE_TYPE="video" ;;
    3) DIRS=("/storage/emulated/0/VidMate/download" "/storage/emulated/0/snaptube/download/SnapTube Video"); MODE_TYPE="video" ;;
    4) DIRS=("/storage/emulated/0/Android/media/org.telegram.messenger/Telegram/Telegram Video"); MODE_TYPE="video" ;;
    5) MODE_TYPE="music" ;;
    6) 
       read -p "Özel dizin yolunu girin: " custom_dir
       DIRS=("$custom_dir")
       MODE_TYPE="video"
       ;;
    0) echo -e "${MAGENTA}Çıkılıyor...${RESET}"; exit 0 ;;
    *) echo -e "${RED}Geçersiz seçim!${RESET}"; continue ;;
  esac

  # 2) İşlem Modu Seçimi
  echo -e "\n${CYAN}--- İşlem Modu Seçimi ---${RESET}"
  echo -e "${YELLOW}1) Prefix ekle${RESET}"
  echo -e "${YELLOW}2) Metin kaldır${RESET}"
  echo -e "${YELLOW}0) Ana Menü${RESET}"
  read -p "Seçiminiz [0-2]: " op_mode
  case "$op_mode" in
    1) MODE_OP="add" ;;
    2) MODE_OP="remove" ;;
    0) continue ;;
    *) echo -e "${RED}Geçersiz seçim!${RESET}"; continue ;;
  esac

  # 3) Kullanıcı Tercihleri
  if [[ "$MODE_OP" == "add" ]]; then
    DEFAULT_PREFIX="〖دوکان سمیع الله دلسوزょ〗"
    read -p "Özel prefix? (E/h): " pch
    if [[ $pch =~ ^[Ee]$ ]]; then
      read -p "Yeni prefix girin: " PREFIX
    else
      PREFIX="$DEFAULT_PREFIX"
    fi
    echo -e "${GREEN}Prefix: $PREFIX${RESET}"
  else
    read -p "Kaldırılacak metni girin: " text_to_remove
    [[ -z "$text_to_remove" ]] && { echo -e "${RED}Hiç metin girilmedi!${RESET}"; continue; }
    echo -e "${GREEN}Kaldırılacak Metin: '$text_to_remove'${RESET}"
  fi

  # 4) Sayaç ve log
  processed=0; skipped=0; failed=0
  LOG_FILE="process_log.txt"
  echo "Başlatma: $(date)" > "$LOG_FILE"
  echo -e "${CYAN}Log: $LOG_FILE${RESET}"

  # 5) İşlem fonksiyonu
  process_file(){
    local f="$1"; local base="$(basename "$f")"
    case "$base" in *.nomedia|*.txt|*.json)
      echo -e "${BLUE}→ Atlandı (özel dosya):${RESET} $base"
      ((skipped++)); echo "SKIP-ÖZEL: $base" >>"$LOG_FILE"; return ;;
    esac
    if [[ "$MODE_OP" == "add" ]]; then
      if [[ "$base" == "$PREFIX"* ]]; then
        echo -e "${BLUE}→ Atlandı (zaten prefix):${RESET} $base"
        ((skipped++)); echo "SKIP-PREF: $base" >>"$LOG_FILE"; return
      fi
      local new="$PREFIX$base"
      if mv -- "$f" "$(dirname "$f")/$new"; then
        echo -e "${GREEN}✓ Eklendi:${RESET} $base → $new"
        ((processed++)); echo "ADD: $base → $new" >>"$LOG_FILE"
      else
        echo -e "${RED}✗ Hata eklerken:${RESET} $base"
        ((failed++)); echo "ERR-ADD: $base" >>"$LOG_FILE"
      fi
    else
      if [[ "$base" == *"$text_to_remove"* ]]; then
        local cleaned="${base//$text_to_remove/}"
        local target="$(dirname "$f")/$cleaned"
        if [[ -z "$cleaned" || "$target" == "$f" ]]; then
          echo -e "${BLUE}→ Atlandı (geçersiz hedef):${RESET} $base"
          ((skipped++)); echo "SKIP-REM: $base" >>"$LOG_FILE"; return
        fi
        if mv -- "$f" "$target"; then
          echo -e "${GREEN}✓ Kaldırıldı:${RESET} $base → $cleaned"
          ((processed++)); echo "REM: $base → $cleaned" >>"$LOG_FILE"
        else
          echo -e "${RED}✗ Hata kaldırırken:${RESET} $base"
          ((failed++)); echo "ERR-REM: $base" >>"$LOG_FILE"
        fi
      else
        echo -e "${BLUE}→ Atlandı (metin yok):${RESET} $base"
        ((skipped++)); echo "SKIP-REM: $base" >>"$LOG_FILE"
      fi
    fi
  }

  # 6) Dosyaları işle (process substitution avoids subshell)
  if [[ "$MODE_TYPE" == "video" ]]; then
    for d in "${DIRS[@]}"; do
      echo -e "\n${CYAN}--- Tarama: $d ---${RESET}"
      while IFS= read -r -d '' file; do
        process_file "$file"
      done < <(find "$d" -maxdepth 1 -type f -print0)
    done
  else
    echo -e "\n${CYAN}--- Tüm müzikler ---${RESET}"
    while IFS= read -r -d '' file; do
      process_file "$file"
    done < <(find /storage/emulated/0 \
      -path "/storage/emulated/0/Android/data" -o -path "/storage/emulated/0/Android/obb" -prune \
      -o -type f -iname "*.mp3" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.flac" -o -iname "*.aac" -o -iname "*.ogg" -print0)
  fi

  # 7) Özet & Bekleme
  echo -e "\n${MAGENTA}========================================${RESET}"
  echo -e "${GREEN}✓ İşlenen:   $processed${RESET}"
  echo -e "${BLUE}→ Atlanan:   $skipped${RESET}"
  echo -e "${RED}✗ Hatalı:     $failed${RESET}"
  echo -e "${MAGENTA}========================================${RESET}"
  read -p $'\nAna menüye dönmek için Enter...' _
done