# Bundeseinheitlicher Medikationsplan (BMP) — Technical Specification Summary

Derived from the four source documents in `docs/german-medication-plan/`:

| File | Content |
|---|---|
| `medikationsplan.pdf` | The base agreement ("Vereinbarung") between KBV, BÄK and DAV under § 31a Abs. 4 Satz 1 SGB V — legal scope, definitions, obligations. |
| `medikationsplan-anlage-1.pdf` | Annex 1 — operational rules for creation/update (handwritten fallback, etc.). Non-technical. |
| `medikationsplan-anlage-2.pdf` | Annex 2 — recommendations/explanations for users (physicians, pharmacists) on how to fill individual fields. Non-technical but clarifies semantics. |
| `medikationsplan-anlage-3.pdf` | Annex 3 — **the actual technical specification** ("Spezifikation für einen bundeseinheitlichen Medikationsplan (BMP)", **Version 2.8, dated 2025-10-01**, binding from **2026-07-01**). This is the primary source for everything below. |
| `beispiel_1.xml` | Official sample carrier-segment XML (ground truth for the XML shape). |
| `bmp_V2.8.xsd` | **Official W3C XML Schema for the carrier segment** (ground truth for element/attribute names, types, lengths, and validation constraints — supersedes any reconstruction from the PDF's text layer). |

This summary is the normative-content extract needed to design data-model compatibility. It does **not** yet map anything onto our existing `LabValue`/`MedicationSchedule` models — that comparison is the next step.

With the official XSD and sample now available, §9–§12 below are **confirmed against ground truth**, not reconstructed from PDF text.

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
- A dedicated extra printed row shows: `<Wochentag>s <morgens>-<mittags>-<abends>-<nachts>`.
- No other content allowed in that row; no bound continuation line allowed in combination (confirmed by XSD: attribute `x` "darf nur angegeben werden, wenn das Attribut wo nicht angegeben ist").
- All weekly-dosed entries are **auto-grouped** under the fixed heading "Wöchentliche Anwendung" (code `425`) — users cannot assign them elsewhere.
- Weekday is a controlled value 1=Montag … 7=Sonntag (Anhang 9, Rule 28; confirmed in XSD as attribute `wo` on the medication element itself).
- Rule: the 4-slot (morgens-mittags-abends-nachts) scheme may **only** be used for daily dosing or for once-weekly dosing with a mandatory weekday attribute — never for other intervals (those must be free text, Kapitel 3.4).

**Confirmed from the XSD/sample**: this is **not** a separate XML element/row. A weekly-dosed medication is still a single `<M>` element — it just also carries the `wo` (weekday) attribute alongside its normal `m`/`d`/`v`/`h` dose-slot attributes. The "separate row with 'siehe nächste Zeile'" is purely a **print-rendering rule**, not a distinct data node. E.g. from `beispiel_1.xml`:
```xml
<S c="425">
  <M p="3159468" wo="1" m="1" du="1" i="Alkoholkonsum vermeiden" r="Rheuma" />
  <M p="3971388" wo="2" m="1" du="1" r="Folsäure-Mangel" />
</S>
```

### 5.2 Rezeptureintrag (compounded-preparation entry)

Free-text description of a compounded preparation (code 5.3), optionally with its own bound continuation line (5.4). Ingredient-level listing is explicitly discouraged.

### 5.3 Freitextzeile (free-text line)

Independent free-text note not tied to any drug (code 5.2); can be grouped with a Zwischenüberschrift into a trailing "Hinweisblock".

### 5.4 Zwischenüberschrift (sub-heading)

Code 5.1. Either a **controlled value** (XSD attribute `S/@c`, enum below) or free text (`S/@t`, 1–50 chars) — never both for the same block (Anhang 9, Rules 17/18; XSD: "@t und @c DARF NICHT gleichzeitig angegeben werden"). The first block in a plan may omit the heading entirely; every block from the 2nd onward **must** have one.

**Confirmed controlled values (`S/@c` enum, from `bmp_V2.8.xsd`)** — note code `420` is intentionally absent:

| Code | Meaning |
|---|---|
| 411 | Bedarfsmedikation |
| 412 | Dauermedikation |
| 413 | Intramuskuläre Anwendung |
| 414 | Besondere Anwendung |
| 415 | Intravenöse Anwendung |
| 416 | Anwendung unter die Haut |
| 417 | Fertigspritze |
| 418 | Selbstmedikation |
| 419 | Allergiehinweise |
| 421 | Wichtige Hinweise |
| 422 | Wichtige Angaben |
| 423 | zu besonderen Zeiten anzuwendende Medikamente |
| 424 | zeitlich befristet anzuwendende Medikamente |
| 425 | Wöchentliche Anwendung (the mandatory auto-heading for weekly dosing entries) |

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
- **Dosiereinheiten (dose units)** — Anhang 4, published table `S_BMP_DOSIEREINHEIT`, OID `1.2.276.0.76.3.1.1.5.2.41`. Attribute `DN` = display name (used on the printout), attribute `V` = code (used in the 2D barcode), attribute `Sortierung` = suggested UI ordering. **Confirmed from the XSD**: the carrier-XML code (`M/@du`) is restricted to the single-character pattern `[#0-9a-v]` — i.e. a compact one-character alphabet of `#`, `0`–`9`, `a`–`v` (33 possible values) for up to 33 distinct controlled dose units; the sample uses `du="1"`, `du="p"`, `du="5"`.
- **Zwischenüberschriften (sub-headings)** — see the confirmed enum in §5.4 above (XSD `S/@c`, OID `1.2.276.0.76.3.1.1.5.2.42`).
- **Fractions (Tabelle 7)**: only ½, ⅓, ¼, ⅔, ¾, ⅛ are allowed in the 4-slot dosing scheme; comma is the decimal separator; automatic fraction↔decimal conversion requires explicit user interaction (not automatic); leading zeros in decimals may not be dropped (e.g. `0,5` not `,5`); `0,125` instead of `1/8` is disallowed. **Confirmed from the XSD** (`dosierungTyp` simple type), each of `M/@m`, `M/@d`, `M/@v`, `M/@h` must match: `([1-9]\d{0,3})|([1-9]\d,\d)|(\d,\d{1,2})|1/8|1/2|2/3|1/3|1/4|3/4` — i.e. a 1–4 digit integer with no leading zero, OR a 2-digit number with 1 decimal place, OR a 1-digit number with 1–2 decimal places, OR one of the 6 literal fraction strings `1/8`, `1/2`, `2/3`, `1/3`, `1/4`, `3/4`.
- **Weekdays**: controlled integers 1 (Montag) … 7 (Sonntag) — XSD attribute `M/@wo` (confirmed; it lives directly on the medication element, see §5.1.2).
- **Länder-/Sprachcodes**: combined as a single required attribute `MP/@l`, **fixed value `"de-DE"`** (confirmed from XSD — not two separate ISO codes as the PDF text implied).
- **E-Mail syntax**: RFC 5322 (explicitly **not** RFC 6531 / internationalized addresses).
- **Character set**: the XSD itself declares `UTF-8` (not ISO-8859-1 — that constraint from the PDF text applied to the *barcode's serialized byte stream*, not the logical XSD declaration; worth clarifying with KBV/an actual encoded sample before assuming one or the other for a given data source). Control chars 0–31 and 127 excluded per the PDF.

## 9. The 2D barcode / Carrier segment (§7, Anhang 8) — confirmed against `bmp_V2.8.xsd` and `beispiel_1.xml`

- Barcode symbology: **Datamatrix** per ISO/IEC 16022.
- Payload: an XML document (the "Carriersegment") validated against the official `bmp_V2.8.xsd` (KBV-maintained, published at `https://update.kbv.de/ita-update/Verordnungen/Arzneimittel/BMP/`).
- No compression/encryption. No XML prolog in the serialized barcode form. No whitespace/line breaks between elements in the actual barcode payload (size optimization) — the provided `beispiel_1.xml` is pretty-printed for readability, not the literal barcode bytes.
- **Hard size limit: 1400 bytes/characters per barcode.** If content would exceed this, the software must either optimize or split content across additional pages; single-page output is preferred when possible.
- Root element: `<MP v="028" U="{GUID}" l="de-DE" ...>`.
- **Data minimization principle (§7.3.2, confirmed in XSD annotation on `M`)**: *"Falls für eine Medikation eine PZN angegeben ist, so sind die anhand der PZN aus einer Arzneimitteldatenbank ableitbaren Attribute (inklusive Wirkstoffe) nicht anzugeben, außer Sie sind vom Anwender manuell anders erfasst."* — if a PZN is present, derivable fields (trade name, form, substances, strength) are normally omitted and only written when the user has manually overridden them relative to the drug database.
- Line breaks inside free-text fields use the literal tilde character `~`; each affected field has its own max-tilde-count constraint, enforced in the XSD only via documentation annotations (**not** machine-enforced by the XSD's `maxLength`/`pattern` facets — an implementation must add this validation itself).
- Medication-entry order in the carrier must be preserved exactly as authored; `<S>` blocks and the `<M>`/`<X>`/`<R>` choice sequence within them are ordered XML sequences, so document order **is** display order.
- `<S>` (block) `minOccurs="0" maxOccurs="23"`; within a block, the `<M>`/`<X>`/`<R>` choice has `maxOccurs="45"`. The first `<S>` may omit both `@c` and `@t` (no heading); every subsequent `<S>` must set exactly one of them.

### 9.1 Carrier element/attribute map — confirmed, from `bmp_V2.8.xsd`

```
<MP>                                     root element
  @v        required, fixed "028"       spec version (xxy format, zero-padded)
  @p        PROHIBITED in this release  patch number (reserved; not usable yet)
  @U        required                    Instance-ID: GUID, UPPERCASE HEX, 32 chars, NO dashes ([A-F0-9]{32})
  @a        optional, int 1–5           page number; omit entirely for single-page plans
  @z        optional, int 2–5           total pages; omit entirely for single-page plans
  @l        required, fixed "de-DE"     combined language-country tag (single attribute, not split)

  <P>                                    Patient (exactly one, required)
    @g      required, 1–45 chars        Vorname
    @f      required, 1–45 chars        Nachname
    @egk    optional, pattern [A-Z]\d{9}  Versicherten-ID (10-char eGK insurance number)
    @b      required, 8 chars           Geburtsdatum, format YYYYMMDD (day/month may be "00" for foreigners)
    @s      optional, enum M|W|X|D      Geschlecht — must never be auto-filled by software
    @t      optional, 1–20 chars        Titel (multiple titles space-separated)
    @v      optional, 1–20 chars        Vorsatzwort (e.g. "von")
    @z      optional, 1–20 chars        Namenszusatz (e.g. "Freifrau")

  <A>                                    Ausdruckender (exactly one, required): physician/pharmacy/institution that printed
    @lanr   optional, 9 digits          Lebenslange Arztnummer — at most ONE of lanr/idf/kik may be present
    @idf    optional, 7 digits          Apotheken-IDF
    @kik    optional, 9 digits          Krankenhaus-Institutionskennzeichen
    @n      required, 1–80 chars        Name of the printing person/institution
    @s      optional, 1–30 chars        Straße (+ Hausnummer)
    @z      optional, 5 digits          PLZ
    @c      optional, 1–20 chars        Ort
    @p      optional, 1–20 chars        Telefon
    @e      optional, 1–80 chars        E-Mail
    @t      required, xs:dateTime       Ausdruckdatum, format YYYY-MM-DDThh:mm:ss — regenerated on every reprint

  <O>                                    Parameter block (optional, at most one)
    @ai     optional, 1–50 chars        Allergien und Unverträglichkeiten (free text)
    @p      optional, enum "1" only     Schwanger — presence = true; absence = "no statement possible" (NOT "false")
    @b      optional, enum "1" only     Stillend — presence = true; absence = "no statement possible"
    @w      optional, decimal (0,999], 1 fraction digit   Gewicht in kg
    @h      optional, int [10,299]      Größe in cm
    @c      optional, decimal >=0, 2 fraction digits       Kreatininwert in mg/dl
    @x      optional, 1–77 chars, max 2 "~"                Parameterfreitext

  <S> (0..23, repeatable)                Block (Zwischenüberschrift grouping)
    @t      optional, 1–50 chars        Freitextzwischenüberschrift      } mutually exclusive;
    @c      optional, enum 411–425      Zwischenüberschrift-Code         } see §5.4 table
                                         (first block may have neither; every later block needs exactly one)
    choice, 1..45 of:
      <M>                                Medikationseintrag
        @p    optional, int [1,99999999]   Modifizierte PZN (no leading zeros)
        @a    optional, 1–50 chars         Arzneimittelname (Handelsname)
        <W> (0..3, repeatable, in substance order)   Wirkstoff
          @w  required, 1–80 chars         Wirkstoffname
          @s  optional, 1–15 chars         Wirkstärke (free text)
        @f    optional, pattern [A-Za-zäüößÄÜÖ]{1,10}  Darreichungsform-Code   } mutually exclusive
        @fd   optional, 1–7 chars          Darreichungsform-Freitext           } (f/fd)
        @wo   optional, enum 1–7           Wochentag (weekly dosing only; requires m/d/v/h — see 5.1.2)
        @m    optional, dosierungTyp       Dosierschema morgens   } 4-slot scheme;
        @d    optional, dosierungTyp       Dosierschema mittags   } mutually exclusive
        @v    optional, dosierungTyp       Dosierschema abends    } with @t as a group
        @h    optional, dosierungTyp       Dosierschema zur Nacht }
        @t    optional, 1–20 chars         Dosierschema-Freitext   (mutually excl. with m/d/v/h)
        @du   optional, pattern [#0-9a-v]  Dosiereinheit-Code (Anhang 4)        } mutually exclusive
        @dud  optional, 2–20 chars         Dosiereinheit-Freitext               } (du/dud)
        @i    optional, 1–80 chars, max 1 "~"   Hinweise
        @r    optional, 1–50 chars, max 1 "~"   Behandlungsgrund
        @x    optional, 1–200 chars, max 1 "~"  gebundene Zusatzzeile (only if @wo absent)
        (constraint: at least one attribute or one <W> must be given)
      <X>                                Freitextzeile
        @t    required, 1–200 chars, max 1 "~"
      <R>                                Rezeptureintrag
        @t    required, 1–200 chars, max 1 "~"   Rezeptur free text
        @x    optional, 1–200 chars, max 1 "~"   gebundene Zusatzzeile
```

`dosierungTyp` (used by `M/@m`, `@d`, `@v`, `@h`): `([1-9]\d{0,3})|([1-9]\d,\d)|(\d,\d{1,2})|1/8|1/2|2/3|1/3|1/4|3/4`.

**Correction vs. the earlier PDF-text-based reconstruction**: the "Stillend"/"Schwanger" attribute letters are confirmed as `O/@b` = Stillend and `O/@p` = Schwanger (the initial guess had these swapped); "Hinweise"/"Behandlungsgrund" are confirmed as `M/@i` and `M/@r` respectively; there is no separate XML node for the weekly-dosing print row (see §5.1.2).

## 10. Validation rules (Anhang 9 + XSD annotations — normative, abridged)

Selected rules most relevant to a data model (full list has 30 entries in Anhang 9; the XSD encodes most of these either structurally via `xs:pattern`/`length`/`enumeration` facets, or only as documentation annotations that an implementation must still enforce itself — noted below):

1. Instance-ID is a GUID, **uppercase hex, 32 chars, without dashes** — enforced structurally by the XSD pattern `[A-F0-9]{32}`.
2. Page number (`@a`) starts at 1 for multi-page plans; **must be omitted entirely for single-page plans** (`@a`/`@z` are both `use="optional"`; the "must omit for single-page" / "must be present for multi-page" constraint is documentation-only, not structurally enforced).
3. Page number ≤ total page count (documentation-only; `@a` range is 1–5, `@z` range is 2–5, but the ≤ relationship itself isn't structurally enforced).
4. Patient identity fields (Versicherten-ID, name parts, DOB) follow eGK/VSDM formats; eGK values preferred when available. `@egk` pattern `[A-Z]\d{9}`, `@b` pattern enforces a real calendar month/day or `00` placeholders for foreign patients.
5. **Sex must never be auto-populated by software** — always an explicit user choice (documentation-only; XSD just allows `@s` enum M|W|X|D, optional).
6. At most **one** of LANR / Apotheken-IDF / Krankenhaus-IK may be present on `<A>` (documentation-only — the XSD does not use `xs:choice` here, so this is **not** structurally enforced and must be validated by application code).
7. Every reprint gets a **new Instance-ID and new print timestamp** (documentation-only).
8. From the 2nd block onward, a heading (`@c` xor `@t`) is mandatory; a block may have **either** a coded or free-text heading, never both (mutual exclusivity is documentation-only, not an XSD `xs:choice` — must be app-validated).
9. PZNs are transmitted with leading zeros stripped — structurally enforced via `xs:int` range `[1, 99999999]` on `M/@p`.
10. Coded dosage form (`@f`) and free-text dosage form (`@fd`) are mutually exclusive per entry (documentation-only).
11. Dosing scheme is **either** the structured 4-slot scheme (`@m`/`@d`/`@v`/`@h`, each matching `dosierungTyp`) **or** free text (`@t`) — never mixed (documentation-only).
12. Dose unit is either coded (`@du`, pattern `[#0-9a-v]`) or free text (`@dud`, 2–20 chars), never both (documentation-only, but `@du`'s pattern does structurally constrain it to a single character from a 33-symbol alphabet).
13. Weekday values (`@wo`) are structurally restricted to enum 1–7 (Mon–Sun); the "requires at least one of m/d/v/h" and "excludes bound continuation line `@x`" constraints are documentation-only.
14. Free-text fields with line-break support are capped at 1–2 embedded `~` characters depending on the field — **documentation-only in the XSD** (the string-length facets don't count tildes specifically); must be enforced in application code.

**Practical implication for implementation**: a large share of the BMP's actual business rules live only in XSD `<xs:documentation>` annotations, not in machine-checkable schema constructs (no `xs:choice`/`xs:key`/`xs:assert` used for the cross-attribute mutual-exclusivity and conditional-requirement rules). An XSD-valid document is **necessary but not sufficient** for BMP conformance — our own import/export code must independently re-implement these documented constraints.

## 11. Relevance to the existing `LabValue` / `MedicationSchedule` models (flag for next step)

- The BMP's **medication entries** map fairly directly onto something like a `MedicationSchedule` concept: substance(s), strength(s), dosage form, a structured W-X-Y-Z (or weekly, or free-text) dosing scheme, dose unit, notes, and treatment reason — plus PZN as an external drug-catalog key.
- The BMP's **parameter block** (weight, height, creatinine, pregnant, breastfeeding, sex, allergies) is **not** a general lab-value model — it's exactly 3 numeric clinical values (weight/height/creatinine) plus boolean/categorical patient attributes, entered manually at print time, explicitly **never auto-populated** from stored patient data. If we want BMP-import/export to interoperate with our `LabValue` model, we'll need to decide: (a) treat these 3 values as a thin, special-cased subset mapped to specific LabValue types/units on import, and (b) decide whether pregnant/breastfeeding/sex/allergies belong in a patient-demographics model rather than `LabValue` at all.
- `MedicationSchedule` compatibility will mainly be about the dosing-scheme representation (today's model vs. the mandatory 4-slot / weekly-via-`@wo` / free-text trichotomy, with the `dosierungTyp` value grammar) and whether we store/round-trip a PZN-keyed vs. free-text substance identity, since the spec treats those as mutually exclusive, order-correlated, and bound by strict mutual-exclusivity + line-break + length constraints.
- Import/export of the **2D barcode carrier XML** is the actual interoperability surface (that's what other systems exchange) — not the print layout — and is now fully specified by `bmp_V2.8.xsd` (§9.1).
- Still missing: the actual Anhang 4 (Dosiereinheit) code table mapping each of the 33 `[#0-9a-v]` single-char codes to its display name/unit — needed to round-trip dose units; not present in any of the four source documents (only referenced by OID/URL).

## 12. Open items to resolve before implementation planning

1. Obtain the published Dosiereinheiten keyword table (`S_BMP_DOSIEREINHEIT`, OID `1.2.276.0.76.3.1.1.5.2.41`) from KBV's `schluesseltabellen.asp` service to map each single-character `@du` code to its unit name — this is the one remaining externally-sourced table we don't have in the repo yet (the Zwischenüberschrift codes are now fully confirmed in the XSD, see §5.4).
2. Decide how/whether the 3 BMP clinical parameters (weight, height, creatinine) and the pregnant/breastfeeding/sex/allergy attributes should round-trip through our `LabValue` model vs. a separate patient-demographics concept.
3. Decide how our current dosing-schedule representation maps onto the confirmed 4-slot (`m`/`d`/`v`/`h`, `dosierungTyp`-constrained) / weekly (`wo` + 4-slot) / free-text (`t`) trichotomy on `<M>`.
4. Decide how/whether to model PZN as a first-class external drug identifier on `MedicationSchedule`, including the "data minimization" convention (PZN present ⇒ other fields typically omitted and derived from a drug DB) and the combination-product (`Mehrkomponentenpräparat`/`Kombipräparat` with >3 substances, ≤3 `<W>` elements) special cases.
5. Since many BMP business rules (mutual exclusivity, conditional requirements, tilde-count caps) live only in XSD documentation and are **not** machine-enforced by the schema itself, our own validation layer needs to re-implement them explicitly rather than relying on XSD validation alone.
