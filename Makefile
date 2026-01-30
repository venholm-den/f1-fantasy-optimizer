SHELL := /bin/bash

SEASON ?= 2025

.PHONY: help venv refresh scrape dims schedule all

help:
	@echo "Targets:"
	@echo "  make venv        - create .venv and install minimal deps"
	@echo "  make refresh     - scrape + dims + schedule for SEASON=$(SEASON)"
	@echo "  make scrape      - scrape f1fantasytools season tables"
	@echo "  make dims        - build dim_* tables"
	@echo "  make schedule    - export dim_round_dates.csv (Ergast/Jolpica)"
	@echo ""
	@echo "Examples:"
	@echo "  make venv"
	@echo "  make refresh SEASON=2024"

venv:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip && pip install requests

scrape:
	. .venv/bin/activate && python -m src.scrape_f1fantasytools --season $(SEASON)

dims:
	. .venv/bin/activate && python -m src.dimensions --season $(SEASON)

schedule:
	. .venv/bin/activate && python -m src.ergast_schedule --season $(SEASON)

refresh: scrape dims schedule
