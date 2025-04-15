# 多碼數預測器（優化版 + 加入關卡判定）
from flask import Flask, render_template_string, request, redirect, session
import random
from collections import Counter

app = Flask(__name__)
app.secret_key = 'secret-key'

history = []
predictions = []
sources = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
last_champion_zone = ""
rhythm_history = []
rhythm_state = "未知"
current_stage = 1

TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>多碼數預測器</title>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>預測器</h2>
  <form method='POST'>
    <label><input type='radio' name='mode' value='4' {{ 'checked' if mode == '4' else '' }}> 4碼</label>
    <label><input type='radio' name='mode' value='5' {{ 'checked' if mode == '5' else '' }}> 5碼</label>
    <label><input type='radio' name='mode' value='6' {{ 'checked' if mode == '6' else '' }}> 6碼</label>
    <label><input type='radio' name='mode' value='7' {{ 'checked' if mode == '7' else '' }}> 7碼</label><br><br>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode='numeric'><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode='numeric'><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode='numeric'><br><br>
    <button type='submit'>提交並預測</button>
  </form>
  <form method='GET' action='/reset'>
    <button type='submit' style='margin-top: 10px;'>清除所有資料</button>
  </form>
  {% if prediction %}<div><strong>本期預測號碼：</strong> {{ prediction }}</div>{% endif %}
  {% if last_prediction %}
    <div><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
    <div style='color: {{ "green" if last_hit_status else "red" }};'>{{ '✅ 命中！' if last_hit_status else '❌ 未命中' }}</div>
  {% endif %}
  {% if last_champion_zone %}<div>冠軍號碼開在：{{ last_champion_zone }}</div>{% endif %}
  <div>熱號節奏狀態：{{ rhythm_state }}</div>
  <div><strong>目前關卡：</strong> 第 {{ current_stage }} 關</div>
  <div style='margin-top: 20px; text-align: left;'>
    <strong>命中統計：</strong><br>
    冠軍命中次數：{{ all_hits }} / {{ total_tests }}<br>
    熱號命中次數：{{ hot_hits }}<br>
    動熱命中次數：{{ dynamic_hits }}<br>
    補碼命中次數：{{ extra_hits }}<br>
  </div>
  {% if history %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>{% for row in history[-10:] %}<li>{{ row }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
<script>
function moveToNext(current, nextId) {
  setTimeout(() => {
    if (current.value === '0') current.value = '10';
    let val = parseInt(current.value);
    if (!isNaN(val) && val >= 1 && val <= 10) {
      document.getElementById(nextId).focus();
    }
  }, 100);
}
</script>
</body>
</html>
"""

@app.route('/reset', methods=['GET'])
def reset():
    global history, predictions, sources, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, last_champion_zone, rhythm_history, rhythm_state, current_stage
    history.clear()
    predictions.clear()
    sources.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    last_champion_zone = ""
    rhythm_history = []
    rhythm_state = "未知"
    current_stage = 1
    return redirect('/')

def get_hot_numbers(flat):
    freq = Counter(flat)
    return [num for num, _ in sorted(freq.items(), key=lambda x: (-x[1], -flat[::-1].index(x[0])))[:2]]

def get_dynamic_numbers(flat, hot):
    pool = [n for n in flat if n not in hot]
    freq = Counter(pool)
    top4 = sorted(freq, key=lambda x: (-freq[x], -flat[::-1].index(x)))[:4]
    return random.sample(top4, 2) if len(top4) >= 2 else top4

def predict(mode):
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    hot = get_hot_numbers(flat)
    dynamic = get_dynamic_numbers(flat, hot)
    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)

    if mode == '4':
        extra = pool[:1]
        result = hot[:2] + dynamic[:1] + extra
    elif mode == '5':
        extra = pool[:1]
        result = hot[:2] + dynamic[:2] + extra
    elif mode == '6':
        extra = pool[:2]
        result = hot[:2] + dynamic[:2] + extra
    elif mode == '7':
        extra = pool[:3]
        result = hot[:2] + dynamic[:2] + extra
    else:
        extra = pool[:1]
        result = hot + dynamic + extra

    while len(result) < int(mode):
        filler = [n for n in range(1, 11) if n not in result]
        random.shuffle(filler)
        result += filler[:int(mode) - len(result)]

    sources.append({'hot': hot, 'dynamic': dynamic, 'extra': extra})
    return sorted(list(dict.fromkeys(result)))

@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, last_champion_zone, rhythm_history, rhythm_state, current_stage
    prediction = None
    mode = session.get('mode', '6')
    last_hit_status = False

    if request.method == 'POST':
        first = int(request.form['first'])
        if first == 0: first = 10
        second = int(request.form['second'])
        if second == 0: second = 10
        third = int(request.form['third'])
        if third == 0: third = 10
        current = [first, second, third]
        history.append(current)

        mode = request.form.get('mode', '6')
        session['mode'] = mode

        last_prediction = predictions[-1] if predictions else []
        champ = current[0]
        last_hit_status = champ in last_prediction

        if predictions:
            src = sources[-1]
            if last_hit_status:
                all_hits += 1
                current_stage = 1
            else:
                current_stage += 1

            if champ in src['hot']:
                hot_hits += 1
                last_champion_zone = "熱號區"
            elif champ in src['dynamic']:
                dynamic_hits += 1
                last_champion_zone = "動熱區"
            elif champ in src['extra']:
                extra_hits += 1
                last_champion_zone = "補碼區"
            else:
                last_champion_zone = "未命中"

            total_tests += 1

            hot_pool = src['hot'] + src['dynamic']
            rhythm_history.append(1 if champ in hot_pool else 0)
            if len(rhythm_history) > 5:
                rhythm_history.pop(0)
            recent = rhythm_history[-3:]
            total = sum(recent)
            if recent == [0, 0, 1]:
                rhythm_state = "預熱期"
            elif total >= 2:
                rhythm_state = "穩定期"
            elif total == 0:
                rhythm_state = "失準期"
            else:
                rhythm_state = "搖擺期"

        prediction = predict(mode)
        predictions.append(prediction)
    else:
        last_prediction = predictions[-1] if predictions else []

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=predictions[-2] if len(predictions) >= 2 else None,
        last_hit_status=last_hit_status,
        last_champion_zone=last_champion_zone,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        rhythm_state=rhythm_state,
        current_stage=current_stage,
        history=history,
        mode=mode)

if __name__ == '__main__':
    app.run(debug=True)
