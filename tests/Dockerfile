# GTS specification e2e test runner.
#
# Builds a self-contained image with Python + pytest deps that runs the
# gts-spec test suite against an external GTS server. The server is expected
# to be reachable from the container (e.g. via host.docker.internal when the
# server runs on the Docker host).
#
# Build (from the gts-spec repo root):
#   docker build -t gts-spec-e2e -f tests/Dockerfile tests
#
# Run against a server on the host (Mac/Docker Desktop):
#   docker run --rm gts-spec-e2e --gts-base-url http://host.docker.internal:8000
#
# Run against a server on the host (Linux — host.docker.internal not built-in):
#   docker run --rm --add-host=host.docker.internal:host-gateway \
#       gts-spec-e2e --gts-base-url http://host.docker.internal:8000

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /tests

# Install dependencies in a separately cached layer. requirements.txt is
# resolved first so pip picks the overrides listed there (notably pydantic
# 1.10.x); httprunner is then installed with --no-deps to sidestep its
# pydantic<1.9 pin without dragging the resolver into a downgrade spiral.
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
 && pip install -r requirements.txt \
 && pip install --no-deps 'httprunner>=4,<5'

# Bundle the test suite so the image is usable standalone. Callers can still
# mount a host directory over /tests to iterate without rebuilding.
COPY . /tests

ENTRYPOINT ["pytest", "-p", "no:cacheprovider"]
CMD ["/tests"]
