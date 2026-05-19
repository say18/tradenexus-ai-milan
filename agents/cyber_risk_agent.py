import os
import json
import socket
import ssl
import httpx
import asyncio
from datetime import datetime, timezone
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key=os.getenv("FEATHERLESS_API_KEY")
)

# Common ports to check
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    80: "HTTP", 443: "HTTPS", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt", 27017: "MongoDB"
}


def extract_domain(company_name: str) -> str:
    """Company name থেকে likely domain বের করে।"""
    name = company_name.lower().strip()
    name = name.replace(" ", "").replace(",", "").replace(".", "").replace("inc", "").replace("ltd", "").replace("corp", "")
    return f"{name}.com"


def check_domain_dns(domain: str) -> dict:
    """DNS resolution check।"""
    try:
        ip = socket.gethostbyname(domain)
        return {"resolved": True, "ip": ip}
    except Exception:
        return {"resolved": False, "ip": None}


def check_ssl_cert(domain: str) -> dict:
    """SSL certificate check।"""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                expire_str = cert.get("notAfter", "")
                try:
                    expire_dt = datetime.strptime(expire_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    days_left = (expire_dt - datetime.now(timezone.utc)).days
                    expired = days_left < 0
                    expiring_soon = 0 <= days_left <= 30
                except Exception:
                    days_left = None
                    expired = False
                    expiring_soon = False

                issuer = dict(x[0] for x in cert.get("issuer", []))
                return {
                    "valid": True,
                    "issuer": issuer.get("organizationName", "Unknown"),
                    "expires": expire_str,
                    "days_left": days_left,
                    "expired": expired,
                    "expiring_soon": expiring_soon,
                }
    except ssl.SSLError as e:
        return {"valid": False, "error": f"SSL Error: {str(e)}", "expired": True}
    except Exception as e:
        return {"valid": False, "error": str(e), "expired": False}


def scan_ports(ip: str, timeout: float = 0.8) -> dict:
    """Common ports scan করে।"""
    if not ip:
        return {"scanned": False, "open_ports": [], "risky_ports": []}

    open_ports = []
    risky = []

    for port, service in COMMON_PORTS.items():
        try:
            with socket.create_connection((ip, port), timeout=timeout):
                open_ports.append({"port": port, "service": service})
                # Risky ports
                if port in [21, 23, 3306, 3389, 5432, 6379, 27017]:
                    risky.append({"port": port, "service": service, "risk": "Exposed sensitive service"})
        except Exception:
            pass

    return {
        "scanned": True,
        "open_ports": open_ports,
        "risky_ports": risky,
        "risky_count": len(risky)
    }


async def check_crt_sh(domain: str) -> dict:
    """crt.sh দিয়ে certificate transparency check।"""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"https://crt.sh/?q={domain}&output=json")
            if r.status_code == 200:
                certs = r.json()
                count = len(certs)
                # Check for suspicious subdomains
                subdomains = set()
                for cert in certs[:50]:
                    name = cert.get("name_value", "")
                    for sub in name.split("\n"):
                        sub = sub.strip().lstrip("*.")
                        if sub and sub != domain:
                            subdomains.add(sub)
                return {
                    "found": True,
                    "cert_count": count,
                    "subdomains_found": len(subdomains),
                    "sample_subdomains": list(subdomains)[:5]
                }
    except Exception as e:
        return {"found": False, "error": str(e)}
    return {"found": False}


async def check_urlscan(domain: str) -> dict:
    """urlscan.io free API — malware/phishing check।"""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"https://urlscan.io/api/v1/search/?q=domain:{domain}&size=5",
                headers={"Accept": "application/json"}
            )
            if r.status_code == 200:
                data = r.json()
                results = data.get("results", [])
                malicious = sum(1 for r in results if r.get("verdicts", {}).get("overall", {}).get("malicious", False))
                return {
                    "scans_found": len(results),
                    "malicious_flags": malicious,
                    "flagged": malicious > 0
                }
    except Exception:
        pass
    return {"scans_found": 0, "malicious_flags": 0, "flagged": False}


async def check_breach_hibp_free(domain: str) -> dict:
    """HaveIBeenPwned free domain search (no key needed for domain check)."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"https://haveibeenpwned.com/api/v3/breacheddomain/{domain}",
                headers={"User-Agent": "TradeNexusAI-SecurityCheck/1.0"}
            )
            if r.status_code == 200:
                data = r.json()
                return {
                    "breached": True,
                    "breach_count": len(data) if isinstance(data, list) else 1,
                    "details": data[:3] if isinstance(data, list) else data
                }
            elif r.status_code == 404:
                return {"breached": False, "breach_count": 0}
    except Exception:
        pass
    return {"breached": None, "breach_count": 0, "note": "Check unavailable"}


def ai_risk_analysis(company: str, domain: str, osint_data: dict) -> dict:
    """Featherless AI দিয়ে সব OSINT data analyze করে final risk score দেয়।"""

    prompt = f"""You are a cybersecurity risk analyst specializing in supply chain security.

Analyze the following OSINT data for company "{company}" (domain: {domain}) and provide a cyber risk assessment.

OSINT FINDINGS:
{json.dumps(osint_data, indent=2, default=str)}

Provide your analysis in this EXACT JSON format (no extra text):
{{
  "cyber_risk_score": <0-100, where 100 is most risky>,
  "risk_level": "LOW" or "MODERATE" or "HIGH" or "CRITICAL",
  "key_vulnerabilities": ["vuln1", "vuln2", "vuln3"],
  "red_flags": ["flag1 or None detected"],
  "positive_signals": ["signal1 or None detected"],
  "attack_vectors": ["vector1", "vector2"],
  "recommendation": "One clear action for the buyer/SME",
  "summary": "2-3 sentence cybersecurity risk assessment"
}}

Scoring guide:
- Exposed RDP/databases = +30 points each
- No SSL or expired SSL = +25 points
- Domain breach = +20 points
- Malicious URL scan flags = +15 points
- Open Telnet/FTP = +20 points
- Everything clean = 0-15 (LOW)"""

    try:
        response = client.chat.completions.create(
            model="Qwen/Qwen2.5-72B-Instruct",
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.1
        )
        raw = response.choices[0].message.content
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        return {
            "cyber_risk_score": 50,
            "risk_level": "MODERATE",
            "key_vulnerabilities": ["Analysis error — manual review required"],
            "red_flags": [str(e)[:100]],
            "positive_signals": [],
            "attack_vectors": [],
            "recommendation": "Perform manual cybersecurity due diligence.",
            "summary": "Automated analysis failed. Manual review recommended."
        }


async def run_cyber_risk_check(company_name: str, domain: str = None) -> dict:
    """Main function — সব OSINT check run করে।"""

    if not domain:
        domain = extract_domain(company_name)

    print(f"🔍 Cyber Risk Check: {company_name} ({domain})")

    # Step 1: DNS
    dns = check_domain_dns(domain)
    ip = dns.get("ip")

    # Step 2: SSL
    ssl_info = check_ssl_cert(domain) if dns["resolved"] else {"valid": False, "error": "Domain not resolved"}

    # Step 3: Port scan (async-compatible via thread)
    port_data = {}
    if ip:
        loop = asyncio.get_event_loop()
        port_data = await loop.run_in_executor(None, scan_ports, ip)

    # Step 4: crt.sh + urlscan + HIBP (parallel)
    crt_data, urlscan_data, breach_data = await asyncio.gather(
        check_crt_sh(domain),
        check_urlscan(domain),
        check_breach_hibp_free(domain)
    )

    osint_data = {
        "domain": domain,
        "dns": dns,
        "ssl_certificate": ssl_info,
        "port_scan": port_data,
        "certificate_transparency": crt_data,
        "malware_scan": urlscan_data,
        "data_breach": breach_data,
        "scan_timestamp": datetime.now(timezone.utc).isoformat()
    }

    # Step 5: AI Analysis
    ai_result = ai_risk_analysis(company_name, domain, osint_data)

    return {
        "status": "success",
        "company": company_name,
        "domain": domain,
        "osint": osint_data,
        "ai_analysis": ai_result,
        "cyber_risk_score": ai_result.get("cyber_risk_score", 50),
        "risk_level": ai_result.get("risk_level", "MODERATE"),
        "source": "TradeNexus CyberRisk — Free OSINT"
    }


if __name__ == "__main__":
    import sys
    company = sys.argv[1] if len(sys.argv) > 1 else "Google"
    domain = sys.argv[2] if len(sys.argv) > 2 else None

    result = asyncio.run(run_cyber_risk_check(company, domain))
    print(json.dumps(result, indent=2, default=str))
