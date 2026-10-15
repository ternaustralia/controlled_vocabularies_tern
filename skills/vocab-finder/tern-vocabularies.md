# TERN vocabularies on RVA

Optional TERN vocabularies you can add to `sources.md`. Endpoints are the current release on [Research Vocabularies Australia (RVA)](https://vocabs.ardc.edu.au/) as at 2026-10-15.

| Vocabulary | Covers | Release | SPARQL endpoint |
|---|---|---|---|
| [TERN Parameters](https://vocabs.ardc.edu.au/viewById/394) | Observable properties, e.g. plant height (already in `sources.md`) | 2026-02-19 | `https://vocabs.ardc.edu.au/repository/api/sparql/tern-rva_parameters-scheme_2026-02-19` |
| [TERN Attribute Scheme](https://vocabs.ardc.edu.au/viewById/358) | Attributes of things in the TERN Ontology, e.g. transect direction | 2025-10-20 | `https://vocabs.ardc.edu.au/repository/api/sparql/tern-rva_attribute-scheme_2025-10-20` |
| [TERN Feature of Interest Scheme](https://vocabs.ardc.edu.au/viewById/372) | Types of things observed, e.g. plant occurrence | 2025-10-20 | `https://vocabs.ardc.edu.au/repository/api/sparql/tern-rva_feature-of-interest-scheme_2025-10-20` |
| [NVIS Categorical Values Version 7](https://vocabs.ardc.edu.au/viewById/761) | Value lists for NVIS vegetation attributes, e.g. growth forms | 2026-05-21 | `https://vocabs.ardc.edu.au/repository/api/sparql/tern-rva_nvis-categorical-values-version-7_2026-05-21` |
| [EMSA modules: Attributes](https://vocabs.ardc.edu.au/viewById/651) | Attributes used in EMSA field survey modules | 2.0.0 | `https://vocabs.ardc.edu.au/repository/api/sparql/dcceew_ecological-monitoring-system-australia-emsa-module_2-0-0` |
| [EMSA modules: Observable Properties](https://vocabs.ardc.edu.au/viewById/653) | Properties measured in EMSA modules, e.g. plant height | 2.0.0 | `https://vocabs.ardc.edu.au/repository/api/sparql/dcceew_test-test-test_2-0-0` |
| [EMSA modules: Monitoring protocols](https://vocabs.ardc.edu.au/viewById/654) | EMSA modules and protocols, e.g. camera trapping | 2.0.0 | `https://vocabs.ardc.edu.au/repository/api/sparql/dcceew_testforprotocolsvocab_2-0-0` |
| [EMSA modules: Collections of Categorical Values](https://vocabs.ardc.edu.au/viewById/655) | Value lists used in EMSA modules | 2.0.0 | `https://vocabs.ardc.edu.au/repository/api/sparql/dcceew_testforlutsss_2-0-0` |

## How to add one

1. In `sources.md`, copy section 3 (TERN) and change the name, description and endpoint. The same search and details queries work.
2. Add a row for it to the table at the top of `sources.md`.
3. Add only the vocabularies you need, so the skill stays quick.
