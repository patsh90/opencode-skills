---
# ---- letter parts ----
sender:
  - Jane Example
  - 12 Sample Street
  - 10115 Berlin
  - jane@example.org
recipient:
  - Example Housing Ltd.
  - Tenant Services
  - Musterweg 5
  - 20095 Hamburg
place: Berlin
date: 2026-09-28            # ISO date is written out in `language`; free text is kept as is
subject: Notice of termination of tenancy, flat 3B, Musterweg 5
reference: 2026-HX-0412     # optional
language: en-GB             # non-Polish: DIN 5008 layout (window left, date below, sign-off left)
salutation: Dear Sir or Madam,
closing: Yours faithfully,
signature_name: Jane Example
enclosures:                 # optional
  - Copy of tenancy agreement
  - Handover checklist

# ---- layout overrides (all optional; defaults shown; paper is always A4) ----
# window_side: left         # left | right (window on the right, e.g. France)
# margins: 25mm
# font: Liberation Serif
# font_size: 12pt
# line_spacing: 1.15
# align: left               # left | justify
# return_line: true         # small sender line above the address
# fold_marks: false
---

I hereby give notice to terminate the tenancy agreement for flat
**3B, Musterweg 5, 20095 Hamburg**, dated 1 March 2021, with effect from
**31 December 2026**. Please confirm receipt of this notice in writing.

Please return the security deposit to the following account:

| Account holder | IBAN                        | BIC        |
|----------------|-----------------------------|------------|
| Jane Example   | DE00 0000 0000 0000 0000 00 | EXAMPLEXXX |

At the handover I will:

- remove all furniture and fixtures I installed, and
- return all *three* sets of keys.
