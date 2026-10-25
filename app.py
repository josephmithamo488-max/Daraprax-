
import os
import json
import requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

LLM_URL = os.getenv(
    "LLM_URL",
    "https://api.deepseek.com/chat/completions"
)
LLM_KEY = os.getenv("LLM_KEY")

HOME_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daraprax | Knowledge into Action</title>
<style>
body{font-family:Arial,sans-serif;max-width:700px;margin:40px auto;padding:20px;line-height:1.6;background:#f7f8fa;color:#18212b}
h1{font-size:2.3rem;margin-bottom:0}
p{color:#465363}
textarea{box-sizing:border-box;width:100%;min-height:150px;padding:14px;border:1px solid #ccd2da;border-radius:10px;font:inherit}
button{width:100%;padding:14px;margin-top:12px;background:#176b4d;color:white;border:0;border-radius:9px;font-size:1rem;font-weight:bold}
.example{font-size:.9rem;color:#176b4d}
</style>
</head>
<body>
<h1>Daraprax</h1>
<p><strong>Knowledge put into action.</strong></p>
<p>Describe a real problem you're trying to solve. Daraprax will help structure it and identify possible next steps.</p>
<form method="post" action="/analyze">
<textarea name="problem" minlength="10" maxlength="3000" required
placeholder="For example: My small shop often runs out of popular products while slow-moving stock ties up my money."></textarea>
<button type="submit">Analyze my problem</button>
</form>
<p class="example">Start with a problem you understand. Clear problems lead to better next steps.</p>
</body>
</html>
"""

RESULT_HTML = """
<!doctype html>
<html lang="en">
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Daraprax Analysis</title>
<style>
body{font-family:Arial,sans-serif;max-width:700px;margin:30px auto;padding:20px;line-height:1.6;color:#18212b}
section{padding:16px;margin:14px 0;background:#f2f5f4;border-radius:10px}
a{color:#176b4d}
</style>
</head>
<body>
<a href="/">← Back to Daraprax</a>
<h1>Your problem analysis</h1>
{% if demo %}<p><strong>Demo mode:</strong> This is a preliminary suggestion, not verified research.</p>{% endif %}
<section><h2>Problem, restated</h2><p>{{ result.restated }}</p></section>
<section><h2>Relevant areas of knowledge</h2><ul>{% for item in result.domains %}<li>{{ item }}</li>{% endfor %}</ul></section>
<section><h2>Potential people to involve</h2><ul>{% for item in result.helpers %}<li>{{ item }}</li>{% endfor %}</ul></section>
<section><h2>Suggested next step</h2><p>{{ result.next_step }}</p></section>
<p><em>These suggestions are starting points, not proof that a solution will work.</em></p>
</body>
</html>
"""

def analyze_problem(problem):
    if LLM_KEY:
        try:
            response = requests.post(
                LLM_URL,
                headers={
                    "Authorization": f"Bearer {LLM_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Analyze the user's practical problem. "
                                "Return only valid JSON with these keys: "
                                "restated (string), domains (list of strings), "
                                "helpers (list of strings), next_step (string). "
                                "Be realistic. Do not invent evidence or claim "
                                "that suggested outcomes are verified."
                            )
                        },
                        {"role": "user", "content": problem}
                    ],
                    "temperature": 0.3
                },
                timeout=25
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            data = json.loads(content)

            if (
                isinstance(data.get("restated"), str)
                and isinstance(data.get("domains"), list)
                and isinstance(data.get("helpers"), list)
                and isinstance(data.get("next_step"), str)
            ):
                return data, False
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass

    return {
        "restated": (
            "You are trying to address: " + problem.strip()
        ),
        "domains": [
            "Understand the people affected",
            "Collect relevant facts and measurements",
            "Investigate possible causes and constraints"
        ],
        "helpers": [
            "Someone directly affected by the problem",
            "A person with practical experience in this area",
            "A subject-matter expert, if needed"
        ],
        "next_step": (
            "Write down the three most important facts you know, "
            "what remains uncertain, and one small test that could "
            "help you learn more."
        )
    }, True

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HOME_HTML)

@app.route("/analyze", methods=["POST"])
def analyze():
    problem = request.form.get("problem", "").strip()

    if len(problem) < 10 or len(problem) > 3000:
        return "Please enter a problem between 10 and 3000 characters.", 400

    result, demo = analyze_problem(problem)
    return render_template_string(
        RESULT_HTML,
        result=result,
        demo=demo
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
