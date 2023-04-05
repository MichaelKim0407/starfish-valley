build:
	docker-compose build --pull prepare-data recommend

.build-lock:
	docker-compose build --pull dependency-lock dependency-lock-recommend

.lock:
	docker-compose run --rm dependency-lock
	docker-compose run --rm dependency-lock-recommend

lock: .build-lock .lock build
