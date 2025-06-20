VENV?=venv
.DEFAULT_GOAL := start

.PHONY: setup start stop clean

setup:
	command -v docker >/dev/null || (sudo apt-get update && sudo apt-get install -y docker.io)
	dpkg -s python3-venv >/dev/null 2>&1 || (sudo apt-get update && sudo apt-get install -y python3-venv)
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

start: setup
	docker compose up -d

stop:
	docker compose down

clean:
	docker compose down -v
	rm -rf $(VENV)
