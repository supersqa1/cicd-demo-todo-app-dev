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

## Pipeline: checks, staging, and production

`.github/workflows/cicd.yaml` runs checks on pull requests targeting `main` (opened, reopened, or updated) and the full release pipeline on pushes to `main`:

- Runs real Ruff linting: syntax/selected correctness errors block the pipeline; style findings are reported without blocking.
- Runs real unit and integration tests in separate jobs; failures block image publishing. Each job uploads HTML/JUnit reports.
- Builds AMD64 and ARM64 images and pushes to `ghcr.io/<owner>/<repo>:<full-commit-sha>` after all three initial jobs pass.
- Authenticates automatically using `GITHUB_TOKEN` with `packages: write`; no custom secrets needed.
- Outputs the full image tag, digest, and digest-based reference for later deployment. The published image details appear in the job summary.

PRs run only lint, unit, and integration tests: no publishing, server credentials, or deployments. A feature-branch push without an open PR does not run the workflow. On a merge (or direct push) to `main`, the checks run again before publishing and deployment. The manual trigger and rehearsal-branch exception have been removed.

Main release runs are serialized so another deployment cannot replace staging while regression tests are running. PRs run independently; newer commits cancel older checks for that same PR.

**Merge blocking is separate:** branch protection/required status checks have not been configured as part of this workflow change. Until configured, failing PR checks report a failure but do not necessarily prevent a merge. To enforce the policy, require PRs and the `Lint`, `Unit tests`, and `Integration tests` checks on `main`. Production still requires its existing environment approval.

After staging succeeds, **Automation / Regression** installs Chromium and runs `tests/regression` headlessly against the staging URL. Failures block the later approval/production jobs. The upload step uses `if: always()` so reports and any failure screenshots/traces are retained even when tests fail. Download the `staging-regression` artifact from the Actions run; report artifacts are kept for 7 days. The browser job uses Ubuntu 24.04 for Playwright system dependency support.

After regression passes, the production job waits for a required reviewer, deploys the same image digest, and passes its public URL to a read-only smoke job. There are no placeholder jobs left. The public template includes all three test suites so recording can focus on connecting them to the pipeline.

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

`compose.yaml` remains the local build configuration. Use `compose.deploy.yaml` for image-based server deployments. Production uses the same scripts with its own environment settings and server; there is no image rebuild between environments.

### Production and approval

Prepare a second Ubuntu server with Docker and Compose, add the deployment public key, and verify SSH login. In **Settings → Environments → production**, add:

| Type | Name | Value |
| --- | --- | --- |
| Secret | `SSH_KEY` | Deployment private key (reused for this demo) |
| Variable | `SERVER_HOST` | Production IP or hostname |
| Variable | `SERVER_USER` | `root` for this disposable demo |
| Variable | `KNOWN_HOSTS` | Verified host-key entry for the production server |

Staging keeps the existing `STAGING_*` names; production uses the names above. Both jobs map their settings to the same script inputs.

Under **Deployment protection rules**, enable **Required reviewers**, select your GitHub user, and save. For a solo recording, leave **Prevent self-review** unchecked so you can approve your own push. Disable administrator bypass to demonstrate a required approval. These settings are separate from the YAML and must be configured in each new tutorial repository.

The production job has `needs: [package, automation]` and `environment: production`. GitHub pauses it before any steps run or production secrets are released. On the run page, select **Review deployments → production → Approve and deploy**. A failed regression job prevents reaching this gate.

The production smoke job then checks `/` and `/view_tasks` over HTTP without changing task data. It uses the public URL output rather than referencing the protected environment again, so it does not require a second approval. A failed smoke check fails the run; automatic rollback is not implemented.

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
