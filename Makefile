SHELL := /bin/bash

PYTHON ?= python3
DJANGO_SETTINGS_MODULE ?= vert_helper.tests.settings
TEST_PATH ?= vert_helper.tests
TEST_VERBOSITY ?= 2

TRIVY_IMAGE ?= aquasec/trivy:0.69.3
TRIVY_SEVERITY ?= HIGH,CRITICAL

DOCKER_REPO ?= django-vert-helper
DOCKER_TAG ?= local
DOCKER_IMAGE ?= $(DOCKER_REPO):$(DOCKER_TAG)
DOCKER_CONTEXT ?= .
DOCKERFILE ?= Dockerfile-example
COMPOSE_FILE ?= docker-compose.yml

.PHONY: \
	test-unit \
	trivy-fs \
	image-build \
	trivy-image \
	scan-audit \
	stack-up \
	stack-down \
	stack-smoke

test-unit:
	@if [ -d .venv ]; then \
		. .venv/bin/activate && \
		DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) \
		$(PYTHON) -m django test $(TEST_PATH) -v $(TEST_VERBOSITY); \
	else \
		DJANGO_SETTINGS_MODULE=$(DJANGO_SETTINGS_MODULE) \
		$(PYTHON) -m django test $(TEST_PATH) -v $(TEST_VERBOSITY); \
	fi

trivy-fs:
	docker run --rm \
		-v "$(PWD):/workspace" \
		-w /workspace \
		$(TRIVY_IMAGE) \
		fs --exit-code 1 --severity $(TRIVY_SEVERITY) \
		--scanners vuln,secret --format table ./

image-build:
	docker build --no-cache \
		-f $(DOCKERFILE) \
		-t $(DOCKER_IMAGE) \
		$(DOCKER_CONTEXT)

trivy-image:
	docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		$(TRIVY_IMAGE) \
		image --exit-code 1 --ignore-unfixed \
		--severity $(TRIVY_SEVERITY) --scanners vuln \
		--format table $(DOCKER_IMAGE)

scan-audit: trivy-fs image-build trivy-image

stack-up:
	docker compose -f $(COMPOSE_FILE) up -d

stack-down:
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans

stack-smoke:
	docker compose -f $(COMPOSE_FILE) exec -T postgres \
		pg_isready -U postgres -d vert_helper
	docker compose -f $(COMPOSE_FILE) exec -T kafka \
		kafka-topics --bootstrap-server kafka:9092 --list >/dev/null
	curl -fsS http://localhost:4566/_localstack/health | grep -qi 's3'
