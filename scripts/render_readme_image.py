"""Generate the standalone, dark SVG version of the profile README.

The visual copy is intentionally composed here; keep its profile text aligned with
README-texto.md when updating the biography or work history.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "readme-completo.svg"
WIDTH = 1200
MARGIN = 32
CARD_WIDTH = WIDTH - MARGIN * 2
CONTENT_X = 62
CONTENT_WIDTH = WIDTH - CONTENT_X * 2
BG = "#080808"
FG = "#f5f5f5"
MUTED = "#b7b7bd"
ACCENT = "#c61a2b"
BORDER = "#262627"
BLUE = "#58a6ff"
FONT_FAMILY = "JetBrains Mono, Consolas, Menlo, monospace"
FONT_DIR = Path(r"C:\Windows\Fonts")


def load_font(size: int, windows_name: str, linux_name: str) -> ImageFont.FreeTypeFont:
    candidates = [FONT_DIR / windows_name, Path("/usr/share/fonts/truetype/dejavu") / linux_name]
    for candidate in candidates:
        if candidate.exists():
            try:
                return ImageFont.truetype(str(candidate), size)
            except OSError:
                pass
    return ImageFont.load_default(size=size)


REGULAR = load_font(19, "consola.ttf", "DejaVuSansMono.ttf")
SMALL = load_font(17, "consola.ttf", "DejaVuSansMono.ttf")
MONO = load_font(16, "consola.ttf", "DejaVuSansMono.ttf")
SVG_NS = "{http://www.w3.org/2000/svg}"


def text_svg(text: str, x: float, y: float, *, size: int = 19, color: str = FG,
             weight: int = 400, family: str = FONT_FAMILY,
             anchor: str = "start", spacing: float | None = None) -> str:
    letter_spacing = f' letter-spacing="{spacing}px"' if spacing is not None else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}px" '
            f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{letter_spacing}>'
            f'{escape(text)}</text>')


def wrap_words(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = word if not current else f"{current} {word}"
        if current and font.getlength(candidate) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


class Section:
    def __init__(self, y: int, number: str, title: str):
        self.y = y
        self.number = number
        self.title = title
        self.cursor = 77
        self.children: list[str] = [
            text_svg(f"{number}  /  {title}", CONTENT_X, y + 45, size=27,
                     color=ACCENT, weight=700, family=FONT_FAMILY),
            f'<line x1="{CONTENT_X}" y1="{y + 57}" x2="{WIDTH - CONTENT_X}" '
            f'y2="{y + 57}" stroke="{BORDER}" stroke-width="1" />',
        ]

    def paragraph(self, text: str, *, color: str = FG, size: int = 19,
                  gap: int = 14, left: int = CONTENT_X, width: int = CONTENT_WIDTH) -> None:
        font = REGULAR if size >= 19 else SMALL
        lines = wrap_words(text, font, width)
        line_height = 29 if size >= 19 else 26
        for line in lines:
            self.children.append(text_svg(line, left, self.y + self.cursor, size=size, color=color))
            self.cursor += line_height
        self.cursor += gap

    def subheading(self, text: str) -> None:
        self.children.append(text_svg(text, CONTENT_X, self.y + self.cursor,
                                      size=21, color=FG, weight=700))
        self.cursor += 38

    def code_block(self, lines: list[str]) -> None:
        line_height = 26
        box_height = 38 + len(lines) * line_height
        self.children.append(
            f'<rect x="{CONTENT_X}" y="{self.y + self.cursor - 18}" width="{CONTENT_WIDTH}" '
            f'height="{box_height}" rx="9" fill="{BG}" stroke="{BORDER}" stroke-width="1" />'
        )
        code_y = self.y + self.cursor + 8
        for line in lines:
            self.children.append(text_svg(line, CONTENT_X + 18, code_y, size=17,
                                          color=FG, family=FONT_FAMILY))
            code_y += line_height
        self.cursor += box_height + 16

    def badges(self, labels: list[str]) -> None:
        x = CONTENT_X
        y = self.y + self.cursor - 18
        max_x = WIDTH - CONTENT_X
        for label in labels:
            pill_width = int(MONO.getlength(label.upper())) + 48
            if x + pill_width > max_x:
                x = CONTENT_X
                y += 39
            self.children.append(
                f'<rect x="{x}" y="{y}" width="{pill_width}" height="34" rx="7" '
                f'fill="{BG}" stroke="{BORDER}" stroke-width="1" />'
            )
            self.children.append(
                f'<circle cx="{x + 14}" cy="{y + 17}" r="4.5" fill="{ACCENT}" />'
            )
            self.children.append(text_svg(label.upper(), x + 28, y + 23, size=15,
                                          color=FG, family=FONT_FAMILY))
            x += pill_width + 10
        self.cursor += (y - (self.y + self.cursor - 18)) + 47

    def finish(self) -> tuple[int, list[str]]:
        height = self.cursor + 10
        rect = (f'<rect x="{MARGIN}" y="{self.y}" width="{CARD_WIDTH}" height="{height}" '
                f'rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="1" />')
        return height, [rect, *self.children]


def add_job(section: Section, period: str, role: str, description: str) -> None:
    desc_lines = wrap_words(description, REGULAR, CONTENT_WIDTH - 48)
    top = section.y + section.cursor - 17
    box_height = 83 + (len(desc_lines) - 1) * 27
    section.children.append(
        f'<rect x="{CONTENT_X}" y="{top}" width="{CONTENT_WIDTH}" height="{box_height}" '
        f'rx="9" fill="{BG}" stroke="{BORDER}" stroke-width="1" />'
    )
    section.children.append(text_svg(period, CONTENT_X + 18, top + 29, size=17,
                                     color=ACCENT, weight=700, family=FONT_FAMILY))
    section.children.append(text_svg(role, CONTENT_X + 150, top + 29, size=19,
                                     color=FG, weight=700))
    line_y = top + 58
    for line in desc_lines:
        section.children.append(text_svg(line, CONTENT_X + 18, line_y, size=18, color=MUTED))
        line_y += 26
    section.cursor += box_height + 15


def add_metric_card(x: int, y: int, width: int, title: str, metrics: list[tuple[str, str]]) -> list[str]:
    parts = [
        f'<rect x="{x}" y="{y}" width="{width}" height="225" rx="10" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="1" />',
        text_svg(title, x + 20, y + 36, size=19, color=ACCENT, weight=700,
                 family=FONT_FAMILY),
        f'<line x1="{x + 20}" y1="{y + 52}" x2="{x + width - 20}" '
        f'y2="{y + 52}" stroke="{BORDER}" />',
    ]
    col_width = (width - 40) / max(1, len(metrics))
    for idx, (value, label) in enumerate(metrics):
        col_x = x + 20 + idx * col_width
        parts.append(text_svg(value, col_x, y + 115, size=40, color=FG, weight=700))
        parts.append(text_svg(label, col_x, y + 147, size=14, color=MUTED,
                              family=FONT_FAMILY))
    parts.append(text_svg("REPOSITÓRIOS PÚBLICOS / DADOS DO PERFIL", x + 20, y + 183,
                          size=13, color=MUTED, family=FONT_FAMILY))
    return parts


def read_profile_stats() -> tuple[list[tuple[str, str]], list[tuple[str, float]]]:
    overview = ET.parse(ROOT / "assets" / "github-overview.svg").getroot()
    values = [node.text or "—" for node in overview.iter()
              if node.tag == f"{SVG_NS}text" and node.get("y") == "116"]
    labels = ["REPOSITÓRIOS", "ESTRELAS", "CONTRIBUIÇÕES 12M"]
    metrics = list(zip(values[:3], labels))
    while len(metrics) < 3:
        metrics.append(("—", labels[len(metrics)]))

    languages_root = ET.parse(ROOT / "assets" / "github-languages.svg").getroot()
    row_positions = {str(86 + 27 * index) for index in range(5)}
    names = [node.text or "" for node in languages_root.iter()
             if node.tag == f"{SVG_NS}text" and node.get("x") == "28"
             and node.get("y") in row_positions]
    widths = {
        node.get("y", ""): float(node.get("width", "3")) / 355
        for node in languages_root.iter()
        if node.tag == f"{SVG_NS}rect" and node.get("x") == "215"
        and node.get("fill") == ACCENT
    }
    rows = [(name, widths.get(str(75 + 27 * index), 0.01))
            for index, name in enumerate(names)]
    if not rows:
        rows = [("Aguardando sincronização", 0.01)]
    return metrics, rows


def add_language_card(x: int, y: int, width: int,
                      langs: list[tuple[str, float]]) -> list[str]:
    parts = [
        f'<rect x="{x}" y="{y}" width="{width}" height="220" rx="10" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="1" />',
        text_svg("GITHUB / LINGUAGENS", x + 20, y + 36, size=19, color=ACCENT,
                 weight=700, family=FONT_FAMILY),
        f'<line x1="{x + 20}" y1="{y + 52}" x2="{x + width - 20}" '
        f'y2="{y + 52}" stroke="{BORDER}" />',
    ]
    bar_x, bar_width = x + 170, width - 195
    row_y = y + 80
    for name, ratio in langs[:5]:
        parts.append(text_svg(name, x + 20, row_y + 4, size=15, color=FG))
        parts.append(f'<rect x="{bar_x}" y="{row_y - 8}" width="{bar_width}" height="8" '
                     f'rx="4" fill="{BORDER}" />')
        parts.append(f'<rect x="{bar_x}" y="{row_y - 8}" width="{max(3, bar_width * ratio):.1f}" '
                     f'height="8" rx="4" fill="{ACCENT}" />')
        row_y += 28
    return parts


elements: list[str] = []
y = 28

# Header card
header_height = 430
elements.append(
    f'<rect x="{MARGIN}" y="{y}" width="{CARD_WIDTH}" height="{header_height}" '
    f'rx="14" fill="{BG}" stroke="{BORDER}" stroke-width="1" />'
)
elements.append(text_svg("oeduardodev / README.md", CONTENT_X, y + 36, size=15,
                         color=MUTED, family=FONT_FAMILY))
elements.append(text_svg("Eduardo Leite", WIDTH / 2, y + 112, size=56,
                         color=FG, weight=700, anchor="middle"))
elements.append(text_svg("FRONT-END DEVELOPER  |  ANGULAR  |  REACT", WIDTH / 2,
                         y + 153, size=19, color=FG, weight=700,
                         family=FONT_FAMILY, anchor="middle"))
elements.append(f'<line x1="{CONTENT_X}" y1="{y + 173}" x2="{WIDTH - CONTENT_X}" '
                f'y2="{y + 173}" stroke="{BORDER}" />')

links = ["LINKEDIN", "GITHUB", "PORTFÓLIO", "E-MAIL"]
link_widths = [int(MONO.getlength(item)) + 40 for item in links]
gap = 14
total = sum(link_widths) + gap * (len(links) - 1)
link_x = int((WIDTH - total) / 2)
for label, pill_width in zip(links, link_widths):
    elements.append(f'<rect x="{link_x}" y="{y + 190}" width="{pill_width}" height="36" '
                    f'rx="7" fill="{BG}" stroke="{BORDER}" />')
    elements.append(text_svg(label, link_x + pill_width / 2, y + 214, size=15,
                             color=BLUE, family=FONT_FAMILY, anchor="middle"))
    link_x += pill_width + gap

term_y = y + 242
term_height = 172
elements.append(f'<rect x="{CONTENT_X}" y="{term_y}" width="{CONTENT_WIDTH}" '
                f'height="{term_height}" rx="9" fill="{BG}" stroke="{BORDER}" />')
elements.append(text_svg("eduardo@github:~$ profile --summary", CONTENT_X + 20,
                         term_y + 30, size=17, color=ACCENT, weight=700,
                         family=FONT_FAMILY))
summary_lines = [
    "role          Front-end Developer",
    "experience    4 years",
    "focus         Angular / React / TypeScript",
    "location      João Pessoa, PB — Brazil",
    "availability  Open to remote opportunities",
]
for idx, line in enumerate(summary_lines):
    elements.append(text_svg(line, CONTENT_X + 20, term_y + 59 + idx * 23,
                             size=15, color=FG, family=FONT_FAMILY))
y += header_height + 20

# About section
section = Section(y, "01", "SOBRE MIM")
section.paragraph("Sou Eduardo Leite, desenvolvedor Front-end com 4 anos de experiência no desenvolvimento de aplicações web, SPAs, dashboards, ERPs e sistemas corporativos.")
section.paragraph("Minha principal atuação é com Angular, React e TypeScript, desde a criação de interfaces responsivas e componentes reutilizáveis até a integração com APIs REST e o gerenciamento de estado. Também tenho conhecimentos em Node.js, Express, AdonisJS e PostgreSQL, que ampliam minha visão sobre o funcionamento das aplicações de ponta a ponta.")
section.paragraph("No dia a dia, valorizo código bem estruturado, acessibilidade, manutenibilidade, testes e colaboração com o time.", gap=8)
section.code_block([
    "const eduardo = {",
    "  role: 'Front-end Developer',",
    "  experience: '4 anos',",
    "  location: 'João Pessoa, PB',",
    "  mainStack: ['Angular', 'React', 'TypeScript'],",
    "  backend: ['Node.js', 'Express', 'AdonisJS'],",
    "  principles: ['SOLID', 'Acessibilidade', 'Clean Code'],",
    "  availableFor: 'Oportunidades remotas'",
    "} as const;",
])
height, parts = section.finish()
elements.extend(parts)
y += height + 20

# Stack section
section = Section(y, "02", "STACK TECNOLÓGICA")
section.subheading("Front-end")
section.badges(["Angular", "React", "TypeScript", "JavaScript", "HTML5", "CSS3", "SCSS", "Tailwind CSS", "Bootstrap", "Material UI"])
section.paragraph("Estado e reatividade: RxJS · NgRx · Angular Signals · Computed · React Hooks · Context API", color=MUTED, size=17, gap=18)
section.paragraph("Componentização e UI: Angular Material · Nebular · Styled Components · Design Systems", color=MUTED, size=17, gap=22)

section.subheading("Back-end e bancos de dados")
section.badges(["Node.js", "Express", "AdonisJS", "PostgreSQL", "SQLite", "MySQL"])
section.paragraph("Integração: REST APIs · Axios · Fetch API · SQL", color=MUTED, size=17, gap=20)

section.subheading("Qualidade, ferramentas e processos")
section.badges(["Git", "GitHub", "GitLab", "ESLint", "Postman", "Jest", "Jasmine"])
section.paragraph("Karma · CI/CD · Scrum · Kanban · SOLID · Testes unitários · Bitbucket", color=MUTED, size=17, gap=18)
section.paragraph("Outras tecnologias com as quais tive contato:", color=FG, size=17, gap=5)
section.badges(["Python", "PHP", "Java", "Ionic", "React Native"])
height, parts = section.finish()
elements.extend(parts)
y += height + 20

# Experience section
section = Section(y, "03", "EXPERIÊNCIA PROFISSIONAL")
add_job(section, "2025 — 2026", "Vox Tecnologia · Front-end",
        "Interfaces para ERPs municipais, componentes reutilizáveis, design systems, microfrontends, APIs REST e testes com Jasmine/Karma.")
add_job(section, "2023 — 2025", "Data Core Solutions Services · Front-end",
        "SPAs, dashboards, aplicações responsivas com Angular e React, gerenciamento de estado, acessibilidade e Ionic.")
add_job(section, "2022 — 2023", "CL Importados · Full Stack / Freelance",
        "Interfaces e aplicações comerciais responsivas, integração de APIs e desenvolvimento de serviços com Node.js, Express e AdonisJS.")
section.paragraph("Formação acadêmica: Tecnólogo em Análise e Desenvolvimento de Sistemas — Faculdade VINCIT (2023–2025).", color=MUTED, size=17, gap=9)
height, parts = section.finish()
elements.extend(parts)
y += height + 20

# GitHub section
section = Section(y, "04", "ATIVIDADE NO GITHUB")
grid_y = section.y + section.cursor - 17
gap = 18
grid_width = (CONTENT_WIDTH - gap) // 2
profile_metrics, profile_languages = read_profile_stats()
section.children.extend(add_metric_card(CONTENT_X, grid_y, grid_width,
                                        "GITHUB / VISÃO GERAL",
                                        profile_metrics))
section.children.extend(add_language_card(CONTENT_X + grid_width + gap, grid_y,
                                          grid_width, profile_languages))
section.cursor += 230
section.paragraph("Gráficos armazenados neste repositório e atualizados automaticamente pelo GitHub Actions. As linguagens representam o código de repositórios públicos, não o nível de domínio de cada tecnologia.", color=MUTED, size=17, gap=8)
height, parts = section.finish()
elements.extend(parts)
y += height + 20

# Contact section
section = Section(y, "05", "CONTATO")
section.paragraph("Estou aberto a oportunidades remotas em Front-end, com Angular ou React, e também a desafios Full Stack com Node.js.", gap=9)
section.badges(["ENVIAR E-MAIL", "CONVERSAR NO LINKEDIN"])
section.children.append(text_svg("Eduardo Leite  ·  João Pessoa, PB  ·  Brasil",
                                 WIDTH / 2, section.y + section.cursor + 4,
                                 size=17, color=MUTED, family=FONT_FAMILY,
                                 anchor="middle"))
section.cursor += 25
height, parts = section.finish()
elements.extend(parts)
y += height + 22

footer_y = y
elements.append(text_svg("VERSÃO EM TEXTO COM LINKS INTERATIVOS: README-texto.md",
                         WIDTH / 2, footer_y, size=14, color=MUTED,
                         family=FONT_FAMILY, anchor="middle"))
y += 38

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{y}" viewBox="0 0 {WIDTH} {y}" role="img" aria-labelledby="title desc">',
    '<title id="title">Eduardo Leite — perfil profissional</title>',
    '<desc id="desc">README completo de Eduardo Leite, desenvolvedor Front-end, em fundo preto #080808. O arquivo README-texto.md mantém o conteúdo com links ativos.</desc>',
    f'<rect width="{WIDTH}" height="{y}" fill="{BG}" />',
    *elements,
    '</svg>',
]
OUT.write_text("\n".join(svg) + "\n", encoding="utf-8")
print(f"Gerado {OUT.relative_to(ROOT)} ({WIDTH} x {y})")
