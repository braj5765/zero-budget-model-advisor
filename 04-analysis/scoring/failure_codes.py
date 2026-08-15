"""The content half of the failure taxonomy.

Scoring-Rubric.md §6 is the canonical list of all eight codes. The other five
— RATE_LIMIT, TIMEOUT, TRUNCATION, EMPTY, API_ERROR — are determinable from
the transport and live in 02-harness/clients/base.py. These three require
reading the response content, which is why they are here: the harness records,
it does not judge.
"""

REFUSAL = "REFUSAL"
MALFORMED = "MALFORMED"
HALLUCINATION = "HALLUCINATION"
