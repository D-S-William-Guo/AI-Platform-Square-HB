.PHONY: doctor venv backend-install backend-dev backend-test frontend-install frontend-dev frontend-build app-serve db-up db-down test

doctor:
	bash scripts/doctor.sh

venv:
	bash scripts/venv.sh

backend-install:
	bash scripts/backend_install.sh

backend-dev:
	bash scripts/backend_dev.sh

backend-test:
	bash scripts/backend_test.sh

frontend-install:
	bash scripts/frontend_install.sh

frontend-dev:
	bash scripts/frontend_dev.sh

frontend-build:
	bash scripts/frontend_build.sh

app-serve:
	bash scripts/app_serve.sh

db-up:
	docker compose up -d mysql

db-down:
	docker compose down

test: backend-test frontend-build
