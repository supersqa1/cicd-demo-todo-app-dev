#!/usr/bin/env bash
# Runs on the GitHub runner. Connection settings come from the selected deployment environment.
set -euo pipefail

: "${SSH_KEY:?Missing SSH_KEY input}"
: "${SERVER_HOST:?Missing SERVER_HOST input}"
: "${SERVER_USER:?Missing SERVER_USER input}"
: "${KNOWN_HOSTS:?Missing verified KNOWN_HOSTS input}"
: "${IMAGE_REF:?Missing published image reference}"

ssh_dir=$(mktemp -d)
trap 'rm -rf "$ssh_dir"' EXIT
printf '%s\n' "$SSH_KEY" > "$ssh_dir/key"
printf '%s\n' "$KNOWN_HOSTS" > "$ssh_dir/known_hosts"
chmod 600 "$ssh_dir/key" "$ssh_dir/known_hosts"
unset SSH_KEY
ssh_options=(-i "$ssh_dir/key" -o BatchMode=yes -o IdentitiesOnly=yes
  -o StrictHostKeyChecking=yes -o "UserKnownHostsFile=$ssh_dir/known_hosts"
  -o ConnectTimeout=15)
target="$SERVER_USER@$SERVER_HOST"

printf -v prepare_command 'mkdir -p %q' "$DEPLOY_DIR"
ssh "${ssh_options[@]}" "$target" "$prepare_command"
scp "${ssh_options[@]}" compose.deploy.yaml "$target:$DEPLOY_DIR/compose.deploy.yaml"
printf -v deploy_command 'bash -s -- %q %q %q' "$DEPLOY_DIR" "$IMAGE_REF" "$PROJECT_NAME"
ssh "${ssh_options[@]}" "$target" "$deploy_command" < scripts/deploy.sh

