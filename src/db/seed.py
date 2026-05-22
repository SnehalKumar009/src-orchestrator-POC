"""Seed the database with realistic sample data for POC."""

from src.db.database import init_db, get_session
from src.db.models import Scan, SrcRequirement, SrcFinding, ComplianceStatus, FixStatus, DeltaType


SAMPLE_REQUIREMENTS = [
    {"req_id": "SEC-509-CERT-2", "psb_text": "All X.509 certificates must be validated including chain verification and revocation checking.", "section": "Cryptography", "category": "crypto", "priority": "P10"},
    {"req_id": "SEC-TLS-VER-1", "psb_text": "Only TLS 1.2 and TLS 1.3 shall be supported. TLS 1.0 and 1.1 must be disabled.", "section": "Cryptography", "category": "crypto", "priority": "P10"},
    {"req_id": "SEC-CRY-ALGO-3", "psb_text": "Deprecated cipher suites (RC4, DES, 3DES) must not be used.", "section": "Cryptography", "category": "crypto", "priority": "P10"},
    {"req_id": "SEC-AUT-PWD-1", "psb_text": "Default credentials must not be present in production builds.", "section": "Authentication", "category": "auth", "priority": "P10"},
    {"req_id": "SEC-AUT-SSO-2", "psb_text": "SAML/OAuth SSO integration must use signed assertions with expiry validation.", "section": "Authentication", "category": "auth", "priority": "P20"},
    {"req_id": "SEC-NET-PORT-1", "psb_text": "Services must bind only to required network interfaces, not 0.0.0.0.", "section": "Network", "category": "network", "priority": "P20"},
    {"req_id": "SEC-NET-FW-2", "psb_text": "Firewall rules must restrict inbound traffic to documented ports only.", "section": "Network", "category": "network", "priority": "P20"},
    {"req_id": "SEC-LOG-AUD-1", "psb_text": "All authentication events (success/failure) must be logged in CEF format.", "section": "Logging", "category": "logging", "priority": "P20"},
    {"req_id": "SEC-HRD-SSH-1", "psb_text": "SSH must disable root login and use key-based authentication only.", "section": "Hardening", "category": "hardening", "priority": "P10"},
    {"req_id": "SEC-HRD-PERM-2", "psb_text": "Config files containing credentials must have 600 permissions.", "section": "Hardening", "category": "hardening", "priority": "P20"},
    {"req_id": "SEC-DEP-LIB-1", "psb_text": "All third-party libraries must be free of known CVEs with CVSS >= 7.0.", "section": "Deprecation", "category": "deprecation", "priority": "P10"},
    {"req_id": "SEC-DEP-VER-2", "psb_text": "Deprecated APIs and protocols must be removed before GA release.", "section": "Deprecation", "category": "deprecation", "priority": "P20"},
]

SAMPLE_COMPONENTS = [
    "ccm/Projects/CAPF",
    "ccm/Projects/CallManager",
    "ccm/Projects/CTIManager",
    "cup/Projects/XCP",
    "cer/Projects/DRF",
    "cuc/Projects/Unity",
]

AGENT_MAP = {
    "crypto": "crypto_agent",
    "auth": "auth_agent",
    "network": "network_agent",  
    "logging": "logging_agent",
    "hardening": "hardening_agent",
    "deprecation": "deprecation_agent",
}

SAMPLE_FINDINGS = [
    # Crypto findings
    {"req_idx": 0, "comp_idx": 0, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.NEW,
     "reason": "CAPF does not validate full X.509 certificate chain. Only leaf cert is checked.",
     "fix_steps": "1. Update ssl_verify_cert() to call X509_verify_cert() with full chain\n2. Add CRL/OCSP check\n3. Update test_ssl_handshake test", "ai_score": 82.0},
    {"req_idx": 1, "comp_idx": 1, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.CHANGED,
     "reason": "CallManager SIP TLS listener still accepts TLS 1.0 connections.",
     "fix_steps": "1. Set SSL_CTX_set_min_proto_version to TLS1_2_VERSION\n2. Remove TLS 1.0/1.1 from cipher list\n3. Verify with openssl s_client", "ai_score": 88.0},
    {"req_idx": 2, "comp_idx": 2, "status": ComplianceStatus.PARTIAL, "delta": DeltaType.UNCHANGED,
     "reason": "CTIManager uses AES-256-GCM but fallback to 3DES is still enabled in config.",
     "fix_steps": "1. Remove 3DES from allowed_ciphers in cti_tls.conf\n2. Restart CTI service\n3. Run cipher scan to verify", "ai_score": 75.0},
    # Auth findings
    {"req_idx": 3, "comp_idx": 1, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.NEW,
     "reason": "Default admin/admin credentials found in platformConfig.xml.",
     "fix_steps": "1. Remove default credentials from platformConfig.xml\n2. Force password change on first login\n3. Add credential check to CI pipeline", "ai_score": 92.0},
    {"req_idx": 4, "comp_idx": 3, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.UNCHANGED,
     "reason": "XCP SAML handler does not validate assertion signature expiry.",
     "fix_steps": "1. Add NotOnOrAfter check in SAMLResponseParser\n2. Reject expired assertions\n3. Add unit test with expired token", "ai_score": 68.0},
    # Network findings
    {"req_idx": 5, "comp_idx": 4, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.NEW,
     "reason": "DRF backup service binds to 0.0.0.0:4040 instead of loopback.",
     "fix_steps": "1. Change bind address to 127.0.0.1 in drf_backup.conf\n2. Add iptables rule for port 4040\n3. Verify with netstat", "ai_score": 85.0},
    # Logging findings
    {"req_idx": 7, "comp_idx": 5, "status": ComplianceStatus.PARTIAL, "delta": DeltaType.UNCHANGED,
     "reason": "Unity logs auth events but not in CEF format. Uses plain text.",
     "fix_steps": "1. Replace log_auth_event() with cef_log_auth_event()\n2. Include CEF header fields\n3. Validate with CEF parser", "ai_score": 60.0},
    # Hardening findings
    {"req_idx": 8, "comp_idx": 0, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.CHANGED,
     "reason": "sshd_config allows root login (PermitRootLogin yes).",
     "fix_steps": "1. Set PermitRootLogin no in /etc/ssh/sshd_config\n2. Set PasswordAuthentication no\n3. Restart sshd\n4. Test SSH access with key", "ai_score": 90.0},
    {"req_idx": 9, "comp_idx": 2, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.NEW,
     "reason": "CTIManager db_credentials.conf has 644 permissions, readable by all.",
     "fix_steps": "1. chmod 600 db_credentials.conf\n2. chown root:root db_credentials.conf\n3. Add permission check to install script", "ai_score": 95.0},
    # Deprecation findings
    {"req_idx": 10, "comp_idx": 3, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.NEW,
     "reason": "XCP uses log4j 1.2.17 which has CVE-2021-44228 (CVSS 10.0).",
     "fix_steps": "1. Upgrade to log4j 2.21.0\n2. Update import statements\n3. Migrate XML config to log4j2 format\n4. Run full test suite", "ai_score": 87.0},
    {"req_idx": 11, "comp_idx": 1, "status": ComplianceStatus.PARTIAL, "delta": DeltaType.UNCHANGED,
     "reason": "CallManager still uses deprecated SSLv3 API calls in legacy module.",
     "fix_steps": "1. Replace SSL_CTX_new(SSLv3_method) with TLS_method()\n2. Remove SSLv3 references\n3. Run regression tests", "ai_score": 72.0},
    {"req_idx": 5, "comp_idx": 5, "status": ComplianceStatus.NON_COMPLIANT, "delta": DeltaType.NEW,
     "reason": "Unity REST API binds to 0.0.0.0:8443 instead of management interface only.",
     "fix_steps": "1. Change bind to management VLAN IP\n2. Update firewall rules\n3. Verify with port scan", "ai_score": 78.0},
]


def seed_database():
    """Populate the database with sample data."""
    init_db()
    session = get_session()

    try:
        # Check if already seeded
        if session.query(Scan).first():
            print("Database already seeded. Skipping.")
            return

        # 1. Create requirements
        requirements = []
        for req_data in SAMPLE_REQUIREMENTS:
            req = SrcRequirement(**req_data)
            session.add(req)
            requirements.append(req)
        session.flush()

        # 2. Create a scan
        scan = Scan(
            week=20, year=2026, csdl_id="247258",
            total_findings=len(SAMPLE_FINDINGS),
            non_compliant_count=sum(1 for f in SAMPLE_FINDINGS if f["status"] == ComplianceStatus.NON_COMPLIANT),
            partial_count=sum(1 for f in SAMPLE_FINDINGS if f["status"] == ComplianceStatus.PARTIAL),
            compliant_count=0,
            summary="Week 20/2026 scan: 12 findings across 6 components. 9 NON_COMPLIANT, 3 PARTIAL."
        )
        session.add(scan)
        session.flush()

        # 3. Create findings
        for f_data in SAMPLE_FINDINGS:
            req = requirements[f_data["req_idx"]]
            comp = SAMPLE_COMPONENTS[f_data["comp_idx"]]
            category = req.category

            finding = SrcFinding(
                scan_id=scan.id,
                requirement_id=req.id,
                component=comp,
                status=f_data["status"],
                reason=f_data["reason"],
                fix_steps=f_data["fix_steps"],
                category=category,
                risk_area=req.section,
                delta_type=f_data["delta"],
                routed_agent=AGENT_MAP.get(category),
                fix_status=FixStatus.PENDING,
                ai_score=f_data["ai_score"],
            )
            session.add(finding)

        session.commit()
        print(f"Seeded: 1 scan, {len(requirements)} requirements, {len(SAMPLE_FINDINGS)} findings.")

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_database()
