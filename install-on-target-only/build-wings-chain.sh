#!/bin/sh
# Build the chain Wings serves from the leaf Angie issued.
# YE1 is signed by Root YE (2025), which is not in trust stores yet.
# leaf + YE1 + Root YE cross-signed by ISRG Root X2 chains to a root
# Debian already trusts. Run on the home server, as root.
set -eu

DIR="${1:-/etc/pterodactyl/ssl}"
LEAF="${DIR}/leaf.pem"
OUT="${DIR}/fullchain.pem"
YE1_URL="https://letsencrypt.org/certs/gen-y/int-ye1.pem"
ROOT_URL="https://letsencrypt.org/certs/gen-y/root-ye-by-x2.pem"

if [ ! -f "$LEAF" ]; then
    echo "build-wings-chain: no leaf at ${LEAF}" >&2
    exit 1
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

curl -fsS -o "${stage}/ye1.pem" "$YE1_URL"
curl -fsS -o "${stage}/root-ye.pem" "$ROOT_URL"
cat "$LEAF" "${stage}/ye1.pem" "${stage}/root-ye.pem" > "${stage}/fullchain.pem"

if ! openssl verify -untrusted "${stage}/fullchain.pem" "$LEAF" >/dev/null 2>&1; then
    echo "build-wings-chain: chain does not verify ${LEAF}" >&2
    exit 1
fi

install -o certsync -g certsync -m 640 "${stage}/fullchain.pem" "$OUT"
echo "build-wings-chain: wrote ${OUT}"
