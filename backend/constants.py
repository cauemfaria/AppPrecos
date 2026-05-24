"""
Shared constants used across the backend. Keeping these in one place
avoids magic strings being silently misspelled in queries.
"""

# processed_urls.status values
STATUS_QUEUED = 'queued'
STATUS_PROCESSING = 'processing'
STATUS_EXTRACTING = 'extracting'
STATUS_SUCCESS = 'success'
STATUS_ERROR = 'error'

# Active statuses used to detect in-flight or completed duplicates
ACTIVE_NFCE_STATUSES = [STATUS_SUCCESS, STATUS_PROCESSING, STATUS_EXTRACTING, STATUS_QUEUED]

# Placeholder market_id values stored temporarily before the real CNPJ is known
MARKET_ID_QUEUED = 'QUEUED'
MARKET_ID_UNRESOLVED = 'UNRESOLVED'

# Sentinel used when an NFCe item has no GTIN/EAN
NO_GTIN = 'SEM GTIN'
