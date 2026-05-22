"""RAG ingestion pipeline — loads fix knowledge into the vector store."""

import uuid
from src.rag.embedder import embed_texts, chunk_jira_fix
from src.rag.vector_store import add_documents, get_stats

# ── Mock Jira Data (simulates resolved SRC epics) ─────────────────────────────

MOCK_JIRA_FIXES = [
    {
        "jira_key": "SRC-1001",
        "req_id": "SEC-509-CERT-2",
        "component": "ccm/Projects/CAPF",
        "category": "crypto",
        "fix_type": "code",
        "description": (
            "Fixed X.509 certificate chain validation in CAPF. "
            "The ssl_verify_cert() function only checked the leaf certificate. "
            "Updated to call X509_verify_cert() with the full chain store. "
            "Added OCSP stapling check and CRL distribution point lookup. "
            "Files changed: capf/src/ssl_utils.c, capf/src/cert_validator.c"
        ),
        "comments": [
            "Root cause: X509_STORE was initialized without loading intermediate CAs. "
            "Fix: Load CA bundle from /etc/ssl/certs/ca-certificates.crt into the store before verify.",
            "Also found that OCSP response was not being checked. Added ocsp_check() call after chain verify. "
            "See capf/src/ocsp_handler.c for the new function.",
            "Regression test added: test_cert_chain_validation() in capf/tests/test_ssl.py — "
            "covers self-signed, expired, revoked, and valid chain scenarios.",
        ],
        "code_diff": (
            "--- a/capf/src/ssl_utils.c\n"
            "+++ b/capf/src/ssl_utils.c\n"
            "@@ -145,6 +145,12 @@\n"
            "-    result = SSL_CTX_verify(ctx, leaf_cert);\n"
            "+    X509_STORE *store = X509_STORE_new();\n"
            "+    X509_STORE_load_locations(store, CA_BUNDLE_PATH, NULL);\n"
            "+    X509_STORE_CTX *verify_ctx = X509_STORE_CTX_new();\n"
            "+    X509_STORE_CTX_init(verify_ctx, store, leaf_cert, chain);\n"
            "+    result = X509_verify_cert(verify_ctx);\n"
            "+    if (result == 1) result = ocsp_check(leaf_cert);\n"
        ),
    },
    {
        "jira_key": "SRC-1002",
        "req_id": "SEC-TLS-VER-1",
        "component": "ccm/Projects/CallManager",
        "category": "crypto",
        "fix_type": "config",
        "description": (
            "Disabled TLS 1.0 and TLS 1.1 on CallManager SIP TLS listener. "
            "Set minimum protocol version to TLS 1.2. Updated cipher suite list "
            "to only include AEAD ciphers. Verified with openssl s_client that "
            "TLS 1.0/1.1 connections are rejected."
        ),
        "comments": [
            "Changed SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION) in sip_tls.c. "
            "Also updated the cipher string to 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM'.",
            "Verified: openssl s_client -connect localhost:5061 -tls1 now fails with 'protocol version' error.",
        ],
        "code_diff": (
            "--- a/cm/src/sip_tls.c\n"
            "+++ b/cm/src/sip_tls.c\n"
            "@@ -89,3 +89,5 @@\n"
            "-    SSL_CTX_set_options(ctx, SSL_OP_NO_SSLv3);\n"
            "+    SSL_CTX_set_min_proto_version(ctx, TLS1_2_VERSION);\n"
            "+    SSL_CTX_set_cipher_list(ctx, \"ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM\");\n"
        ),
    },
    {
        "jira_key": "SRC-1003",
        "req_id": "SEC-AUT-PWD-1",
        "component": "ccm/Projects/CallManager",
        "category": "auth",
        "fix_type": "code",
        "description": (
            "Removed default admin credentials from platformConfig.xml. "
            "Implemented first-login forced password change flow. "
            "Added CI check (check_default_creds.py) to prevent default credentials "
            "from being committed."
        ),
        "comments": [
            "The default admin/admin was in platformConfig.xml line 42. Removed and replaced "
            "with a placeholder that triggers setup wizard on first boot.",
            "Added pre-commit hook: scripts/check_default_creds.py scans for common default "
            "credential patterns in config files.",
        ],
        "code_diff": (
            "--- a/cm/config/platformConfig.xml\n"
            "+++ b/cm/config/platformConfig.xml\n"
            "@@ -40,4 +40,4 @@\n"
            "-    <admin-user>admin</admin-user>\n"
            "-    <admin-password>admin</admin-password>\n"
            "+    <admin-user>SETUP_REQUIRED</admin-user>\n"
            "+    <admin-password>CHANGE_ON_FIRST_LOGIN</admin-password>\n"
        ),
    },
    {
        "jira_key": "SRC-1004",
        "req_id": "SEC-HRD-SSH-1",
        "component": "ccm/Projects/CAPF",
        "category": "hardening",
        "fix_type": "config",
        "description": (
            "Hardened sshd_config on CAPF server. Disabled root login, "
            "disabled password authentication, set key-based auth only. "
            "Added banner and reduced MaxAuthTries to 3."
        ),
        "comments": [
            "Changes to /etc/ssh/sshd_config:\n"
            "PermitRootLogin no\nPasswordAuthentication no\nPubkeyAuthentication yes\n"
            "MaxAuthTries 3\nBanner /etc/ssh/banner.txt",
            "Tested: SSH as root now returns 'Permission denied'. Key-based login works for service account.",
        ],
        "code_diff": (
            "--- a/install/templates/sshd_config\n"
            "+++ b/install/templates/sshd_config\n"
            "@@ -12,4 +12,6 @@\n"
            "-PermitRootLogin yes\n"
            "-PasswordAuthentication yes\n"
            "+PermitRootLogin no\n"
            "+PasswordAuthentication no\n"
            "+PubkeyAuthentication yes\n"
            "+MaxAuthTries 3\n"
        ),
    },
    {
        "jira_key": "SRC-1005",
        "req_id": "SEC-DEP-LIB-1",
        "component": "cup/Projects/XCP",
        "category": "deprecation",
        "fix_type": "dependency",
        "description": (
            "Upgraded log4j from 1.2.17 to 2.21.0 in XCP module to remediate "
            "CVE-2021-44228. Migrated all log4j 1.x API calls to log4j 2.x API. "
            "Converted log4j.xml config to log4j2.xml format."
        ),
        "comments": [
            "Dependency chain: log4j-core 2.21.0, log4j-api 2.21.0, log4j-slf4j2-impl 2.21.0. "
            "Removed log4j 1.2.17 from pom.xml.",
            "Import changes: org.apache.log4j.Logger → org.apache.logging.log4j.LogManager. "
            "Logger.getLogger(cls) → LogManager.getLogger(cls).",
            "Config migration: log4j.xml appenders converted to log4j2.xml syntax. "
            "PatternLayout format preserved.",
        ],
        "code_diff": (
            "--- a/xcp/pom.xml\n"
            "+++ b/xcp/pom.xml\n"
            "@@ -55,4 +55,8 @@\n"
            "-    <dependency><groupId>log4j</groupId><artifactId>log4j</artifactId><version>1.2.17</version></dependency>\n"
            "+    <dependency><groupId>org.apache.logging.log4j</groupId><artifactId>log4j-core</artifactId><version>2.21.0</version></dependency>\n"
            "+    <dependency><groupId>org.apache.logging.log4j</groupId><artifactId>log4j-api</artifactId><version>2.21.0</version></dependency>\n"
        ),
    },
    {
        "jira_key": "SRC-1006",
        "req_id": "SEC-NET-PORT-1",
        "component": "cer/Projects/DRF",
        "category": "network",
        "fix_type": "config",
        "description": (
            "Changed DRF backup service bind address from 0.0.0.0 to 127.0.0.1. "
            "The service only needs local access for backup operations. "
            "Added iptables rule to drop external traffic on port 4040."
        ),
        "comments": [
            "In drf_backup.conf: bind_address changed from 0.0.0.0 to 127.0.0.1. "
            "Also added iptables -A INPUT -p tcp --dport 4040 -j DROP to firewall rules.",
            "Verified with 'netstat -tlnp | grep 4040' — now shows 127.0.0.1:4040 instead of 0.0.0.0:4040.",
        ],
        "code_diff": (
            "--- a/drf/config/drf_backup.conf\n"
            "+++ b/drf/config/drf_backup.conf\n"
            "@@ -8,2 +8,2 @@\n"
            "-bind_address=0.0.0.0\n"
            "+bind_address=127.0.0.1\n"
        ),
    },
    {
        "jira_key": "SRC-1007",
        "req_id": "SEC-LOG-AUD-1",
        "component": "cuc/Projects/Unity",
        "category": "logging",
        "fix_type": "code",
        "description": (
            "Converted Unity authentication logging from plain text to CEF format. "
            "Created cef_log_auth_event() utility function. All auth success/failure "
            "events now emit CEF-formatted syslog messages."
        ),
        "comments": [
            "CEF format: CEF:0|Cisco|Unity|14.0|AUTH_SUCCESS|User Login|3|src=x dst=y suser=admin",
            "Replaced 12 instances of log_auth_event() with cef_log_auth_event() across 4 files.",
        ],
        "code_diff": (
            "--- a/unity/src/auth_logger.py\n"
            "+++ b/unity/src/auth_logger.py\n"
            "@@ -22,4 +22,8 @@\n"
            "-def log_auth_event(user, success):\n"
            "-    logger.info(f'Auth {\"success\" if success else \"failure\"} for {user}')\n"
            "+def cef_log_auth_event(user, success, src_ip, dst_ip):\n"
            "+    severity = 3 if success else 7\n"
            "+    event = 'AUTH_SUCCESS' if success else 'AUTH_FAILURE'\n"
            "+    cef = f'CEF:0|Cisco|Unity|14.0|{event}|User Login|{severity}|src={src_ip} dst={dst_ip} suser={user}'\n"
            "+    syslog.info(cef)\n"
        ),
    },
]


def ingest_mock_jira_fixes():
    """Ingest mock Jira fix data into the RAG vector store."""
    all_chunks = []
    for fix in MOCK_JIRA_FIXES:
        chunks = chunk_jira_fix(fix)
        all_chunks.extend(chunks)

    if not all_chunks:
        print("No chunks to ingest.")
        return

    ids = [str(uuid.uuid4()) for _ in all_chunks]
    texts = [c["text"] for c in all_chunks]
    metadatas = [c["metadata"] for c in all_chunks]

    # Clean metadata — ensure no None values
    for m in metadatas:
        for k, v in list(m.items()):
            if v is None:
                m[k] = ""

    print(f"Embedding {len(texts)} chunks...")
    embeddings = embed_texts(texts)

    print(f"Storing {len(texts)} chunks in vector store...")
    add_documents(ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)

    stats = get_stats()
    print(f"Ingestion complete. Collection '{stats['name']}' now has {stats['count']} documents.")


if __name__ == "__main__":
    ingest_mock_jira_fixes()
