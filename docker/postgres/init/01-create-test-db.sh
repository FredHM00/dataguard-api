#!/bin/sh
# Cria o banco isolado de testes na primeira subida do container.
# Executado automaticamente pelo entrypoint oficial do Postgres.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOSQL
    CREATE DATABASE dataguard_test;
EOSQL
