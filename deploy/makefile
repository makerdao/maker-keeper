APP = maker-keeper
HELM_CONFIG = ./prod/values.yaml
CHART = common
CHART_REPO = https://makerops.github.io/helm-charts
CHART_VER = 0.0.11
TIMEOUT = 5m0s

.ONESHELL:
.SHELL := /bin/bash

.PHONY: check update-repo dryrun deploy

check:
	@if command -v helm >/dev/null 2>&1; then \
		echo "Helm is installed. Continue..."; \
	else \
		echo "Helm is not installed. Please install it to deploy"; \
		exit 1; \
	fi

update-repo: check
	@echo "Updating Helm repository..."
	helm repo add $(CHART) $(CHART_REPO)
	helm repo update

dryrun: update-repo
	@echo "Starting dry run..."
	helm upgrade --install $(APP) $(CHART) \
		--repo $(CHART_REPO) \
		-f $(HELM_CONFIG) \
		--namespace $(APP) \
		--create-namespace \
		--timeout $(TIMEOUT) \
		--version $(CHART_VER) \
		--atomic \
		--dry-run

deploy: update-repo
	@echo "Starting deployment..."
	helm upgrade --install $(APP) $(CHART) \
		--repo $(CHART_REPO) \
		-f $(HELM_CONFIG) \
		--namespace $(APP) \
		--create-namespace \
		--timeout $(TIMEOUT) \
		--version $(CHART_VER) \
		--atomic
