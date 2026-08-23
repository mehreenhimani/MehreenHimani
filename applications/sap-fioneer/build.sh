#!/usr/bin/env bash
# Render the CV and cover letter to PDF and DOCX.
#
#   ./build.sh                      -> public build, no phone number
#   ./build.sh "+49 XXX XXXX XXX"  -> private build with the number injected,
#                                      written to *_with_phone.* (git-ignored)
#
# The phone number is deliberately NOT stored in this repo. Pass it as an
# argument when you want the copies you actually send to recruiters.
set -euo pipefail
cd "$(dirname "$0")"

CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome
CV_PDF="Mehreen_Himani_CV_SAP_Fioneer_Senior_Solution_Manager"
CL_PDF="Mehreen_Himani_Cover_Letter_SAP_Fioneer"

render() { "$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
             --print-to-pdf="$2" "file://$PWD/$1" 2>/dev/null; }

if [ $# -ge 1 ] && [ -n "$1" ]; then
  PHONE="$1"
  TEL="tel:$(printf '%s' "$PHONE" | tr -cd '+0-9')"
  python3 - "$PHONE" "$TEL" <<'PY'
import sys
phone, tel = sys.argv[1], sys.argv[2]
link = f'<a href="{tel}">{phone}</a> <span class="sep">|</span>'
for src, dst in (("cv.html", ".cv.phone.html"), ("cover_letter.html", ".cl.phone.html")):
    s = open(src, encoding="utf-8").read()
    s = s.replace("<!--PHONE-->", link).replace("<!--PHONESIG-->", f" · {phone}")
    open(dst, "w", encoding="utf-8").write(s)
PY
  render .cv.phone.html "${CV_PDF}_with_phone.pdf"
  render .cl.phone.html "${CL_PDF}_with_phone.pdf"
  python3 make_docx.py .cv.phone.html "${CV_PDF}_with_phone.docx" \
                       .cl.phone.html "${CL_PDF}_with_phone.docx"
  rm -f .cv.phone.html .cl.phone.html
  echo "built WITH phone: ${CV_PDF}_with_phone.{pdf,docx} ${CL_PDF}_with_phone.{pdf,docx}"
else
  render cv.html "${CV_PDF}.pdf"
  render cover_letter.html "${CL_PDF}.pdf"
  python3 make_docx.py
  echo "built without phone: ${CV_PDF}.{pdf,docx} ${CL_PDF}.{pdf,docx}"
fi
