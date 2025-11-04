#!/usr/bin/env bash
export PYTHONUNBUFFERED=1
export PYTHONPATH=.
uvicorn app.main:app --reload --port 8080