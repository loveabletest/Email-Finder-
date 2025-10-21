import csv
total = len(df)


# ensure we access columns case-insensitively
for i, r in enumerate(df.itertuples(index=False), start=1):
# build row dict mapping original header names to values
row = {str(h): getattr(r, h) if hasattr(r, h) else r[idx] for idx, h in enumerate(headers)}


# case-insensitive pulls
def _get(col):
for h in headers:
if str(h).lower() == col:
return row.get(str(h))
return ''


first = str(_get('first') or '').strip()
last = str(_get('last') or '').strip()
domain = str(_get('company_website') or '').strip()


verified_email = ''
verification_status = ''


if domain:
candidates = generate_candidate_emails(first, last, domain)[:max_candidates_per_row]
for c in candidates:
time.sleep(random.uniform(sleep_min, sleep_max))
status = verify_email_status(c)
logs.append(f"[{i}/{total}] {c} -> {status}")
if progress_callback:
progress_callback(f"[{i}/{total}] Checking {c} -> {status}")
if status == 'deliverable':
verified_email = c
verification_status = status
break
if status == 'catch_all' and not verification_status:
verification_status = status
if status in ('undeliverable', 'inconclusive') and not verification_status:
verification_status = status


out_row = {str(h): getattr(r, h) if hasattr(r, h) else r[idx] for idx, h in enumerate(headers)}
out_row['verified_email'] = verified_email
out_row['verification_status'] = verification_status or ('no_domain' if not domain else 'none_found')


if only_verified:
if verified_email:
rows_out.append(out_row)
else:
rows_out.append(out_row)


out_df = pd.DataFrame(rows_out)
return out_df, logs




# Reuse the verify_email_status function but keep implementation in utils for clarity.
from app.utils.email_utils import verify_email_status
