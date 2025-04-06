from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hits = 0
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
total = 0
stage = 1
training = False
sources = []

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>4碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>4碼預測器</h2>
  <div>版本：熱號2 + 動熱1 + 補碼1（公版UI）</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>
  <a href='/reset'><button style='margin-left: 10px;'>清除所有資料</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% elif stage and history|length >= 5 and predictions %}
    <div style='margin-top: 20px;'>目前第 {{ stage }} 關</div>
  {% endif %}

  {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}
    </div>
  {% endif %}

  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ hits }} / {{ total }}<br>
      熱號命中次數：{{ hot_hits }}<br>
      動熱命中次數：{{ dynamic_hits }}<br>
      補碼命中次數：{{ extra_hits }}<br>
    </div>
  {% endif %}

  {% if history %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history[-10:] %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
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

@app.route('/', methods=['GET', 'POST'])
def index():
    global hits, hot_hits, dynamic_hits, extra_hits, total, stage, training
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(predictions) >= 1:
                champion = current[0]
                prev = predictions[-1]
                if training:
                    total += 1
                    if champion in prev:
                        hits += 1
                        stage = 1
                    else:
                        stage += 1
                    src = sources[-1]
                    if champion in src['hot']:
                        hot_hits += 1
                    elif champion in src['dynamic']:
                        dynamic_hits += 1
                    elif champion in src['extra']:
                        extra_hits += 1

            if training or len(history) >= 5:
                prediction = generate_prediction()
                predictions.append(prediction)

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=stage,
        history=history,
        training=training,
        hits=hits,
        total=total,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits)

@app.route('/toggle')
def toggle():
    global training, hits, total, stage, predictions, sources
    training = not training
    hits = total = stage = 1
    predictions = []
    sources = []
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hits, total, stage, training, sources, hot_hits, dynamic_hits, extra_hits
    history.clear()
    predictions.clear()
    sources = []
    hits = total = stage = 1
    hot_hits = dynamic_hits = extra_hits = 0
    training = False
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot = [n for n, _ in sorted(freq.items(), key=lambda x: (-x[1], -flat[::-1].index(x[0])))][:2]
    flat_dyn = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dyn)
    dynamic = [n for n, _ in sorted(freq_dyn.items(), key=lambda x: (-x[1], -flat_dyn[::-1].index(x[0])))][:1]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra = pool[:1]

    result = hot + dynamic + extra
    filler_pool = [n for n in range(1, 11) if n not in result]
    random.shuffle(filler_pool)
    result += filler_pool[:(4 - len(result))]

    sources.append({"hot": hot, "dynamic": dynamic, "extra": extra})
    return sorted(result)

if __name__ == '__main__':
    app.run(debug=True)
