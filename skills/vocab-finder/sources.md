# Sources

Search only these sources, using only these calls. To add a source, add a section below in the same format.

| Source | Level | Best for |
|---|---|---|
| Darwin Core (TDWG) | Global | Standard field names (properties) |
| GBIF vocabularies | Global | Controlled value lists for Darwin Core fields |
| TERN (via ARDC RVA) | National | Observable properties / parameters (e.g. plant height) |

---

## 1. Darwin Core (TDWG)

**Find candidate terms** (one request, ~3 KB, one term name per line):
`https://raw.githubusercontent.com/tdwg/dwc/master/dist/simple_dwc_vertical.csv`

Pick up to 5 term names that may fit.

**Get term details** (one request per term):
`http://rs.tdwg.org/dwc/terms/{term}.json`, e.g. `http://rs.tdwg.org/dwc/terms/establishmentMeans.json`

Read `skos:prefLabel`, `skos:definition`, `dcterms:modified`. Always add `.json`: the plain IRI redirects to a very large page.

**PID:** `http://rs.tdwg.org/dwc/terms/{term}`

**Note:** Darwin Core has no specific term for most measurements (e.g. plant height). These are recorded with the MeasurementOrFact terms: `dwc:measurementType` (the name) and `dwc:measurementTypeID` (a PID from a vocabulary such as TERN's). Say this in the report when it applies.

---

## 2. GBIF vocabularies

**A. Value-list files** (one request each). Each `<concept>` has `dc:URI` (the PID), `dc:description` (definition) and labels.

| Darwin Core field | File |
|---|---|
| establishmentMeans | `https://rs.gbif.org/vocabulary/dwc/establishment_means_2025-07-10.xml` |
| degreeOfEstablishment | `https://rs.gbif.org/vocabulary/dwc/degree_of_establishment_2025-07-10.xml` |
| pathway | `https://rs.gbif.org/vocabulary/dwc/pathway_2025-07-10.xml` (~55 KB) |
| basisOfRecord | `https://rs.gbif.org/vocabulary/dwc/basis_of_record_2024-02-19.xml` |
| occurrenceStatus | `https://rs.gbif.org/vocabulary/gbif/occurrence_status_2020-07-15.xml` |
| lifeStage | `https://rs.gbif.org/vocabulary/gbif/life_stage.xml` |
| sex | `https://rs.gbif.org/vocabulary/gbif/sex.xml` |
| threatStatus (IUCN) | `https://rs.gbif.org/vocabulary/iucn/threat_status.xml` |
| units of measurement | `https://rs.gbif.org/vocabulary/gbif/unit_of_measurement_2015-07-10.xml` |
| vegetation layer | `https://rs.gbif.org/vocabulary/gbif/vegetation_layer.xml` |
| life form | `https://rs.gbif.org/vocabulary/gbif/life_form.xml` |

**B. Vocabulary server** (only if no file above fits):
- Find a vocabulary: `https://api.gbif.org/v1/vocabularies?q={keyword}&limit=20`
- List its values: `https://api.gbif.org/v1/vocabularies/{Name}/concepts?limit=20` (add `&q={keyword}` to filter)

Read `name`, `definition[].value`, `sameAsUris`. The API does not return a PID for each value: use `sameAsUris` if present, otherwise give the API URL and note "no PID".

---

## 3. TERN (via ARDC RVA)

Endpoint (TERN Parameters, release 2026-02-19):
`https://vocabs.ardc.edu.au/repository/api/sparql/tern-rva_parameters-scheme_2026-02-19`

Do not use TERN's own vocabulary endpoint or viewer.

Send each query as a GET request: `{endpoint}?query={URL-encoded query}`. Add the header `Accept: application/sparql-results+json` if you can; the default XML response is also fine.

**Search** (one request). Put the user's phrase first, plus up to 2 synonyms, all in lower case:

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?concept ?label ?definition WHERE {
  ?concept skos:prefLabel ?label ; skos:prefLabel|skos:altLabel ?match .
  OPTIONAL { ?concept skos:definition ?definition }
  FILTER(CONTAINS(LCASE(STR(?match)), "plant height") || CONTAINS(LCASE(STR(?match)), "vegetation height"))
} ORDER BY STRLEN(STR(?label)) LIMIT 20
```

If nothing is found, retry once with a single key word (e.g. "height"). The vocabulary also includes climate/ocean names (e.g. "sea surface height"); ignore them unless relevant.

**Details for the best matches** (one request, up to 5 concepts):

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX tern: <https://w3id.org/tern/ontologies/tern/>
SELECT ?concept ?property ?value WHERE {
  VALUES ?concept { <IRI-1> <IRI-2> }
  ?concept ?property ?value .
  FILTER(?property IN (skos:altLabel, skos:exactMatch, skos:closeMatch, skos:broader,
    tern:hasUnits, tern:hasCategoricalCollection,
    <http://purl.org/dc/terms/source>, <http://purl.org/dc/terms/modified>,
    <http://www.w3.org/2002/07/owl#deprecated>))
}
```

`exactMatch`/`closeMatch` link to the same idea in other vocabularies (useful evidence). Ignore matches that point to the concept itself.

**PID:** the `?concept` IRI, e.g. `http://linked.data.gov.au/def/tern-cv/09296da0-c645-4165-950c-780c21b3c140` (plant height).
