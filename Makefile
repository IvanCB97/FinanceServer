VENV?=venv

.PHONY: setup start stop clean

setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

start: setup
	docker-compose up -d

stop:
	docker-compose down

clean:
	docker-compose down -v
	rm -rf $(VENV)
