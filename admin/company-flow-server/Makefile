.PHONY: up down logs ps scale-worker
up:
	docker compose up --build -d
down:
	docker compose down
logs:
	docker compose logs -f api worker scheduler
ps:
	docker compose ps
scale-worker:
	docker compose up -d --scale worker=3
