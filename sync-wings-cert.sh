#!/bin/sh
# Push the cert Angie manages for the Wings node name.
# Runtime values come from the environment (systemd loads
# /etc/nomcproxy/certsync.env). Install remembers the same values
# in /etc/nomcproxy/settings.json.
# Angie stores PEM already: certificate.pem + private.key. If only
# .crt/.key exist, build PEM. rsync -c skips an unchanged copy.
set -eu

: "${NOMC_ACME_CLIENT:?set NOMC_ACME_CLIENT (certsync.env)}"
: "${NOMC_CERTSYNC_HOST:?set NOMC_CERTSYNC_HOST (certsync.env)}"
NOMC_CERTSYNC_USER="${NOMC_CERTSYNC_USER:-certsync}"
NOMC_CERTSYNC_DIR="${NOMC_CERTSYNC_DIR:-/etc/pterodactyl/ssl}"
NOMC_CERTSYNC_KEY="${NOMC_CERTSYNC_KEY:-/root/.ssh/nomcproxy-certsync}"

SRC="/var/lib/angie/acme/${NOMC_ACME_CLIENT}"

if [ ! -d "$SRC" ]; then
    echo "certsync: Angie has no cert dir yet: ${SRC}" >&2
    echo "certsync: it appears after the node name resolves and Angie issues." >&2
    exit 0
fi

cert=""
priv=""
if [ -f "${SRC}/certificate.pem" ] && [ -f "${SRC}/private.key" ]; then
    cert="${SRC}/certificate.pem"
    priv="${SRC}/private.key"
elif [ -f "${SRC}/certificate.crt" ] && [ -f "${SRC}/private.key" ]; then
    cert="${SRC}/certificate.crt"
    priv="${SRC}/private.key"
else
    echo "certsync: ${SRC} has no certificate.pem/private.key yet" >&2
    exit 0
fi

stage=$(mktemp -d)
trap 'rm -rf "$stage"' EXIT

if [ -f "${SRC}/chain.pem" ]; then
    cat "$cert" "${SRC}/chain.pem" > "${stage}/fullchain.pem"
else
    openssl x509 -in "$cert" -out "${stage}/fullchain.pem"
fi
openssl pkey -in "$priv" -out "${stage}/privkey.pem"
chmod 600 "${stage}/privkey.pem"

changed=$(rsync -ac --itemize-changes --chmod=Fu=rw,go= \
    -e "ssh -i ${NOMC_CERTSYNC_KEY} -o StrictHostKeyChecking=accept-new" \
    "${stage}/fullchain.pem" "${stage}/privkey.pem" \
    "${NOMC_CERTSYNC_USER}@${NOMC_CERTSYNC_HOST}:${NOMC_CERTSYNC_DIR}/")

if [ -z "$changed" ]; then
    echo "certsync: unchanged, not reloading wings"
    exit 0
fi

echo "certsync: updated from ${SRC}"
echo "$changed"
ssh -i "$NOMC_CERTSYNC_KEY" -o StrictHostKeyChecking=accept-new \
    "${NOMC_CERTSYNC_USER}@${NOMC_CERTSYNC_HOST}" \
    "sudo systemctl reload wings || sudo systemctl restart wings"
echo "certsync: wings reloaded"
