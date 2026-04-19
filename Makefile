up:
	docker-compose -f docker/docker-compose.yml build
	docker-compose -f docker/docker-compose.yml up -d

down:
	docker-compose -f docker/docker-compose.yml down

destroy-database:
	docker-compose -f docker/docker-compose.yml down
	docker volume rm -f fastapi_template_db_data

connect-db:
	docker exec -it postgres-db psql -U app_user -d app_db

connect-app:
	docker exec -it -w /app/app fastapi-app /bin/bash

# Database migration commands
migrate-up:
	@echo "Running database migrations..."
	docker exec fastapi-app alembic upgrade head

migrate-down-last:
	@echo "Rolling back database migrations..."
	docker exec fastapi-app alembic downgrade -1

# use as 'make migrate-revision message="Migration Description"'
migrate-revision:
	@echo "Creating new migration revision..."
	docker exec fastapi-app alembic revision --autogenerate -m "$(message)"
