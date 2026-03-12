#!/usr/bin/env bash
set -euo pipefail

env_file="${1:-deploy/.env.production}"
compose_file="${2:-docker-compose.server.yml}"

resolve_compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return 0
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return 0
  fi

  echo ""
}

compose_runner="$(resolve_compose_cmd)"

export_compose_env() {
  local env_source="$1"
  while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
    raw_line="${raw_line%$'\r'}"
    [[ -z "${raw_line}" || "${raw_line}" =~ ^[[:space:]]*# ]] && continue
    [[ "${raw_line}" != *=* ]] && continue
    export "${raw_line}"
  done <"${env_source}"
}

prepare_legacy_env() {
  local env_source="$1"
  local compose_target="$2"

  legacy_compose_dir="$(cd "$(dirname "${compose_target}")" && pwd)"
  legacy_env_path="${legacy_compose_dir}/.env"
  legacy_env_backup=""

  if [[ -e "${legacy_env_path}" && ! -L "${legacy_env_path}" ]]; then
    legacy_env_backup="${legacy_env_path}.bak.$(date +%s)"
    mv "${legacy_env_path}" "${legacy_env_backup}"
  elif [[ -L "${legacy_env_path}" ]]; then
    rm -f "${legacy_env_path}"
  fi

  ln -s "$(realpath "${env_file}")" "${legacy_env_path}"
}

cleanup_legacy_env() {
  if [[ -n "${legacy_env_path:-}" ]]; then
    rm -f "${legacy_env_path}"
  fi

  if [[ -n "${legacy_env_backup:-}" && -f "${legacy_env_backup}" ]]; then
    mv "${legacy_env_backup}" "${legacy_env_path}"
  fi
}

echo "== system =="
uname -a
cat /etc/os-release
echo

echo "== resources =="
free -h
df -h
swapon --show || true
echo

echo "== runtime =="
docker --version
if [[ -n "${compose_runner}" ]]; then
  if [[ "${compose_runner}" == "docker compose" ]]; then
    docker compose version
  else
    docker-compose version
  fi
else
  echo "docker compose not available"
fi
systemctl is-active docker || true
echo

echo "== listening ports =="
ss -tulpn
echo

if [[ -f "${env_file}" ]]; then
  export_compose_env "${env_file}"
  echo "== compose config =="
  if [[ "${compose_runner}" == "docker compose" ]]; then
    docker compose --env-file "${env_file}" -f "${compose_file}" config >/dev/null
    echo "compose config ok"
  elif [[ "${compose_runner}" == "docker-compose" ]]; then
    prepare_legacy_env "${env_file}" "${compose_file}"
    trap cleanup_legacy_env EXIT
    docker-compose -f "${compose_file}" config >/dev/null
    echo "compose config ok"
  else
    echo "compose config skipped: docker compose not available"
  fi
  echo
fi

echo "== health check =="
curl -fsS http://127.0.0.1:8001/api/health/ || true
