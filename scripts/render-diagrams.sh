#!/usr/bin/env bash

set -euo pipefail

readonly D2_VERSION="v0.7.1"
readonly SOURCE_DIRECTORY="docs/diagrams"
readonly DOCUMENTATION_OUTPUT_DIRECTORY="docs/diagrams/rendered"
readonly SITE_OUTPUT_DIRECTORY="site/public/diagrams"

if [[ -n "${D2_BIN:-}" ]]; then
  d2_command=("${D2_BIN}")
elif command -v d2 >/dev/null 2>&1; then
  d2_command=(d2)
else
  echo "D2 ${D2_VERSION} is required. Install it from https://d2lang.com/tour/install/ or set D2_BIN." >&2
  exit 1
fi

installed_version="$("${d2_command[@]}" --version)"
if [[ "${installed_version}" != "${D2_VERSION}" ]]; then
  echo "Expected D2 ${D2_VERSION}; found ${installed_version}. Set D2_BIN to the pinned binary." >&2
  exit 1
fi

mkdir -p "${DOCUMENTATION_OUTPUT_DIRECTORY}" "${SITE_OUTPUT_DIRECTORY}"

for source in "${SOURCE_DIRECTORY}"/*.d2; do
  name="$(basename "${source}" .d2)"
  # --salt pins the generated CSS scope id. Without it D2 picks a random id per
  # run, so every render churns the whole file and the CI drift check below can
  # never pass. Salting per diagram also keeps ids unique when several diagrams
  # are embedded in one page.
  "${d2_command[@]}" "${source}" "${DOCUMENTATION_OUTPUT_DIRECTORY}/${name}.svg" --layout elk --theme 6 --dark-theme 200 --salt "${name}"
  cp "${DOCUMENTATION_OUTPUT_DIRECTORY}/${name}.svg" "${SITE_OUTPUT_DIRECTORY}/${name}.svg"
done

echo "Rendered D2 diagrams with ${installed_version}."
