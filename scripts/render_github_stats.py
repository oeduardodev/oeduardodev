#!/usr/bin/env python3
"""Gera gráficos SVG locais a partir da API pública do GitHub.

Sem dependências externas: funciona no GitHub Actions com Python 3.12.
Use --placeholder apenas para criar arquivos iniciais, sem dados inventados.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, timedelta
from html import escape
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parent.parent / 'assets'
BASE = '#080808'
SURFACE = '#111113'
TEXT = '#f5f5f5'
MUTED = '#b7b7bd'
LINE = '#262627'
ACCENT = '#c61a2b'
PALE = '#e6a0a6'
LEVELS = ('#1d1d20', '#54131d', '#861625', '#b51a2b', '#e0404b')
MONO = 'JetBrains Mono, Consolas, Menlo, monospace'


def api(path: str, token: str, *, payload: dict | None = None):
    url = 'https://api.github.com/' + path.lstrip('/')
    headers = {'Accept': 'application/vnd.github+json',
               'User-Agent': 'github-profile-chart-generator',
               'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    req = Request(url, data=data, headers=headers, method='POST' if data else 'GET')
    with urlopen(req, timeout=22) as resp:
        return json.load(resp)


def text(x, y, value, size=18, fill=TEXT, weight='normal', *, anchor='start'):
    return (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
            f'{escape(str(value))}</text>')


def svg(contents: list[str], w: int, h: int, title: str):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title>'
            f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="15" fill="{BASE}" '
            f'stroke="{LINE}" stroke-width="2"/>'
            + ''.join(contents) + '</svg>')


def save(name, markup):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(markup + '\n', encoding='utf-8')
    print('saved', path)


def overview(public_repos=None, stars=None, contributions=None, *, pending=False):
    p = [text(28, 42, 'GITHUB / VISÃO GERAL', 19, ACCENT, 'bold'),
         f'<line x1="28" y1="60" x2="592" y2="60" stroke="{LINE}"/>']
    values = [public_repos, stars, contributions]
    labels = ['REPOSITÓRIOS', 'ESTRELAS', 'CONTRIBUIÇÕES 12M']
    for i, (lab, value) in enumerate(zip(labels, values)):
        x = 28 + 194 * i
        p.append(text(x, 116, '—' if value is None else f'{value:,}'.replace(',', '.'), 34, TEXT, 'bold'))
        p.append(text(x, 145, lab, 13, MUTED))
    if pending:
        footer = 'Aguardando primeira execução do GitHub Actions'
    else:
        footer = 'Dados de repositórios públicos; contribuições via GitHub API'
    p.append(f'<line x1="28" y1="179" x2="592" y2="179" stroke="{LINE}"/>')
    p.append(text(28, 206, footer, 12, MUTED))
    return svg(p, 620, 235, 'Estatísticas públicas do GitHub')


def languages_card(languages: Counter, *, pending=False):
    p = [text(28, 42, 'GITHUB / LINGUAGENS', 19, ACCENT, 'bold'),
         f'<line x1="28" y1="60" x2="592" y2="60" stroke="{LINE}"/>']
    top = languages.most_common(5)
    if not top:
        p.append(text(28, 111, 'Aguardando sincronização' if pending else 'Sem dados de linguagens públicas', 17, TEXT))
        p.append(text(28, 143, 'O gráfico é criado automaticamente pelo workflow.', 12, MUTED))
    else:
        biggest = max(v for _, v in top)
        for i, (lang, total) in enumerate(top):
            y = 86 + i * 27
            p.append(text(28, y, lang[:15], 13, TEXT))
            p.append(f'<rect x="215" y="{y-11}" width="355" height="9" rx="4" fill="{LINE}"/>')
            p.append(f'<rect x="215" y="{y-11}" width="{max(3, int(355*total/biggest))}" height="9" rx="4" fill="{ACCENT}"/>')
    p.append(text(28, 217, 'Volume de código nos repositórios públicos', 11, MUTED))
    return svg(p, 620, 235, 'Linguagens dos repositórios públicos')


def contribution_card(days: dict[str, int], total=None, *, pending=False, source='12 meses'):
    w, h = 1260, 288
    p = [text(28, 42, 'GITHUB / ATIVIDADE', 21, ACCENT, 'bold'),
         text(1230, 42, f'{total:,} contribuições'.replace(',', '.') if total is not None else 'Sincronização pendente', 15, MUTED, anchor='end'),
         f'<line x1="28" y1="61" x2="1232" y2="61" stroke="{LINE}"/>']
    today = date.today()
    # Exibe um calendário de 52 semanas, alinhado ao domingo.
    end = today
    start = end - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)
    x0, y0, step, side = 44, 100, 18, 12
    week_index = 0
    current = start
    while current <= end:
        dow = (current.weekday() + 1) % 7
        week_index = (current - start).days // 7
        value = days.get(current.isoformat(), 0)
        if value == 0:
            color = LEVELS[0]
        elif value == 1:
            color = LEVELS[1]
        elif value <= 3:
            color = LEVELS[2]
        elif value <= 6:
            color = LEVELS[3]
        else:
            color = LEVELS[4]
        x, y = x0 + week_index * 21, y0 + dow * step
        p.append(f'<rect x="{x}" y="{y}" width="{side}" height="{side}" rx="2" fill="{color}"/>')
        current += timedelta(days=1)
    if pending:
        # A grade cinza é apenas um espaço reservado, não são contribuições reais.
        p.append(text(630, 197, 'Dados disponíveis após a primeira atualização', 16, TEXT, anchor='middle'))
    p.extend([text(44, 260, f'Calendário de atividade pública / {source}', 12, MUTED),
              text(1230, 260, 'MENOS  ·  MAIS', 12, PALE, anchor='end')])
    return svg(p, w, h, 'Calendário de contribuições públicas do GitHub')


def fetch_public_repos(username: str, token: str) -> list[dict]:
    found = []
    for page in range(1, 11):
        batch = api(f'users/{username}/repos?type=owner&sort=updated&per_page=100&page={page}', token)
        if not isinstance(batch, list):
            raise RuntimeError('Formato inesperado de repositórios')
        found.extend(repo for repo in batch if not repo.get('private'))
        if len(batch) < 100:
            break
    return found


def fetch_contributions(username: str, token: str):
    if not token:
        return None
    q = '''query($login: String!) {
        user(login: $login) { contributionsCollection {
          contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
        } }
    }'''
    try:
        result = api('graphql', token, payload={'query': q, 'variables': {'login': username}})
        if result.get('errors'):
            raise RuntimeError(str(result['errors'])[:200])
        cal = result['data']['user']['contributionsCollection']['contributionCalendar']
        days = {d['date']: d['contributionCount'] for week in cal['weeks'] for d in week['contributionDays']}
        return cal['totalContributions'], days, '12 meses'
    except (HTTPError, URLError, RuntimeError, KeyError, TypeError) as exc:
        print(f'GitHub GraphQL indisponível ({exc}); usando eventos públicos como alternativa.', file=sys.stderr)
        return None


def fetch_public_events(username: str, token: str):
    # Fallback; a API de eventos fornece um histórico mais curto que o calendário anual.
    events = api(f'users/{username}/events/public?per_page=100', token)
    byday = Counter()
    for event in events:
        if 'created_at' in event:
            byday[event['created_at'][:10]] += 1
    return dict(byday)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--placeholder', action='store_true', help='Criar SVGs iniciais sem dados falsos')
    args = parser.parse_args()
    if args.placeholder:
        save('github-overview.svg', overview(pending=True))
        save('github-languages.svg', languages_card(Counter(), pending=True))
        save('github-activity.svg', contribution_card({}, pending=True))
        return

    username = os.environ.get('GH_USERNAME', 'oeduardodev')
    token = os.environ.get('GITHUB_TOKEN', '')
    user = api(f'users/{username}', token)
    repos = fetch_public_repos(username, token)
    public_repos = user.get('public_repos', len(repos))
    stars = sum(r.get('stargazers_count', 0) for r in repos)
    languages = Counter()
    # Os 60 repositórios públicos mais recentemente modificados refletem a stack atual.
    for repo in repos[:60]:
        try:
            langs = api(f"repos/{repo['full_name']}/languages", token)
            languages.update({k: int(v) for k, v in langs.items()})
        except (HTTPError, URLError, ValueError, TypeError) as exc:
            print(f'Linguagens de {repo.get("name", "?")}: {exc}', file=sys.stderr)
    contribution_data = fetch_contributions(username, token)
    if contribution_data:
        total, days, source = contribution_data
    else:
        try:
            days = fetch_public_events(username, token)
            source = 'eventos públicos recentes (histórico limitado)'
        except (HTTPError, URLError, TypeError) as exc:
            print(f'Eventos públicos indisponíveis: {exc}', file=sys.stderr)
            days = {}
            source = 'dados temporariamente indisponíveis'
        total = None
    # Só escreve quando todos os arquivos foram montados com dados confiáveis.
    save('github-overview.svg', overview(public_repos, stars, total))
    save('github-languages.svg', languages_card(languages))
    save('github-activity.svg', contribution_card(days, total, source=source))


if __name__ == '__main__':
    main()
