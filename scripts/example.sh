#!/bin/bash


./scripts/reset.sh
head -c 5M </dev/urandom >storage/x
python cli.py signature storage/x
echo x >> storage/x
python cli.py update storage/x
diff -u --color  metadata/x-*/chunks.json metadata/x/chunks.json
