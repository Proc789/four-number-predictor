from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hit_stats = {"hot": 0, "dynamic": 0, "extra": 0, "total": 0, "all": 0}
current_stage = 1
training_mode = False

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>4碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 30px; font-family: sans-serif; text-align: center;'>
  <h2>4碼預測器</h2>
  <div>版本：熱號2＋動熱1＋補碼1（公版UI）</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>
  <a href='/reset'><button>清除資料</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% endif %}
  {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}
    </div>
  {% endif %}

  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ hit_stats.all }} / {{ hit_stats.total }}<br>
      熱號命中次數：{{ hit_stats.hot }}<br>
      動熱命中次數：{{ hit_stats.dynamic }}<br>
      補碼命中次數：{{ hit_stats.extra }}<br>
    </div>
  {% endif %}

  {% if history_data %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history_data %}
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
    global current_stage
    prediction = None
    last_prediction = predictions[-1] if predictions else None

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 5:
                prediction = generate_prediction()
                predictions.append(prediction)

                if training_mode and len(predictions) >= 2:
                    champion = current[0]
                    hit_stats['total'] += 1
                    if champion in predictions[-2]:
                        hit_stats['all'] += 1
                        current_stage = 1
                    else:
                        current_stage += 1
                    if champion in prediction[:2]:
                        hit_stats['hot'] += 1
                    elif champion in prediction[2:3]:
                        hit_stats['dynamic'] += 1
                    elif champion in prediction[3:]:
                        hit_stats['extra'] += 1
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        history_data=history[-10:],
        hit_stats=hit_stats,
        training=training_mode)

@app.route('/toggle')
def toggle():
    global training_mode, hit_stats, current_stage
    training_mode = not training_mode
    hit_stats = {"hot": 0, "dynamic": 0, "extra": 0, "total": 0, "all": 0}
    current_stage = 1
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hit_stats, current_stage
    history = []
    predictions = []
    hit_stats = {"hot": 0, "dynamic": 0, "extra": 0, "total": 0, "all": 0}
    current_stage = 1
    return redirect('/')

def generate_prediction():
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)
    hot = [n for n, _ in freq.most_common(2)]

    flat_dyn = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dyn)
    dynamic_pool = sorted(freq_dyn.items(), key=lambda x: (-x[1], -flat_dyn[::-1].index(x[0])))
    dynamic = [n for n, _ in dynamic_pool[:1]]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra = pool[:1]

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
