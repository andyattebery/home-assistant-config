#!/usr/bin/env sh

secrets_dir="$(dirname $0)"

op inject --in-file "$secrets_dir/secrets.yaml.j2" > "$secrets_dir/secrets.yaml"