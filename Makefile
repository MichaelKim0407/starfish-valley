build:
	docker-compose build --pull

.build-lock:
	docker-compose build --pull dependency-lock

.lock:
	docker-compose run --rm dependency-lock

lock: .build-lock .lock build
