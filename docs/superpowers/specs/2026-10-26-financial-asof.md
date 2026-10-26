# Explicit financial information cutoff

Direction: daily US-equity historical research with CRSP price history kept source-qualified. This slice exposes the existing SEC engine's point-in-time selection through shared financial queries. It does not certify historical ticker membership, total returns, or portfolio readiness.

Add optional `as_of` to structured financials only, as a real UTC timestamp with second precision (`YYYY-MM-DDTHH:mm:ssZ`). No natural-language inference or date-only end-of-day assumption. Pin existing source release and bundle. Explicit cutoffs bypass current financial packets and request native annual/quarterly/TTM revision selection. Validate echoed cutoff and observation/leaf availability across every page, including accounting-check inputs. Reject missing, malformed, later, or inconsistent evidence. Preserve as_of in returned request and source metadata, independently from source coverage ceiling and data_as_of.

No upstream acquisition, raw dataset promotion or universe gate bypass. Existing no-cutoff reads stay compatible. A source cutoff ceiling or missing materialization remains an explicit error. MCP schema forwards the same input without expanding reader scope.
