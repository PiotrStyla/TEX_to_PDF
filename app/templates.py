INDEX_HTML = """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TeX → PDF Builder</title>
  <style>
    :root {
      --bg: #f6f7fb;
      --card: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --border: #d1d5db;
      --accent: #2563eb;
      --accent-dark: #1d4ed8;
    }

    * { box-sizing: border-box; }

    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: var(--bg);
      color: var(--text);
    }

    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }

    h1 {
      font-size: 40px;
      margin: 0 0 8px;
      letter-spacing: -0.04em;
    }

    h2 {
      margin-top: 0;
      letter-spacing: -0.02em;
    }

    p {
      line-height: 1.6;
    }

    .lead {
      color: var(--muted);
      font-size: 18px;
      margin-bottom: 28px;
    }

    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 22px;
      align-items: start;
    }

    .box {
      background: var(--card);
      border: 1px solid var(--border);
      padding: 24px;
      border-radius: 16px;
      box-shadow: 0 8px 30px rgba(15, 23, 42, 0.06);
    }

    label {
      display: block;
      font-weight: 650;
      margin: 14px 0 6px;
    }

    input,
    textarea,
    select {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      font: inherit;
      background: #fff;
    }

    input[type="file"] {
      padding: 10px;
    }

    textarea {
      min-height: 260px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 14px;
      line-height: 1.5;
    }

    button,
    .button {
      display: inline-block;
      border: 0;
      border-radius: 10px;
      padding: 11px 16px;
      background: var(--accent);
      color: white;
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      margin-top: 16px;
    }

    button:hover,
    .button:hover {
      background: var(--accent-dark);
    }

    code {
      background: #eef2ff;
      padding: 2px 5px;
      border-radius: 5px;
    }

    pre {
      background: #111827;
      color: #e5e7eb;
      padding: 16px;
      overflow: auto;
      border-radius: 12px;
      line-height: 1.4;
    }

    .hint {
      color: var(--muted);
      font-size: 14px;
      margin-top: 8px;
    }

    .full {
      margin-top: 22px;
    }

    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <h1>TeX → PDF Builder</h1>
    <p class="lead">Wrzuć zwykły plik <code>.tex</code>/<code>.zip</code> albo wygeneruj raport w trybie Slayer Paper Mode.</p>
    <p><a class="button secondary" href="/history">Historia buildów</a></p>

    <div class="grid">
      <section class="box">
        <h2>Plain TeX / ZIP</h2>
        <p>Użyj tego trybu, gdy masz gotowy <code>main.tex</code> albo cały projekt LaTeX spakowany jako ZIP.</p>

        <form action="/compile" method="post" enctype="multipart/form-data">
          <input type="hidden" name="mode" value="plain" />

          <label>Plik .tex albo .zip</label>
          <input type="file" name="file" accept=".tex,.zip" required />

          <button type="submit">Generate PDF</button>
        </form>
      </section>

      <section class="box">
        <h2>Slayer Paper Mode</h2>
        <p>Ten tryb sam tworzy strukturę <code>main.tex</code>, <code>formatka/slayer.sty</code> i <code>tresc/*.tex</code>.</p>

        <form action="/compile-slayer" method="post">
          <label>Nazwa projektu / folderu</label>
          <input name="paper_name" value="pes-com-report" />

          <label>Tytuł</label>
          <input name="title" value="PES-CoM Research Note" />

          <label>Podtytuł</label>
          <input name="subtitle" value="Generated with TeX to PDF Builder" />

          <label>Autor</label>
          <input name="author" value="Piotr Styła" />

          <label>Treść raportu LaTeX</label>
          <textarea name="report_content">\section{Cel}

Ten raport został wygenerowany automatycznie w trybie Slayer Paper Mode.

\section{Wyniki}

\begin{center}
\begin{tabular}{lrr}
\toprule
Model & Change Rate & Wrong Flip Rate \\
\midrule
Llama 3.2 3B & 90.75\% & 22.25\% \\
Gemma 3 1B & 33.75\% & 10.75\% \\
Bielik 11B Q4 & 59.00\% & 37.50\% \\
\bottomrule
\end{tabular}
\end{center}

\section{Wniosek}

Answer change nie jest tym samym co useful belief revision.</textarea>

          <p class="hint">Po sukcesie pobierzesz zarówno PDF, jak i ZIP źródeł LaTeX.</p>

          <button type="submit">Generate Slayer PDF</button>
        </form>
      </section>
    </div>

    <section class="box full">
      <h2>Jak przygotować ZIP?</h2>
      <pre>project.zip
├── main.tex
├── references.bib        opcjonalnie
├── formatka/slayer.sty   opcjonalnie
└── tresc/10-tresc.tex    opcjonalnie</pre>
    </section>
  </main>
</body>
</html>
"""

RESULT_HTML = """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TeX → PDF Result</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: #f6f7fb;
      color: #111827;
    }

    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }

    h1 {
      letter-spacing: -0.03em;
    }

    a.button {
      display: inline-block;
      padding: 10px 16px;
      background: #2563eb;
      color: white;
      border-radius: 10px;
      text-decoration: none;
      margin-right: 8px;
      margin-bottom: 8px;
      font-weight: 700;
    }

    a.button.secondary {
      background: #111827;
    }

    a.button.source {
      background: #047857;
    }

    iframe {
      width: 100%;
      height: 760px;
      border: 1px solid #d1d5db;
      border-radius: 12px;
      background: white;
    }

    pre {
      background: #111827;
      color: #e5e7eb;
      padding: 16px;
      overflow: auto;
      border-radius: 12px;
      line-height: 1.4;
      white-space: pre-wrap;
    }

    .ok {
      color: #0a7b2f;
      font-weight: 800;
    }

    .err {
      color: #a40000;
      font-weight: 800;
    }
  </style>
</head>
<body>
  <main>
    <h1>{{ title }}</h1>

    {% if success %}
      <p class="ok">PDF wygenerowany.</p>
      <p>
        <a class="button" href="/download/{{ job_id }}">Download PDF</a>
        {% if has_source_zip %}
        <a class="button source" href="/download-source/{{ job_id }}">Download TEX source ZIP</a>
        {% endif %}
        <a class="button secondary" href="/">Nowy plik</a>
        <a class="button secondary" href="/history">Historia</a>
        <a class="button secondary" href="/download-log/{{ job_id }}">Download log</a>
      </p>
      <iframe src="/download/{{ job_id }}"></iframe>
    {% else %}
      <p class="err">Kompilacja nie powiodła się.</p>
      <p><a class="button secondary" href="/">Wróć</a></p>
    {% endif %}

    <h2>Log</h2>
    <pre>{{ log }}</pre>
  </main>
</body>
</html>
"""


HISTORY_HTML = """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Build history</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 0;
      background: #f6f7fb;
      color: #111827;
    }

    main {
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 24px 80px;
    }

    h1 { letter-spacing: -0.03em; }

    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      border: 1px solid #d1d5db;
      border-radius: 12px;
      overflow: hidden;
    }

    th, td {
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
      padding: 12px;
      vertical-align: top;
    }

    th { background: #f3f4f6; }

    .ok { color: #0a7b2f; font-weight: 800; }
    .err { color: #a40000; font-weight: 800; }
    .muted { color: #6b7280; font-size: 13px; }

    a.button, a.linkbutton {
      display: inline-block;
      padding: 8px 11px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 700;
      margin: 2px 4px 2px 0;
    }

    a.button {
      background: #111827;
      color: white;
    }

    a.linkbutton {
      background: #eef2ff;
      color: #1d4ed8;
    }

    .empty {
      background: white;
      border: 1px solid #d1d5db;
      padding: 24px;
      border-radius: 12px;
    }
  </style>
</head>
<body>
  <main>
    <h1>Historia buildów</h1>
    <p><a class="button" href="/">Nowy build</a></p>

    {% if builds %}
      <table>
        <thead>
          <tr>
            <th>Czas</th>
            <th>Tryb</th>
            <th>Tytuł / plik</th>
            <th>Status</th>
            <th>Pliki</th>
          </tr>
        </thead>
        <tbody>
          {% for build in builds %}
            <tr>
              <td>{{ build.created_at }}</td>
              <td><code>{{ build.mode }}</code></td>
              <td>
                {{ build.title }}
                <div class="muted">{{ build.job_id }}</div>
              </td>
              <td>
                {% if build.success %}
                  <span class="ok">OK</span>
                {% else %}
                  <span class="err">FAIL</span>
                {% endif %}
              </td>
              <td>
                {% if build.has_pdf %}
                  <a class="linkbutton" href="/download/{{ build.job_id }}">PDF</a>
                {% endif %}
                {% if build.has_source_zip %}
                  <a class="linkbutton" href="/download-source/{{ build.job_id }}">TEX ZIP</a>
                {% endif %}
                {% if build.has_log %}
                  <a class="linkbutton" href="/download-log/{{ build.job_id }}">LOG</a>
                {% endif %}
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <div class="empty">
        Brak historii. Wygeneruj pierwszy PDF.
      </div>
    {% endif %}
  </main>
</body>
</html>
"""
