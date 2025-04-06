from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hits = 0
total = 0
stage = 1
training = False
last_result = None

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>4碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>4碼預測器</h2>
  <div style='font-size: 14px;'>版本：熱號2 + 動熱1 + 補碼1（公版UI）</div><br>

  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>
  <a href='/reset'><button style='margin-left: 10px;'>清除資料</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% elif stage and history|length >= 5 %}
    <div style='margin-top: 20px;'>目前第 {{ stage }} 關</div>
  {% endif %}

  {% if last_result %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}<br>
      <strong>上期冠軍號碼：</strong> {{ last_result[0] }}<br>
      <strong>是否命中：</strong> {{ last_result[1] }}
    </div>
  {% endif %}

  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ hits }} / {{ total }}<br>
    </div>
  {% endif %}

  <div style='margin-top: 20px; text-align: left;'>
    <strong>最近輸入紀錄：</strong>
    <ul>
      {% for row in history_data %}
        <li>第 {{ loop.index }} 期：{{ row }}</li>
      {% endfor %}
    </ul>
  </div>

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
    global hits, total, stage, training, last_result
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(predictions) >= 1 and len(history) > 1:
                champion = current[0]
                last = predictions[-1]
                hit = '命中' if champion in last else '未命中'
                last_result = (champion, hit)
                if training:
                    total += 1
                    if hit == '命中':
                        hits += 1
                        stage = 1
                    else:
                        stage += 1
            elif len(history) > 1:
                last_result = (current[0], '未比對')

            if training or len(history) >= 5:
                try:
                    prediction = generate_prediction()
                    predictions.append(prediction)
                except:
                    prediction = ['格式錯誤']

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        last_result=last_result,
        stage=stage,
        history_data=history[-10:],
        training=training,
        hits=hits,
        total=total)

@app.route('/toggle')
def toggle():
    global training, hits, total, stage
    training = not training
    if training:
        hits = 0
        total = 0
        stage = 1
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hits, total, stage, training, last_result
    history = []
    predictions = []
    hits = 0
    total = 0
    stage = 1
    last_result = None
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = Counter(flat)
    top_hot = sorted(freq.items(), key=lambda x: (-x[1], -flat[::-1].index(x[0])))
    hot = [n for n, _ in top_hot[:2]]
    
    flat_dynamic = [n for n in flat if n not in hot]
    freq_dyn = {n: flat_dynamic.count(n) for n in set(flat_dynamic)}
    dynamic_pool = sorted(freq_dyn, key=lambda x: (-freq_dyn[x], -flat_dynamic[::-1].index(x)))
    dynamic = dynamic_pool[:1] if dynamic_pool else []

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra = pool[:1]

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
