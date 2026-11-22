# Reference audit

`audit.csv` accounts for all 82 entries in the supplied bibliography and five
new entries. The active manuscript cites 23 sources, each checked against a
publisher, an author publication page or paper, or an official institutional
source. `retained_sources.json` records which claim each source supports and
what it does not establish.

The audit corrected, among other things, Mallucci's article number/DOI,
Seghini's article-number field, the authors and working-paper number of Igan,
Kim and Levy, the Barbados country report, and the precise ICMA document.
The published Bilal--Känzig 2026 version and Klusak et al. 2023 are cited.
The full text of Seghini, Dées and de Gaye's SSRN paper was not accessible;
existence/authorship were checked on the Banque de France author's page and
no numerical findings from it are attributed in the manuscript.

Crossref responses in `metadata/` are raw lookup diagnostics, not automatic
claim verification. Some received HTTP 429 or matched the wrong work. Such
records are explicitly unresolved or superseded by a primary-source check.
The bibliography retains no placeholder or unverified reference to support a
claim. Removed entries are not silently marked correct. The audit script can
refresh lookups independently of the scientific build; internet access and
`requirements-dev.txt` are needed for that optional operation.
