from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from textwrap import wrap


OUTPUT_DIR = Path(__file__).resolve().parent


PALETTE = {
    "ink": "#0f172a",
    "muted": "#475569",
    "blue": "#dbeafe",
    "blue_border": "#60a5fa",
    "green": "#dcfce7",
    "green_border": "#4ade80",
    "amber": "#fef3c7",
    "amber_border": "#f59e0b",
    "rose": "#ffe4e6",
    "rose_border": "#fb7185",
    "violet": "#ede9fe",
    "violet_border": "#8b5cf6",
    "teal": "#ccfbf1",
    "teal_border": "#14b8a6",
}


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


@dataclass(frozen=True)
class Box:
    x: float
    y: float
    w: float
    h: float
    title: str
    body: str
    face: str
    edge: str


@dataclass(frozen=True)
class Arrow:
    x1: float
    y1: float
    x2: float
    y2: float
    label: str | None = None
    label_dy: float = -10
    color: str = PALETTE["muted"]


def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" fill="none">\n'
        "<defs>\n"
        '<filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">\n'
        '<feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#0f172a" flood-opacity="0.10"/>\n'
        "</filter>\n"
        '<marker id="arrowhead" markerWidth="10" markerHeight="8" refX="8" refY="4" orient="auto">\n'
        f'<polygon points="0 0, 10 4, 0 8" fill="{PALETTE["muted"]}"/>\n'
        "</marker>\n"
        "</defs>\n"
    )


def text_lines(
    *,
    x: float,
    y: float,
    text: str,
    size: int,
    color: str,
    width: int,
    line_height: int,
    anchor: str = "start",
    weight: str | None = None,
) -> str:
    lines = wrap(text, width=width) or [""]
    weight_attr = f' font-weight="{weight}"' if weight else ""
    return "\n".join(
        f'<text x="{x}" y="{y + index * line_height}" text-anchor="{anchor}" '
        f'font-size="{size}"{weight_attr} fill="{color}" '
        f'font-family="Inter, Arial, sans-serif">{esc(line)}</text>'
        for index, line in enumerate(lines)
    ) + "\n"


def draw_title(title: str, subtitle: str) -> str:
    return (
        text_lines(
            x=44,
            y=54,
            text=title,
            size=28,
            color=PALETTE["ink"],
            width=72,
            line_height=32,
            weight="700",
        )
        + text_lines(
            x=44,
            y=88,
            text=subtitle,
            size=14,
            color=PALETTE["muted"],
            width=118,
            line_height=18,
        )
    )


def draw_box(box: Box) -> str:
    title_width = max(18, int(box.w / 9.2))
    body_width = max(24, int(box.w / 7.5))
    body_y = box.y + 62
    return (
        f'<rect x="{box.x}" y="{box.y}" width="{box.w}" height="{box.h}" rx="16" '
        f'fill="{box.face}" stroke="{box.edge}" stroke-width="2" filter="url(#shadow)"/>\n'
        + text_lines(
            x=box.x + 20,
            y=box.y + 30,
            text=box.title,
            size=16,
            color=PALETTE["ink"],
            width=title_width,
            line_height=19,
            weight="700",
        )
        + text_lines(
            x=box.x + 20,
            y=body_y,
            text=box.body,
            size=13,
            color=PALETTE["ink"],
            width=body_width,
            line_height=18,
        )
    )


def draw_arrow(arrow: Arrow) -> str:
    parts = [
        f'<line x1="{arrow.x1}" y1="{arrow.y1}" x2="{arrow.x2}" y2="{arrow.y2}" '
        f'stroke="{arrow.color}" stroke-width="2.4" marker-end="url(#arrowhead)"/>\n'
    ]
    if arrow.label:
        mid_x = (arrow.x1 + arrow.x2) / 2
        mid_y = (arrow.y1 + arrow.y2) / 2 + arrow.label_dy
        parts.append(
            f'<text x="{mid_x}" y="{mid_y}" text-anchor="middle" font-size="12" '
            f'fill="{arrow.color}" font-family="Inter, Arial, sans-serif">{esc(arrow.label)}</text>\n'
        )
    return "".join(parts)


def draw_footer(text: str, width: int, y: int) -> str:
    return text_lines(
        x=width / 2,
        y=y,
        text=text,
        size=13,
        color=PALETTE["muted"],
        width=150,
        line_height=18,
        anchor="middle",
    )


def write_svg(path: Path, width: int, height: int, content: list[str]) -> Path:
    svg = [
        svg_header(width, height),
        f'<rect width="{width}" height="{height}" fill="white"/>\n',
        *content,
        "</svg>\n",
    ]
    path.write_text("".join(svg), encoding="utf-8")
    return path


def render_compile_export_flow() -> Path:
    width, height = 1500, 900
    boxes = [
        Box(50, 145, 260, 175, "1. YAML-Module", "Report-Templates, Sektionen, Findings und Validatoren werden als versionierte YAML-Daten gepflegt.", PALETTE["blue"], PALETTE["blue_border"]),
        Box(380, 145, 260, 175, "2. DataLoader", "Findet Modulkonfigurationen und baut pro Modul eine KnowledgeBase im Speicher auf.", PALETTE["teal"], PALETTE["teal_border"]),
        Box(710, 145, 260, 175, "3. Typisierte Modelle", "Der Parser wählt über model=... das Pydantic-Modell und validiert jeden YAML-Eintrag.", PALETTE["violet"], PALETTE["violet_border"]),
        Box(1040, 145, 330, 175, "4. KnowledgeBase", "Speichert Templates, Sektionen, Report-Findings und Validatoren in benannten Registern.", PALETTE["green"], PALETTE["green_border"]),
        Box(210, 510, 350, 180, "5. Strukturprüfung", "Prüft Referenzen, Graph-Struktur, Publikationsreife und Preview-Fähigkeit.", PALETTE["amber"], PALETTE["amber_border"]),
        Box(650, 510, 300, 180, "6. Compiler", "Löst Sektionen, Finding-Anforderungen und Validatoren zu einem JSON-Baum auf.", PALETTE["blue"], PALETTE["blue_border"]),
        Box(1040, 510, 350, 180, "7. Export", "Preview exportiert Entwürfe. Produktion exportiert nur veröffentlichte und freigegebene Templates.", PALETTE["rose"], PALETTE["rose_border"]),
    ]
    arrows = [
        Arrow(310, 232, 380, 232, "finden"),
        Arrow(640, 232, 710, 232, "parsen"),
        Arrow(970, 232, 1040, 232, "registrieren"),
        Arrow(1205, 320, 385, 510, "validieren", label_dy=-16),
        Arrow(560, 600, 650, 600, "kompilieren"),
        Arrow(950, 600, 1040, 600, "ausliefern"),
    ]
    content = [
        draw_title(
            "Report-Template: Kompilierung und Export",
            "Vom YAML-Modul zur typisierten KnowledgeBase, validierten Struktur und JSON-Ausgabe für Frontend und API.",
        )
    ]
    content.extend(draw_box(box) for box in boxes)
    content.extend(draw_arrow(arrow) for arrow in arrows)
    content.append(
        draw_footer(
            "Wichtig: Struktur- und Graph-Prüfung bewerten Template-Topologie. Die Prüfung eines echten Berichts gegen PExamination läuft separat.",
            width,
            820,
        )
    )
    return write_svg(OUTPUT_DIR / "report_template_compile_export_flow.svg", width, height, content)


def render_builder_publish_flow() -> Path:
    width, height = 1500, 900
    boxes = [
        Box(50, 150, 300, 165, "Generator: Speichern", "Der Generator schreibt eine neue Template-Definition als YAML in ein Wissensbasis-Modul.", PALETTE["blue"], PALETTE["blue_border"]),
        Box(410, 150, 280, 165, "Datei + Cache", "Nach dem Schreiben werden Caches geleert und das Modul frisch geladen.", PALETTE["teal"], PALETTE["teal_border"]),
        Box(750, 150, 280, 165, "Vorschau-Prüfung", "validate_and_compile(mode='preview') erzeugt Vorschau, Readiness und Hinweise.", PALETTE["amber"], PALETTE["amber_border"]),
        Box(1090, 150, 300, 165, "Entwurfsstatus", "Das Template bleibt Entwurf, bis es explizit veröffentlicht wird.", PALETTE["rose"], PALETTE["rose_border"]),
        Box(230, 515, 310, 175, "Veröffentlichungs-Endpoint", "Kompiliert im Veröffentlichungsmodus.", PALETTE["violet"], PALETTE["violet_border"]),
        Box(620, 515, 290, 175, "Aktualisierbarer Lebenszyklus", "Setzt den gespeicherten Status auf published und leert die KB-Caches erneut.", PALETTE["green"], PALETTE["green_border"]),
        Box(990, 515, 400, 175, "Produktionsfreigabe", "Produktions-Export ist nur für published Templates ohne blockierende Issues möglich.", PALETTE["blue"], PALETTE["blue_border"]),
    ]
    arrows = [
        Arrow(350, 232, 410, 232, "schreiben"),
        Arrow(690, 232, 750, 232, "neu laden"),
        Arrow(1030, 232, 1090, 232, "Vorschau"),
        Arrow(1240, 315, 385, 515, "Veröffentlichung anstoßen", label_dy=-16),
        Arrow(540, 602, 620, 602, "freigeben"),
        Arrow(910, 602, 990, 602, "exportierbar"),
    ]
    content = [
        draw_title(
            "Report-Template: Builder und Veröffentlichung",
            "Der Lebenszyklus vom gespeicherten YAML-Entwurf über Readiness-Prüfung bis zur produktiven Veröffentlichung.",
        )
    ]
    content.extend(draw_box(box) for box in boxes)
    content.extend(draw_arrow(arrow) for arrow in arrows)
    content.append(
        draw_footer(
            "Wenn can_publish false ist, antwortet die Publish-Route mit 409. Unpublish setzt den Lifecycle zurück auf Entwurf.",
            width,
            820,
        )
    )
    return write_svg(OUTPUT_DIR / "report_template_builder_publish_flow.svg", width, height, content)


def render_runtime_validation_flow() -> Path:
    width, height = 1500, 900
    boxes = [
        Box(50, 150, 280, 170, "Client-Payload", "Frontend oder Host-Django sendet einen Bericht oder fordert Validierung aus dem Ledger an.", PALETTE["blue"], PALETTE["blue_border"]),
        Box(390, 150, 280, 170, "PExamination", "Der Bericht wird in eine typisierte PExamination-Struktur überführt.", PALETTE["teal"], PALETTE["teal_border"]),
        Box(730, 150, 300, 170, "KB-Auflösung", "Modul und optionale Version werden bestimmt; die passende KnowledgeBase wird geladen.", PALETTE["violet"], PALETTE["violet_border"]),
        Box(1090, 150, 320, 170, "Produktions-Template", "export_report_template stellt sicher, dass das Template veröffentlicht und freigegeben ist.", PALETTE["amber"], PALETTE["amber_border"]),
        Box(210, 515, 360, 180, "Semantische Zulässigkeit", "Prüft, ob Untersuchung, Findings und Anforderungen zum gewählten Template passen.", PALETTE["rose"], PALETTE["rose_border"]),
        Box(650, 515, 320, 180, "Validator-Ausführung", "Findings-, Klassifikations-, Interventions-, Unit- und Examination-Validatoren laufen gegen Runtime-Daten.", PALETTE["green"], PALETTE["green_border"]),
        Box(1050, 515, 360, 180, "Ergebnis oder Fehler", "Erfolg liefert Validator-Ergebnisse. Semantikfehler werden 422, fehlende Templates 404.", PALETTE["blue"], PALETTE["blue_border"]),
    ]
    arrows = [
        Arrow(330, 235, 390, 235, "normalisieren"),
        Arrow(670, 235, 730, 235, "Version wählen"),
        Arrow(1030, 235, 1090, 235, "Template laden"),
        Arrow(1250, 320, 420, 515, "Runtime-Prüfung", label_dy=-16),
        Arrow(570, 605, 650, 605, "ausführen"),
        Arrow(970, 605, 1050, 605, "antworten"),
    ]
    content = [
        draw_title(
            "Report-Template: Runtime-Validierung",
            "Produktiver Prüfpfad für einen echten Bericht: KnowledgeBase auflösen, Zulässigkeit prüfen, Validatoren ausführen.",
        )
    ]
    content.extend(draw_box(box) for box in boxes)
    content.extend(draw_arrow(arrow) for arrow in arrows)
    content.append(
        draw_footer(
            "Dieser Pfad nutzt eine aufgelöste produktive KnowledgeBase. Er arbeitet nicht direkt auf rohen YAML-Dateien.",
            width,
            820,
        )
    )
    return write_svg(OUTPUT_DIR / "report_template_runtime_validation_flow.svg", width, height, content)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = [
        render_compile_export_flow(),
        render_builder_publish_flow(),
        render_runtime_validation_flow(),
    ]
    for output in outputs:
        print(output)


if __name__ == "__main__":
    main()
