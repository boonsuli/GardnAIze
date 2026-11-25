#!/usr/bin/env bash

# GardnAIze - GDAI-PLANT V1
# Local PostgreSQL configuration (WSL2 + Docker)

export GDAI_PLANT_DSN="host=127.0.0.1 port=5433 dbname=gardnaize_ml user=gardnaize"

# Ask for password only if not already configured
if [[ -z "${PGPASSWORD:-}" ]]; then
    read -rsp "PostgreSQL password: " PGPASSWORD
    echo
    export PGPASSWORD
fi

echo "GDAI-PLANT local environment configured."
echo "Database: gardnaize_ml"
echo "Host: 127.0.0.1:5433"
echo "User: gardnaize"
