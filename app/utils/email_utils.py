import re




def pip_install_hints() -> List[str]:
hints = []
if not DNSPY_AVAILABLE:
hints.append("pip install dnspython")
if not EMAIL_VALIDATOR_AVAILABLE:
hints.append("pip install email-validator")
return hints




def clean_domain(domain: str) -> str:
d = (domain or "").lower().strip()
d = re.sub(r'^https?://', '', d)
d = re.sub(r'^www\.', '', d)
return d.strip().rstrip('/')




def has_mx(domain: str) -> bool:
if not DNSPY_AVAILABLE:
return False
try:
answers = dns.resolver.resolve(domain, 'MX')
return len(answers) > 0
except Exception:
return False




def smtp_verify(email: str, timeout: float = 10.0) -> Optional[bool]:
if not DNSPY_AVAILABLE:
return None
try:
domain = email.split('@')[1]
answers = dns.resolver.resolve(domain, 'MX')
mx_record = str(answers[0].exchange).rstrip('.')
server = smtplib.SMTP(mx_record, timeout=timeout)
server.set_debuglevel(0)
server.helo("example.com")
server.mail("test@example.com")
code, _ = server.rcpt(email)
try:
server.quit()
except Exception:
server.close()
return code == 250
except smtplib.SMTPRecipientsRefused:
return False
except Exception:
return None




def is_catch_all(domain: str) -> bool:
if not DNSPY_AVAILABLE:
return False
try:
rand = random.randint(10000, 99999)
random_email = f"random{rand}@{domain}"
return smtp_verify(random_email) is True
except Exception:
return False




def simple_syntax_check(email: str) -> bool:
pattern = r"^[^@\s]+@[^@\s]+\.[^@\s
