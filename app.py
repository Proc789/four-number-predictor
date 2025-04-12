from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
sources = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
training_enabled = False
rhythm_history = []
rhythm_state = "未知"
last_champion_zone = ""
was_observed = False
observation_message = ""

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>7碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>7碼預測器</h2>
  <div>版本：熱號2 + 動熱2 + 補碼3（第4關補碼改為2碼）</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <form method='GET' action='/observe' onsubmit="syncBeforeObserve()">
    <input type='hidden' name='first' id='first_obs'>
    <input type='hidden' name='second' id='second_obs'>
    <input type='hidden' name='third' id='third_obs'>
    <button type='submit'>觀察本期</button>
  </form>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>
  <a href='/reset'><button>清除所有資料</button></a>
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
  {% if last_champion_zone %}<div>冠軍號碼開在：{{ last_champion_zone }}</div>{% endif %}
  {% if observation_message %}<div style='color: gray;'>{{ observation_message }}</div>{% endif %}
  <div>熱號池節奏狀態：{{ rhythm_state }}</div>
  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
      熱號命中次數：{{ hot_hits }} / {{ total_tests }}<br>
      動熱命中次數：{{ dynamic_hits }} / {{ total_tests }}<br>
      補碼命中次數：{{ extra_hits }} / {{ total_tests }}<br>
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
        document.getElementById('first_obs').value = document.getElementById('first').value;
        document.getElementById('second_obs').value = document.getElementById('second').value;
        document.getElementById('third_obs').value = document.getElementById('third').value;
      }, 100);
    }
    function syncBeforeObserve() {
      document.getElementById('first_obs').value = document.getElementById('first').value;
      document.getElementById('second_obs').value = document.getElementById('second').value;
      document.getElementById('third_obs').value = document.getElementById('third').value;
    }
  </script>
</body>
</html>
"""

@app.route('/observe')
def observe():
    global was_observed, observation_message
    was_observed = True
    observation_message = "上期為觀察期"
    try:
        first = int(request.args.get('first', '10'))
        second = int(request.args.get('second', '10'))
        third = int(request.args.get('third', '10'))
        current = [first, second, third]
        history.append(current)

        if len(history) >= 5:
            prediction = make_prediction(current_stage)
            predictions.append(prediction)
            champion = current[0]
            hot_pool = sources[-1]['hot'] + sources[-1]['dynamic'] if sources else []

            rhythm_history.append(1 if champion in hot_pool else 0)
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
    except:
        pass
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests
    global current_stage, training_enabled, was_observed, observation_message
    global rhythm_history, rhythm_state, last_champion_zone

    prediction = None
    last_prediction = predictions[-1] if predictions else None
    observation_message = ""

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(history) >= 5 or training_enabled:
                prediction = make_prediction(current_stage)
                predictions.append(prediction)

                if len(predictions) >= 2:
                    champion = current[0]
                    if champion in predictions[-2]:
                        all_hits += 1
                        current_stage = 1
                    else:
                        current_stage += 1

                    if training_enabled:
                        total_tests += 1
                        if champion in sources[-1]['hot']:
                            hot_hits += 1
                            last_champion_zone = "熱號區"
                        elif champion in sources[-1]['dynamic']:
                            dynamic_hits += 1
                            last_champion_zone = "動熱區"
                        elif champion in sources[-1]['extra']:
                            extra_hits += 1
                            last_champion_zone = "補碼區"
                        else:
                            last_champion_zone = "未命中"

                    hot_pool = sources[-1]['hot'] + sources[-1]['dynamic']
                    rhythm_history.append(1 if champion in hot_pool else 0)
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
        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        history=history,
        training=training_enabled,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        rhythm_state=rhythm_state,
        last_champion_zone=last_champion_zone,
        observation_message=observation_message)

@app.route('/toggle')
def toggle():
    global training_enabled, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, predictions
    training_enabled = not training_enabled
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    predictions = []
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, sources
    history.clear()
    predictions.clear()
    sources.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    return redirect('/')

def make_prediction(stage):
    recent = history[-3:]
    flat = [n for g in recent for n in g]
    freq = Counter(flat)

    hot = [n for n, _ in freq.most_common(3)][:2]

    dynamic_pool = [n for n in freq if n not in hot]
    dynamic_sorted = sorted(dynamic_pool, key=lambda x: (-freq[x], -flat[::-1].index(x)))
    dynamic = dynamic_sorted[:2]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)
    extra_count = 2 if stage == 4 else 3
    extra = pool[:extra_count]

    sources.append({'hot': hot, 'dynamic': dynamic, 'extra': extra})
    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
