#!/usr/bin/env bash
# vault-lib.sh — vault state detection helper
# Usage: source vault-lib.sh; STATE=$(vault_state <vault_dir>)
# Returns: existing | partial | empty | missing
#   existing — both wiki/ and _schema/ present (healthy vault)
#   partial  — only one of wiki/ or _schema/ present (incomplete init)
#   empty    — directory exists but neither subdirectory present
#   missing  — directory does not exist

vault_state() {
  local _d="$1" _w=0 _s=0
  [ -d "$_d/wiki" ]    && _w=1
  [ -d "$_d/_schema" ] && _s=1
  if   [ $_w -eq 1 ] && [ $_s -eq 1 ]; then echo "existing"
  elif [ $_w -eq 1 ] || [ $_s -eq 1 ]; then echo "partial"
  elif [ -d "$_d" ];                    then echo "empty"
  else                                       echo "missing"
  fi
}
