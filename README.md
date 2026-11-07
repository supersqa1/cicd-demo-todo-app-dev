# CI/CD Demo To-Do App

A small Dockerized Flask app for the SuperSQA CI/CD tutorial series. Create, view, update, and delete tasks while learning how to build a deployment pipeline. This is the starter application; no CI/CD pipeline is included yet.

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

Open http://localhost:5151. The app is accessible only from your local machine.

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

On Windows, use `py -3.12 -m venv .venv` and activate with `.venv\Scripts\Activate.ps1` in PowerShell. Open http://localhost:5151; stop with Ctrl+C. Local task files use the same `tasks/` folder as Docker. Run only one app instance against that folder at a time.

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

## Demo scope

Docker runs Gunicorn as a non-root user. The direct Python command runs Flask's development server. This starter has no authentication and is not ready for public hosting: task titles become filenames without validation, duplicate titles overwrite tasks, and multiline descriptions are not handled correctly. These limitations will be addressed before public deployment.

## Source

Adapted from [supersqa1/todo-app-flask-demo](https://github.com/supersqa1/todo-app-flask-demo), commit `1e918f19c0a42222cdb47687a71f700971f69619`. Sample data and unused duplicate code were omitted.
