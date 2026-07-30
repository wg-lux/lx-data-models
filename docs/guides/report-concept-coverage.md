# Autoritative Befund- und Konzeptabdeckung

Dieses Dokument beschreibt den versionierten Coverage-Vertrag für klinische
Berichtsvorlagen. Es ist die technische Referenz für Template-Autorinnen,
Backend- und Frontend-Entwickler sowie für die fachliche Abnahme.

## Zweck und Grenze

Die Coverage beantwortet für jedes freigegebene Reporting-Konzept:

- Ist das Konzept auf die aktuelle Untersuchung anwendbar?
- Ist ein Wert dokumentiert?
- Ist der Wert gemäß der autorisierten Wertemenge gültig?
- Welche Validatoren und Payload-Pfade belegen das Ergebnis?

Coverage ist kein Ersatz für:

- klinische Vollständigkeit,
- Leitlinienadhärenz,
- fachliche Richtigkeit der Konzeptmatrix,
- eine Wirksamkeits- oder Qualitätsstudie.

Diese Aussagen benötigen eine separate klinisch annotierte Referenzmenge und
eine dokumentierte fachliche Freigabe.

## Autoritative Datenquelle

Die autoritative Auflösung entsteht ausschließlich serverseitig aus:

1. der tatsächlich geladenen KnowledgeBase,
2. der identifizierten Berichtsvorlage,
3. der typisierten `PExamination`-Payload,
4. den ausgeführten Runtime-Validatoren.

Die Validierungsrouten liefern das Ergebnis unter `concept_coverage`:

```text
POST /report-templates/{module}/{template}/validate
POST /report-templates/{module}/{template}/validate-from-ledger/{id}
```

Das Frontend zeigt die Serverantwort. Eine lokale Heuristik darf nur als
sichtbar gekennzeichneter, nicht autoritativer Fallback für alte Antworten
verwendet werden.

## Identität und Provenienz

Jedes Coverage-Ergebnis enthält:

- `contract_version` (`report_concept_coverage_v1`),
- Modulname, Modulversion und Modul-Digest,
- Template-Name, Template-Version und Template-Digest,
- Resolvername und Resolverversion,
- einen Digest aus Payload und Validatorresultat.

Ein Identitäts- oder Digest-Mismatch darf nicht automatisch repariert werden.
Der Vorgang muss laut fehlschlagen und darf kein klinisch gültiges Ergebnis
behaupten.

## Konzeptmetadaten in einer Vorlage

Eine anwendbare Coverage-Konzeptdefinition benötigt mindestens:

```yaml
coverage_version: report_concept_coverage_v1
coverage_concepts:
  - concept_id: colon.polyp.size_mm
    label: Polypengröße
    applicability_status: required
    validator_names:
      - colonoscopy_polyp_size_valid
    evidence_path:
      - patient_findings
    finding_selector:
      finding_name: colon_polyp
    concept_value_path:
      - patient_finding_classifications
      - "0"
      - patient_finding_classification_choices
      - "0"
      - classification_choice
    allowed_values:
      - "10"
      - "12"
```

Die fachliche Vorlage muss die tatsächliche Wertsemantik festlegen. Beispiel-
werte dürfen nicht ungeprüft als klinische Wertemenge übernommen werden.

Für wiederholte Befunde wird ein `finding_selector` verwendet. Der Builder
prüft alle passenden Instanzen in stabiler Payload-Reihenfolge und liefert
konkrete `evidence_paths`. Ein erster passender Treffer darf einen späteren
ungültigen Treffer nicht verdecken.

Ein `classification_choice` darf nur zusammen mit `classification_name`
angegeben werden. Für `not_applicable` ist kein Wertpfad erforderlich, aber ein
fachlich begründeter `applicability_reason` ist Pflicht.

## Statussemantik

| Status | Bedeutung |
| --- | --- |
| `present` | Wert vorhanden, explizit erlaubt und alle zugehörigen Validatoren erfolgreich |
| `missing` | Kein passender Befund beziehungsweise keine passende Instanz gefunden |
| `unknown` | Wert oder Kontext nicht auflösbar; keine positive Aussage zulässig |
| `invalid` | Wert vorhanden, aber nicht erlaubt, oder ein Validator schlägt fehl |
| `not_applicable` | Konzept ist aufgrund einer freigegebenen Regel nicht anwendbar |

`present` darf niemals allein aus einem lexikalischen Befundnamen oder der
Existenz eines JSON-Pfades abgeleitet werden. Fehlende Einheiten oder nicht
aufgelöste Synonyme dürfen nicht stillschweigend als gültig gelten.

## Einheiten und aktuelle Einschränkung

Die derzeitigen `PExamination`-/`PFinding`-Persistenzmodelle führen für die
patientenseitigen Befundwerte noch keine eigenständige, belastbare Einheit.
Deshalb darf eine Template-Autorenschaft aktuell keine Einheit als erfüllt
ausgeben, wenn sie nur aus KnowledgeBase-Metadaten stammt.

Die Einheitensicherheit benötigt einen eigenen, versionierten Vertrag für
Wert, Einheit, Umrechnung und zulässige Toleranz. Bis dahin bleiben solche
Konzepte `unknown` oder blockieren die Freigabe.

## Fail-Closed-Regeln

Die Runtime weist eine Vorlage mit `422` zurück, wenn unter anderem:

- `coverage_version` fehlt oder nicht unterstützt wird,
- stabile Konzept-IDs fehlen,
- eine anwendbare Regel keinen Wertpfad oder Selector besitzt,
- erlaubte Werte fehlen,
- ein referenzierter Validator nicht geliefert wird,
- die Template-Identität nicht mit der Route übereinstimmt.

Das ist beabsichtigt. Eine Vorlage ohne fachlich autorisierte Coverage-Matrix
ist nicht produktionsfähig und darf keine scheinbar vollständige Auflösung
liefern.

## Prüf- und Freigabeprozess

Vor einer klinischen Freigabe sind mindestens erforderlich:

1. Fachlich annotierte Positiv-, Negativ-, Nicht-anwendbar- und Ungültig-Fälle.
2. Tests für fehlende, unbekannte und nicht aufgelöste Werte.
3. Tests für mehrere Befundinstanzen desselben Befundtyps.
4. Nachweis von Modul-/Template-Version und Digest.
5. Reproduzierbare Evidence-Pfade und Validatorresultate.
6. Getrennte Prüfung von technischer Coverage und klinischer Vollständigkeit.
7. Dokumentierte fachliche Freigabe der Wertemengen, Regeln und Einheiten.

Die Produktionsreife wird ausschließlich im Feature-Tracker bewertet. Dieses
Dokument enthält keine eigene Fertigstellungsmarkierung.

## Relevante Implementierung

- Vertrag: `lx_dtypes/models/knowledge_base/report_template/ReportConceptCoverage.py`
- Template-Metadaten: `ReportTemplateCoverage.py`
- Runtime-Builder: `ReportConceptCoverageBuilder.py`
- API: `lx_dtypes/django/api/report_template_routes.py`
- Frontend-Vertrag: `frontend/src/types/reportTemplate.ts`
- Frontend-Anzeige: `frontend/src/views/reporting/ReportingShell.vue`
- Feature-Tracker: `feature-tracking/Colonoscopy.yml`
