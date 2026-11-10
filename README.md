# CI/CD Demo To-Do App

A small Dockerized Flask app for the SuperSQA CI/CD tutorial series. Create, view, update, and delete tasks while learning how to build a deployment pipeline. This rehearsal repo contains a CI/CD workflow under construction and a small regression suite. The public template stays at the starter stage.

## Start your own repository

1. Click **Use this template → Create a new repository** on GitHub.
2. Choose your repository name and owner.
3. Clone **your new repository** and open its directory in a terminal.

## Project structure

```text
app/
  main.py             # Flask routes and file-based task storage
  templates/          # HTML pages rendered by Flask
  requirements.txt    # Python dependencies
  __init__.py         # Python package marker
Dockerfile            # Application image
compose.yaml          # Local container and tasks/ bind mount
.dockerignore         # Files excluded from the image build
.gitignore            # Files excluded from Git
README.md
```

`app/templates/` contains the app's HTML pages. It is unrelated to GitHub's repository template feature.

## Run with Docker (recommended)

Install Docker with Compose (included in Docker Desktop). From the repository root:

```bash
mkdir -p tasks
docker compose up --build -d
```

On native Linux (including our Ubuntu server), set the container user to your host user before starting it, so both Docker and your editor can write task files:

```bash
mkdir -p tasks
export LOCAL_UID=$(id -u) LOCAL_GID=$(id -g)
docker compose up --build -d
```

Run those exports in each new Linux terminal used for Compose, as your regular user (not root). Docker Desktop on Mac/Windows uses the default non-root container user; the exports are not needed there.

Open http://localhost:5151 locally, or `http://SERVER_IP:5151/` on a remote server. Docker publishes port 5151 on all host interfaces; remote access also requires inbound TCP 5151 to be allowed by the server/cloud firewall. HTTPS is not configured.

```bash
docker compose logs -f   # View logs; Ctrl+C stops following logs
docker compose down     # Stop and remove containers; keep task data
```

Tasks are saved as text files in your project's `tasks/` folder, bind-mounted at `/app/tasks` inside the container. Create a task in the browser and its file appears in VS Code. Git ignores these files. They survive container replacement and even `docker compose down --volumes`; deleting files from `tasks/` deletes the data.

If you previously used the named-volume version, its existing tasks stay in that old volume. This setup starts with the contents of `./tasks`; it does not migrate old data automatically.

## Run without Docker

Use Python 3.12 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirements.txt
python -m app.main
```

On Windows, use `py -3.12 -m venv .venv` and activate with `.venv\Scripts\activate.bat` in Command Prompt. Open http://localhost:5151; stop with Ctrl+C. Local task files use the same `tasks/` folder as Docker. Run only one app instance against that folder at a time.

## ARM64 and AMD64 builds

By default, Docker builds for the architecture of the Docker host (unless you explicitly select another platform):

- Apple Silicon with local Docker Desktop: **ARM64**.
- Intel/AMD machines and our Vultr x64 server: **AMD64**.

The same source code and Dockerfile work on both. When we copy the source to Vultr and build there, Docker produces AMD64 automatically. Copying an already-built ARM64 image to an AMD64 server is different; it needs a matching image or emulation.

From the repository root, build for the current Docker host and then start the app:

```bash
docker compose build
docker compose up -d
```

Or combine both steps with `docker compose up --build -d`.

To explicitly build either platform with a compatible Buildx builder (cross-platform builds require builder support such as Docker Desktop's emulation):

```bash
docker buildx build --platform linux/arm64 -t cicd-demo-todo-app:arm64 --load .
docker buildx build --platform linux/amd64 -t cicd-demo-todo-app:amd64 --load .
```

## Pipeline: checks, image publishing, and staging

`.github/workflows/cicd.yaml` runs on pushes to any branch during rehearsal. It currently:

- Runs real Ruff linting: syntax/selected correctness errors block the pipeline; style findings are reported without blocking.
- Runs real unit and integration tests in separate jobs; failures block image publishing. Each job uploads HTML/JUnit reports.
- Builds AMD64 and ARM64 images and pushes to `ghcr.io/<owner>/<repo>:<full-commit-sha>` after all three initial jobs pass.
- Authenticates automatically using `GITHUB_TOKEN` with `packages: write`; no custom secrets needed.
- Outputs the full image tag, digest, and digest-based reference for later deployment. The published image details appear in the job summary.

The staging job deploys on `main` and the current `feat/pipeline-skeleton-and-regression` rehearsal branch. Other branches only run checks and publishing. Before recording the final workflow, remove the rehearsal branch exception and add PR checks. Workflow runs are serialized so another deployment cannot replace staging while regression tests are running.

After staging succeeds, **Automation / Regression** installs Chromium and runs `tests/regression` headlessly against the staging URL. Failures block the later approval/production jobs. The upload step uses `if: always()` so reports and any failure screenshots/traces are retained even when tests fail. Download the `staging-regression` artifact from the Actions run; report artifacts are kept for 7 days. The browser job uses Ubuntu 24.04 for Playwright system dependency support.

Approval, production, and production smoke-check jobs remain placeholders. Unit, integration, and regression tests are now real. The public template includes all three suites so recording can focus on connecting them to the pipeline.

### Staging setup

Use a public GHCR package so the server can pull without registry credentials. New packages default to private; change package visibility separately after the first push.

In **Settings → Environments → staging**, configure:

| Type | Name | Value |
| --- | --- | --- |
| Secret | `STAGING_SSH_KEY` | Dedicated deployment private key |
| Variable | `STAGING_HOST` | Server IP or hostname |
| Variable | `STAGING_USER` | `root` for this disposable demo |
| Variable | `STAGING_KNOWN_HOSTS` | Verified OpenSSH known_hosts entry for the server |

Install the matching public key in the server user's `~/.ssh/authorized_keys`. Obtain the server's public host key through a trusted connection or provider console; do not disable host-key checking. For an Ed25519 host key, the known_hosts entry has the form `SERVER_IP ssh-ed25519 PUBLIC_HOST_KEY_BASE64`.

The Ubuntu server needs Docker, Compose, and curl. Deployment uses `/root/projects/<repository-name>` and the repository name as the Compose project name, matching our manual deployment. If your manual deployment used a different directory/project name, adjust the workflow before running it.

The staging job has three visible steps: check out the code, deploy the published image, and verify the public URL. `scripts/deploy-via-ssh.sh` handles SSH setup and copies `compose.deploy.yaml`; it runs `scripts/deploy.sh` on the server. It pulls the exact image digest from the build job, replaces the existing `app` service, and checks HTTP locally and from the runner. No source clone or image build is needed on the server. `tasks/` remains bind-mounted in the same directory; ownership is set to the image's UID/GID 10001. Container replacement can briefly interrupt service. Failed health checks fail the job; automatic rollback is not implemented.

`compose.yaml` remains the local build configuration. Use `compose.deploy.yaml` for image-based server deployments. Later, production will use a separate environment with its own credentials and a real approval gate.

To run lint locally:

```bash
python -m pip install -r requirements-lint.txt
ruff check app tests --select E9,F63,F7,F82
ruff check app tests --select E,W,I --ignore E9 --exit-zero
```

## Tests included

The starter includes **4 unit tests**, **3 integration cases**, and **4 browser regression cases**. Unit tests exercise storage functions; integration tests exercise Flask routes with real temporary files. Backend tests use isolated directories and do not touch your app's tasks.

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows CMD: `py -3.12 -m venv .venv`, then `.venv\Scripts\activate.bat`.

Install the test dependencies (includes Flask) and run backend tests; no running app is needed:

```bash
python -m pip install -r requirements-test.txt
python -m pytest tests/unit
python -m pytest tests/integration
```

`python -m pytest` runs both backend suites by default. To run browser regression, start the app first, then:

```bash
python -m playwright install chromium
python -m pytest tests/regression --base-url http://localhost:5151
```

Tests run headlessly in Chromium. For staging, replace the URL with `http://SERVER_IP:5151`. Browser tests cover create, status updates, and deletion across reloads; each test cleans up only its own uniquely named tasks. Use local/staging, not production.

Reports from the most recent run: `reports/report.html` and `reports/junit.xml`. Failed browser tests also save screenshots and traces under `reports/playwright/`. These generated files are ignored by Git.

## Demo scope

Docker runs Gunicorn as a non-root user with one worker and four threads, so an idle browser connection does not block every request. The direct Python command runs Flask's development server. This starter has no authentication and is not ready for public hosting: task titles become filenames without validation, duplicate titles overwrite tasks, and multiline descriptions are not handled correctly. These limitations will be addressed before public deployment.

## Source

Adapted from [supersqa1/todo-app-flask-demo](https://github.com/supersqa1/todo-app-flask-demo), commit `1e918f19c0a42222cdb47687a71f700971f69619`. Sample data and unused duplicate code were omitted.
