#!/bin/bash

# while true; do
#     sleep 60
# done

uvicorn main:app --reload --host 0.0.0.0 --port 8000
