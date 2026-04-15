#!/usr/bin/env bash
# validate-vault.sh — Check vault directory status for setup skill.
set -euo pipefail
# Usage: bash validate-vault.sh <vault_path>
# Output (two lines):
#   VAULT_STATUS=existing|partial|needs_init|not_found
#   NEED_INIT=0|1

[ $# -ge 1 ] || { echo "Usage: bash validate-vault.sh <vault_path>" >&2; exit 2; }
_dir="${1/#\~/$HOME}"

source "$(dirname "$0")/vault-lib.sh"
case "$(vault_state "$_dir")" in
  existing) printf 'VAULT_STATUS=existing\nNEED_INIT=0\n' ;;
  partial)  printf 'VAULT_STATUS=partial\nNEED_INIT=1\n' ;;
  empty)    printf 'VAULT_STATUS=needs_init\nNEED_INIT=1\n' ;;
  missing)  printf 'VAULT_STATUS=not_found\nNEED_INIT=1\n' ;;
esac
