# Bundeseinheitlicher Medikationsplan (BMP) — Technical Specification Summary

Derived from the four source documents in `docs/german-medication-plan/`:

| File | Content |
|---|---|
| `medikationsplan.pdf` | The base agreement ("Vereinbarung") between KBV, BÄK and DAV under § 31a Abs. 4 Satz 1 SGB V — legal scope, definitions, obligations. |
| `medikationsplan-anlage-1.pdf` | Annex 1 — operational rules for creation/update (handwritten fallback, etc.). Non-technical. |
| `medikationsplan-anlage-2.pdf` | Annex 2 — recommendations/explanations for users (physicians, pharmacists) on how to fill individual fields. Non-technical but clarifies semantics. |
| `medikationsplan-anlage-3.pdf` | Annex 3 — **the actual technical specification** ("Spezifikation für einen bundeseinheitlichen Medikationsplan (BMP)", **Version 2.8, dated 2025-10-01**, binding from **2026-07-01**). This is the primary source for everything below. |

This summary is the normative-content extract needed to design data-model compatibility. It does **not** yet map anything onto our existing `LabValue`/`MedicationSchedule` models — that comparison is the next step.

---

## 1. Legal/organizational context

- Legal basis: § 31a SGB V. Insured persons taking ≥3 concurrently prescribed reimbursable drugs have a right to a BMP, created by the GP (or treating specialist if no GP).
- The BMP is a **patient-held document**, handed out on paper. It is **not** a medication history, not a substitute for patient records/discharge letters/prescriptions, and completeness/currency cannot be guaranteed (a disclaimer is mandatory on the printout).
- Pharmacies may update it at the patient's request upon dispensing.
- A "MP-Modul" (medication-plan module) must exist in physician practice software (PVS) and is recommended for pharmacy software (AVS); it creates, edits, stores, and prints BMPs and reads/writes the 2D barcode.
- Conformance requires: following Annex 1 rules, producing a correct paper printout (content from §5 + keywords from Annexes 2/4), following syntax rules (Annex 2), producing/reading the 2D barcode per §7/Annex 8, meeting §3/§4 requirements, and applying the rules in Annex 9.
- Versioning: a new spec version becomes binding on its stated effective date; software reading barcodes must support the current version **plus all versions valid within the last year** (plus a transition period of max. 3 months).

## 2. What the BMP is / is not

- Contains: prescription drugs, OTC-but-pharmacy-only drugs the physician documents, self-medication (if medically/pharmaceutically relevant), and references to medical devices relevant to drug therapy (e.g., inhalers, pens) — but **not** a full medication history and **not** every drug ever taken, only what's currently relevant/applicable.
- Compounded preparations ("Rezeptur") are represented as a single descriptive free-text line, not as itemized ingredients.
- Combination products with >3 active substances are shown only as "Kombipräparat" (keyword 310) with substance/strength columns left blank.
- Patients may ask to omit specific drugs from the plan (documented risk accepted by patient).

## 3. Use cases (Kapitel 4)

1. Initial creation at a physician practice.
2. Update by the creating physician.
3. Update by a co-treating physician (reads existing plan via barcode, reconciles, reprints).
4. Update by a pharmacy (reconciles dispensed items, e.g. after Rabattvertrag/Aut-idem substitution; may add OTC self-medication on patient request).
5. Initial creation/update in a care institution (e.g. hospital discharge management).
6. Merging multiple concurrent plans (optional) — software should support side-by-side comparison, duplicate detection (same PZN or same active substance), and reconciliation.

Each update: old plan should be destroyed or at minimum have its barcode struck through/invalidated; a **new Instance-ID (GUID)** and new print timestamp are mandatory on every reprint (Anhang 9, Rule 15).

## 4. Document structure (paper layout, §6)

DIN A4 **landscape**, white paper (ideally 80 g/m²), black print only, Arial font, ≥0.85 cm margin. Fixed zones, each appearing once per page:

- **Identification block** (top-left, 7.0 × 4.0 cm): fixed title "Medikationsplan" (20pt bold), page X of Y (14pt), certification logo/text area (currently unused).
- **Administration block** (top-middle, 16.7 × 4.0 cm, 7 fixed lines): patient name block, birth date, printer name/institution + address/phone/email, print timestamp, and an optional 4-slot "parameter block" (weight, height, creatinine, allergies, pregnant, breastfeeding, free text — see §6 below).
- **Carrier area** (top-right): quiet zone + 2D Datamatrix barcode.
- **Medication table**: the actual drug/line entries (see §5).
- **Footer** (bottom-left): plan spec version, country code, language code, vendor area, reserved blank field, disclaimer text.

Max. ~15 medication rows/page, max. 5 pages (≈75 drugs) per the informative data sheet (Anhang 7); multi-page plans must keep page/total-page numbers consistent, and bound continuation rows (see below) must stay on the same page as their parent entry.

## 5. Medication table — row types

Every row in the medication table is exactly one of four types:

### 5.1 Medikationseintrag (medication entry) — the core row

Columns, fixed order (Tabelle 1), field codes in brackets:

| # | Field (code) | Notes |
|---|---|---|
| 1 | Wirkstoff / Wirkstoffname (4.1) | Active substance name(s); free text or from drug DB. Blank for Mehrkomponentenpräparat. |
| 2 | Arzneimittelname / Handelsname (4.2) | Trade name; no package-size info. |
| 3 | Wirkstärke (4.3) | Strength(s); order must match substance order. Blank for Mehrkomponentenpräparat. |
| 4 | Darreichungsform (4.4) | Dosage form, patient-friendly abbreviation; either coded (from Referenzdatenbank § 31b SGB V) or free text — **never both**. |
| 5 | Dosierschema (4.5) | Dosing schedule — structured 4-slot scheme, weekly variant, or free text — mutually exclusive (Anhang 9, Rule 22). |
| 6 | Dosiereinheit (4.6) | Dose unit — coded (Anhang 4) or free text — mutually exclusive (Rule 24). |
| 7 | Hinweise (4.7, optional) | Free-text usage notes (≤80 chars print / up to 1 line-break in carrier). |
| 8 | Behandlungsgrund (4.8, optional) | Patient-understandable reason for treatment, free text, min. 2 chars if present. |

Up to **3 substances/strengths** can be listed per entry (line-break separated; 2 may alternatively use `/` inline). >3 substances ⇒ render as "Kombipräparat" with blank substance/strength columns.

Ordering rule: substance order **must** match strength order **must** match the ATC-driven / Referenzdatenbank-defined substance order, and this order must be identical between the printout and the carrier segment XML.

### 5.1.1 Gebundene Zusatzzeile (bound continuation line)

An optional free-text line (≤31/200 chars depending on context) permanently attached to one medication or compound entry, for extra dosing/usage detail that doesn't fit the normal fields. Not combinable with the weekly-dosing row (5.1.2).

### 5.1.2 Zusätzliche Zeile bzgl. der wöchentlichen Dosierung (weekly dosing line)

New in v2.8 (§6.2.11). For weekly medications (e.g. Methotrexat):

- The 4-slot scheme column prints literally `"siehe nächste Zeile"`.
- A dedicated extra row prints: `<Wochentag>s <morgens>-<mittags>-<abends>-<nachts>`.
- No other content allowed in that row; no bound continuation line allowed in combination.
- All weekly-dosed entries are **auto-grouped** under the fixed heading "Wöchentliche Anwendung" — users cannot assign them elsewhere.
- Weekday is a controlled value 1=Montag … 7=Sonntag (Anhang 9, Rule 28).
- Rule: the 4-slot (morgens-mittags-abends-nachts) scheme may **only** be used for daily dosing or for once-weekly dosing with a mandatory weekday attribute — never for other intervals (those must be free text, Kapitel 3.4).

### 5.2 Rezeptureintrag (compounded-preparation entry)

Free-text description of a compounded preparation (code 5.3), optionally with its own bound continuation line (5.4). Ingredient-level listing is explicitly discouraged.

### 5.3 Freitextzeile (free-text line)

Independent free-text note not tied to any drug (code 5.2); can be grouped with a Zwischenüberschrift into a trailing "Hinweisblock".

### 5.4 Zwischenüberschrift (sub-heading)

Code 5.1. Either a **controlled value** from Anhang 2.3 Tabelle 6 (OID `1.2.276.0.76.3.1.1.5.2.42`, published at KBV's `schluesseltabellen.asp`) or free text — never both for the same block (Anhang 9, Rules 17/18). Known controlled headings include: Bedarfsmedikation, Dauermedikation, Intramuskuläre Anwendung, Besondere Anwendung, Intravenöse Anwendung, Anwendung unter die Haut, Fertigspritze, Selbstmedikation, Allergiehinweise, Wichtige Hinweise, Wichtige Angaben, "zu besonderen Zeiten anzuwendende Medikamente", "zeitlich befristet anzuwendende Medikamente", and the mandatory auto-heading **"Wöchentliche Anwendung"**. *(Exact numeric codes were not reliably extractable from the PDF's text layer — confirm against the published KBV table before implementing.)*

> Rule (Anhang 9, #17): from the second block onward, every block **must** have a heading (code or free text).

## 6. Header / administration-block fields

| Code | Field | Notes |
|---|---|---|
| 1.1 | Identifikationsname | Fixed text "Medikationsplan" |
| 1.2/1.3 | Seitenzahl / Gesamtseitenzahl | Page X of Y; omitted entirely for single-page plans (Anhang 9, Rules 2/3/5/6) |
| 1.4 | Zertifizierungskennung | Reserved, currently unused |
| 2.1/2.2 | Vorname / Nachname | Patient first/last name |
| 2.22/2.23/2.24 | Titel / Vorsatzwort / Namenszusatz | Patient name affixes, eGK/VSDM-aligned |
| 2.3 | Patienten-ID | eGK "Versicherten-ID" — **carrier only**, not printed |
| 2.4 | Geburtsdatum | May be partial (e.g. year only) per eGK rules |
| 2.21 | Geschlecht | M / W / D / X — **must never be auto-filled by software** (Rule 9); carrier-only |
| 2.5 | Ausdruckende/r | Name of the person/institution that produced the current printout (physician, pharmacy, or institution) — **not a signature**, just an attribution |
| — | LANR / Apotheken-IDF / Krankenhaus-IK | At most **one** of these three identifiers may be present (Rule 10) |
| 2.6–2.10 | Straße, PLZ, Ort, Telefon, E-Mail | Contact data of the printer |
| 2.11 | Datum/Uhrzeit des Ausdrucks | Print timestamp; must be regenerated on every reprint along with a new Instance-ID (Rule 15) |
| 2.12 | Parameterblock | Up to 4 lines, 25 chars/line, composited from the optional clinical parameters below; **never auto-populated from primary-system data** — user must actively select values each time |

### 6.1 Parameter block sub-fields (optional, printed with fixed keyword templates)

| Field | Keyword (code) | Print template | Max length |
|---|---|---|---|
| Allergies/intolerances | 264 | `Allerg./Unv.: {}` | 50 chars |
| Pregnant | 266 | `schwanger` (printed only if true) | flag |
| Breastfeeding | 267 | `stillend` (printed only if true) | flag |
| Weight | 261 | `Gew.: {} kg` | 5 chars |
| Height | 268 | `Größe: {} cm` | 3 chars |
| Creatinine | 262 | `Krea.: {} mg/dl` | 5 chars |
| Sex | 263 | `Geschl.: {m\|w\|divers\|unbestimmt}` | — |
| Free-text parameter | — | raw text, ≤2 embedded line breaks (`~`) | 3×25 chars |

These are the **only** clinical/lab-like values the BMP carries — see §12 (relevance to LabValue) below.

## 7. Footer fields

| Code | Field | Notes |
|---|---|---|
| 6.1 | Versionsnummer | Format `x.y` on print (e.g. "2.8"); carrier format is `xxy` zero-padded (e.g. `028`) |
| 6.12 | Patchnummer | Carrier-only, sequential patch number for the spec version |
| 6.3 | Länderkennzeichen | ISO 3166-1 alpha-2, fixed `DE` |
| 6.4 | Sprachkennzeichen | ISO 639-1 alpha-2, fixed `DE` (carrier representation is a sequential 0–99 index per spec text — reconcile against actual XSD) |
| 6.6 | Herstellerbereich | Reserved vendor area, max 1.0×11.0 cm, not otherwise specified |
| 6.7 | Freifeld | Reserved blank area, max 1.0×5.0 cm — **must stay unprinted** |
| 6.9 | Disclaimerbereich | Fixed text, keyword 531: *"Für Vollständigkeit und Aktualität des Medikationsplans wird keine Gewähr übernommen."* |

## 8. Code systems & controlled vocabularies

- **PZN (Pharmazentralnummer)**: 8-digit German drug product identifier. In the carrier segment it's transmitted as an **integer 1..99999999 without leading zeros**; for display, leading zeros are re-added to form the 8-digit PZN.
- **Referenzdatenbank nach § 31b SGB V**: mandatory authoritative source for patient-friendly substance name, strength, and dosage-form (abbreviated) strings whenever a PZN-backed entry is used.
- **ATC-code-driven substance ordering**: for combination products, substance/strength order follows the Referenzdatenbank's defined rank order; this order must be identical in print and in the carrier XML.
- **Dosiereinheiten (dose units)** — Anhang 4, published table `S_BMP_DOSIEREINHEIT`, OID `1.2.276.0.76.3.1.1.5.2.41`. Attribute `DN` = display name (used on the printout), attribute `V` = code (used in the 2D barcode), attribute `Sortierung` = suggested UI ordering.
- **Zwischenüberschriften (sub-headings)** — Anhang 2.3 Tabelle 6, published table `S_BMP_ZWISCHENUEBERSCHRIFT`, OID `1.2.276.0.76.3.1.1.5.2.42`.
- **Fractions (Tabelle 7)**: only ½, ⅓, ¼, ⅔, ¾, ⅛ are allowed in the 4-slot dosing scheme; comma is the decimal separator; automatic fraction↔decimal conversion requires explicit user interaction (not automatic); leading zeros in decimals may not be dropped (e.g. `0,5` not `,5`); `0,125` instead of `1/8` is disallowed.
- **Weekdays**: controlled integers 1 (Montag) … 7 (Sonntag) — used only for the weekly-dosing row.
- **Länder-/Sprachcodes**: ISO 3166-1 alpha-2 / ISO 639-1 alpha-2.
- **E-Mail syntax**: RFC 5322 (explicitly **not** RFC 6531 / internationalized addresses).
- **Character set**: ISO/IEC 8859-1 (Latin-1) for the carrier segment; control chars 0–31 and 127 excluded; all other Latin-1 code points allowed.

## 9. The 2D barcode / Carrier segment (§7, Anhang 8)

- Barcode symbology: **Datamatrix** per ISO/IEC 16022.
- Payload: an XML document (the "Carriersegment") — a fairly literal serialization of the BMP's data fields, built from a KBV-maintained XSD (hosted at `https://update.kbv.de/ita-update/Verordnungen/Arzneimittel/BMP/`, not reproducible as text from this PDF since Annex 8 is embedded as diagram images, not machine text).
- No compression/encryption. No XML prolog in the serialized form (encoding is implicitly ISO-8859-1, to be assumed `<?xml version="1.0" encoding="ISO-8859-1"?>` when parsing, but omitted when serializing). No whitespace/line breaks between elements (size optimization).
- **Hard size limit: 1400 bytes/characters per barcode.** If content would exceed this, the software must either optimize or split content across additional pages; single-page output is preferred when possible.
- Root element: `<MP U="{GUID}" v="{version}"> ... </MP>`
  - `U` = Instance-ID, a GUID **without dashes**, regenerated on every single printout (even without content changes) (Anhang 9, Rule 1/15).
  - `v` = plan spec version, zero-padded 3-digit form (e.g. `028` = v2.8).
- **Data minimization principle (§7.3.2)**: if a PZN is given, the dependent fields (Handelsname, Darreichungsform, Wirkstoff, Stärke) should generally be *omitted* from the XML and derived from the drug database on read — they're only written explicitly when they deviate from the database.
- Line breaks inside free-text fields use the literal tilde character `~` (ISO-8859-1 decimal 126); users must never be allowed to type `~` directly into those fields. Only specific fields allow embedded line breaks at all (Parameter-Freitext, Freitextzeile, Rezepturzeile, gebundene Zusatzzeile, weekly-dosing line, Hinweise, Behandlungsgrund), each capped at 1–2 embedded breaks depending on field (see Anhang 9 rules 16/25/26/27/29/30).
- Medication-entry order in the carrier **must** be preserved exactly as the user ordered them on the printout; reordering is a user action only, not automatic.
- Every block after the first **must** carry a sub-heading (code or free text) — this is how line grouping/association to a Zwischenüberschrift is structurally represented.

### 9.1 Carrier element/attribute map (best-effort reconstruction from Tabelle 3 — **verify against the actual XSD before implementing**, since Annex 8 itself ships only as diagrams, not machine-readable text)

```
MP                     (root; U=Instance-ID GUID, v=version "0yy", p=patch#, a=page#, z=total pages, l=lang/country index)
├─ MP.P                (patient)
│    g=Vorname, f=Nachname, t=Titel, v=Vorsatzwort, z=Namenszusatz,
│    egk=Patienten-ID (eGK), b=Geburtsdatum, s=Geschlecht
├─ MP.A                (author/printer: physician, pharmacy, or institution)
│    n=Name, lanr=LANR, idf=Apotheken-IDF, kik=Krankenhaus-IK,
│    s=Straße, z=PLZ, c=Ort, p=Telefon, e=E-Mail, t=Ausdruck-Zeitstempel
├─ MP.O                (optional clinical parameters — header parameter block)
│    w=Gewicht, h=Körpergröße, c=Kreatinin, ai=Allergien/Unverträglichkeiten,
│    [stillend]=?, [schwanger]=?, x=Parameter-Freitext   ⚠ exact attribute
│    letters for "stillend"/"schwanger" could not be reliably read from the
│    extracted PDF text (table reflow garbled columns) — confirm against XSD
└─ MP.S                (one block per Zwischenüberschrift grouping)
     c=Zwischenüberschrift-Code, t=Zwischenüberschrift-Freitext  (mutually excl.)
     ├─ MP.S.M         (Medikationseintrag)
     │    p=PZN, a=Arzneimittelname(Handelsname)
     │    ├─ MP.S.M.W  (repeatable, one per substance, ≤3)
     │    │    w=Wirkstoffname, s=Wirkstärke
     │    f=Darreichungsform(code), fd=Darreichungsform(Freitext)   (mutually excl.)
     │    wo=Wochentag (weekly dosing only)
     │    m=morgens, d=mittags, v=abends, h=zur Nacht   (4-slot scheme)
     │    t=Freitextdosierung                            (mutually excl. w/ m/d/v/h)
     │    du=Dosiereinheit(code), dud=Dosiereinheit(Freitext)      (mutually excl.)
     │    [Hinweise]=?, [Behandlungsgrund]=?             ⚠ exact attribute letters
     │    unclear from extraction — likely single-letter attributes near "i"/"r"
     │    x=gebundene Zusatzzeile
     ├─ MP.S.R         (Rezeptureintrag)
     │    t=Rezeptur-Freitext, x=gebundene Zusatzzeile
     └─ MP.S.X         (Freitextzeile)
          t=Freitext
```

## 10. Validation rules (Anhang 9 — normative, abridged)

Selected rules most relevant to a data model (full list has 30 entries):

1. Instance-ID is a GUID **without dashes**.
2. Page number starts at 1 for multi-page plans; **must be omitted entirely for single-page plans**.
3. Page number ≤ total page count.
4. Patient identity fields (Versicherten-ID, name parts, DOB) follow eGK/VSDM formats; eGK values preferred when available.
5. **Sex must never be auto-populated by software** — always an explicit user choice.
6. At most **one** of LANR / Apotheken-IDF / Krankenhaus-IK may be present.
7. Every reprint gets a **new Instance-ID and new print timestamp**.
8. From the 2nd medication block onward, a heading (code or free text) is mandatory; a block may have **either** a coded or free-text heading, never both.
9. PZNs are transmitted with leading zeros stripped.
10. Coded dosage form (per Referenzdatenbank) and free-text dosage form are mutually exclusive per entry.
11. Dosing scheme is **either** the structured 4-slot scheme (possibly with "siehe nächste Zeile" for weekly dosing) **or** free text — never mixed.
12. Dose unit is either coded (Anhang 4) or free text, never both.
13. Weekday values are restricted to 1–7 (Mon–Sun).
14. Free-text fields with line-break support are capped at 1–2 embedded `~` characters depending on the field.

## 11. Relevance to the existing `LabValue` / `MedicationSchedule` models (flag for next step)

- The BMP's **medication entries** map fairly directly onto something like a `MedicationSchedule` concept: substance(s), strength(s), dosage form, a structured W-X-Y-Z (or weekly, or free-text) dosing scheme, dose unit, notes, and treatment reason — plus PZN as an external drug-catalog key.
- The BMP's **parameter block** (weight, height, creatinine, pregnant, breastfeeding, sex, allergies) is **not** a general lab-value model — it's exactly 3 numeric clinical values (weight/height/creatinine) plus boolean/categorical patient attributes, entered manually at print time, explicitly **never auto-populated** from stored patient data. If we want BMP-import/export to interoperate with our `LabValue` model, we'll need to decide: (a) treat these 3 values as a thin, special-cased subset mapped to specific LabValue types/units on import, and (b) decide whether pregnant/breastfeeding/sex/allergies belong in a patient-demographics model rather than `LabValue` at all.
- `MedicationSchedule` compatibility will mainly be about the dosing-scheme representation (today's model vs. the mandatory W-X-Y-Z / weekly-dosing-row / free-text trichotomy) and whether we store/round-trip a PZN-keyed vs. free-text substance identity, since the spec treats those as mutually exclusive, order-correlated, and bound by strict mutual-exclusivity + line-break + length constraints.
- Import/export of the **2D barcode carrier XML** is the actual interoperability surface (that's what other systems exchange) — not the print layout. Getting the actual KBV XSD (Annex 8 is diagrams only in this PDF) before implementation is strongly recommended, since several attribute names in §9.1 above are reconstructed from a column-reflowed text table and are only "best effort."

## 12. Open items to resolve before implementation planning

1. Obtain the actual machine-readable XSD from `https://update.kbv.de/ita-update/Verordnungen/Arzneimittel/BMP/` to confirm exact carrier-XML element/attribute names (several are uncertain above, esp. in the `MP.O` block and the Hinweise/Behandlungsgrund attribute letters in `MP.S.M`).
2. Obtain the published keyword tables for Dosiereinheiten (OID `1.2.276.0.76.3.1.1.5.2.41`) and Zwischenüberschriften (OID `1.2.276.0.76.3.1.1.5.2.42`) from KBV's `schluesseltabellen.asp` service — the numeric codes for sub-headings were not reliably extractable from this PDF.
3. Decide how/whether the 3 BMP clinical parameters (weight, height, creatinine) and the pregnant/breastfeeding/sex/allergy attributes should round-trip through our `LabValue` model vs. a separate patient-demographics concept.
4. Decide how our current dosing-schedule representation maps onto the mandatory W-X-Y-Z / weekly / free-text trichotomy, including the "siehe nächste Zeile" + separate weekly-dosing-row mechanic.
5. Decide how/whether to model PZN as a first-class external drug identifier on `MedicationSchedule`, including the "data minimization" convention (PZN present ⇒ other fields typically omitted and derived from a drug DB) and the combination-product (`Mehrkomponentenpräparat`/`Kombipräparat` with >3 substances) special cases.
