.PHONY: doctor venv backend-install backend-dev backend-test frontend-install frontend-dev frontend-build app-serve app-run release-bundle service-install service-start service-stop service-restart service-status service-logs service-uninstall db-up db-down test

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

app-run:
	bash scripts/app_run.sh

release-bundle:
	bash scripts/release_bundle.sh

service-install:
	bash scripts/service_install.sh

service-start:
	bash scripts/service_start.sh

service-stop:
	bash scripts/service_stop.sh

service-restart:
	bash scripts/service_restart.sh

service-status:
	bash scripts/service_status.sh

service-logs:
	bash scripts/service_logs.sh

service-uninstall:
	bash scripts/service_uninstall.sh

db-up:
	docker compose up -d mysql

db-down:
	docker compose down

test: backend-test frontend-build
