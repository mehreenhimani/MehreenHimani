#!/usr/bin/env bash
# Build the Word versions of the architecture and interview documents.
#
# The markdown files are the source of truth — edit those, then run this. The
# reference document carries the styling; docx-postprocess.py fixes the two things
# pandoc cannot do well (header-row shading that LibreOffice honours, and column
# widths proportioned to the text rather than to the markdown source).
set -euo pipefail

# pandoc reads metadata as UTF-8 only if the locale says so; under POSIX every
# em dash becomes a replacement character.
export LANG=C.UTF-8 LC_ALL=C.UTF-8

cd "$(dirname "$0")/.."
REF=docs/.pandoc-reference.docx

build() {
  local src=$1 out=$2 title=$3 subtitle=$4
  local meta; meta=$(mktemp /tmp/meta-XXXX.yaml)
  cat > "$meta" <<YAML
---
title: "$title"
subtitle: "$subtitle"
author: "Mehreen Himani"
lang: en-GB
---
YAML
  pandoc "$meta" "$src" -f gfm+yaml_metadata_block -t docx \
    --reference-doc="$REF" -o "$out"
  rm -f "$meta"
  echo "  built $out"
}

build docs/INTERVIEW-QA.md docs/Redcare-Interview-QA.docx \
  "Technical Round — Questions & Answers" \
  "Product Manager, Agentic AI Platform · Redcare Pharmacy"

build docs/ARCHITECTURE.md docs/Redcare-Architecture.docx \
  "Architecture — Redcare Agentic AI Platform" \
  "How a customer question becomes a safe, grounded, observable, affordable answer"

python3 scripts/docx-postprocess.py docs/Redcare-Interview-QA.docx docs/Redcare-Architecture.docx
echo "Done."
