#!/usr/bin/env bash
# Runs on the Ubuntu demo server via SSH; Docker and Compose are already installed.
set -euo pipefail

deploy_dir=${1:?Deployment directory required}
export IMAGE_REF=${2:?Published image digest required}
project_name=${3:?Compose project name required}

cd "$deploy_dir"
mkdir -p tasks
# Match the non-root app user, including files created during manual deployment.
chown -R 10001:10001 tasks

compose=(docker compose --project-name "$project_name" -f compose.deploy.yaml)
# Download successfully before replacing the existing app container.
"${compose[@]}" pull app
"${compose[@]}" up -d --no-build --pull never app

for attempt in {1..30}; do
  if curl --fail --silent --max-time 3 http://127.0.0.1:5151/ > /dev/null; then
    echo "Staging responds on port 5151. Image: $IMAGE_REF"
    "${compose[@]}" ps
    exit 0
  fi
  sleep 2
done

echo "Staging failed its HTTP check." >&2
"${compose[@]}" logs --tail 50 app
exit 1
