.PHONY: up seed test eval

up:
	docker compose up --build

seed:
	docker compose exec api python -m app.services.seed

test:
	cd apps/api && pytest

eval:
	cd apps/api && python -m app.ai.evaluation.runner --dataset ../../evaluation/datasets/synthetic_support_cases.json --output ../../evaluation/reports/latest.json
