INDEX_HTML = """
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>TeX → PDF Builder</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 40px; max-width: 900px; }
    .box { border: 1px solid #ddd; padding: 24px; border-radius: 12px; }
    button { padding: 10px 16px; cursor: pointer; }
    input, select { margin: 8px 0 18px; }
    pre { background: #111; color: #eee; padding: 16px; overflow: auto; border-radius: 8px; }
    .ok { color: #0a7b2f; font-weight: 700; }
    .err { color: #a40000; font-weight: 700; }
  </style>
</head>
<body>
  <h1>TeX → PDF Builder</h1>
  <p>Wrzuć pojedynczy plik <code>.tex</code> albo projekt <code>.zip</code> z <code>main.tex</code>.</p>

  <div class="box">
    <form action="/compile" method="post" enctype="multipart/form-data">
      <label>Tryb:</label><br />
      <select name="mode">
        <option value="plain">Plain TeX / ZIP</option>
        <option value="slayer">Slayer Paper Mode</option>
      </select><br />

      <label>Plik:</label><br />
      <input type="file" name="file" accept=".tex,.zip" required /><br />

      <button type="submit">Generate PDF</button>
    </form>
  </div>

  <h2>Jak przygotować ZIP?</h2>
  <pre>project.zip
├── main.tex
├── references.bib        opcjonalnie
├── formatka/slayer.sty   opcjonalnie
└── tresc/10-tresc.tex    opcjonalnie</pre>
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
    body { font-family: system-ui, sans-serif; margin: 40px; max-width: 1000px; }
    a.button { display: inline-block; padding: 10px 16px; border: 1px solid #222; border-radius: 8px; text-decoration: none; margin-right: 8px; }
    iframe { width: 100%; height: 700px; border: 1px solid #ddd; border-radius: 8px; }
    pre { background: #111; color: #eee; padding: 16px; overflow: auto; border-radius: 8px; }
    .ok { color: #0a7b2f; font-weight: 700; }
    .err { color: #a40000; font-weight: 700; }
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  {% if success %}
    <p class="ok">PDF wygenerowany.</p>
    <p>
      <a class="button" href="/download/{{ job_id }}">Download PDF</a>
      <a class="button" href="/">Nowy plik</a>
    </p>
    <iframe src="/download/{{ job_id }}"></iframe>
  {% else %}
    <p class="err">Kompilacja nie powiodła się.</p>
    <p><a class="button" href="/">Wróć</a></p>
  {% endif %}
  <h2>Log</h2>
  <pre>{{ log }}</pre>
</body>
</html>
"""
