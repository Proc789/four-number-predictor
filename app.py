from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hot_hits = 0
hot_pool_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
actual_bet_stage = 1
training_mode = False
last_hot_pool_hit = False
last_champion_zone = ""
rhythm_history = []  # 最近5期熱號池命中紀錄
rhythm_state = "未知"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>預測器 - 追關版</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>預測器 - 追關版</h2>
  <div>版本：app-hotboost-v5-rhythm（下注追蹤 + 熱號池節奏）</div>

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
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關 / 建議下注第 {{ bet_stage }} 關）
    </div>
  {% endif %}
  {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}
    </div>
  {% endif %}

  {% if stage > 4 %}
    <div style='color: red; margin-top: 15px;'>
      已失敗，系統將重置。
    </div>
  {% endif %}

  {% if training %}
    {% if last_hot_pool_hit %}
      <div style='color: green; margin-top: 15px; font-weight: bold;'>
        上期熱號池有命中，預測方向正確，建議持續追關。
      </div>
    {% endif %}
    {% if last_champion_zone %}
      <div style='margin-top: 10px;'>
        冠軍號碼開在：{{ last_champion_zone }}
      </div>
    {% endif %}
    <div style='margin-top: 10px;'>
      熱號池節奏狀態：{{ rhythm_state }}
    </div>
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
      熱號命中次數：{{ hot_hits }}<br>
      熱號池命中次數：{{ hot_pool_hits }}<br>
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
    global hot_hits, hot_pool_hits, dynamic_hits, extra_hits, all_hits, total_tests
    global current_stage, actual_bet_stage, training_mode, history, predictions
    global last_hot_pool_hit, last_champion_zone, rhythm_history, rhythm_state

    prediction = None
    last_prediction = predictions[-1] if predictions else None
    last_hot_pool_hit = False
    last_champion_zone = ""

    if request.method == 'POST':
        try:
            first = int(request.form['first']) or 10
            second = int(request.form['second']) or 10
            third = int(request.form['third']) or 10
            current = [first, second, third]
            history.append(current)

            if len(predictions) >= 1:
                champion = current[0]
                last_pred = predictions[-1]
                if champion in last_pred:
                    if training_mode:
                        all_hits += 1
                    current_stage = 1
                    actual_bet_stage = 1
                else:
                    current_stage += 1
                    if training_mode:
                        actual_bet_stage += 1
                    if current_stage > 4:
                        history.clear()
                        predictions.clear()
                        current_stage = 1
                        actual_bet_stage = 1

                if training_mode:
                    total_tests += 1
                    if champion in last_pred[:2]:
                        hot_hits += 1
                        last_champion_zone = "熱號區"
                    elif champion in last_pred[2:4]:
                        dynamic_hits += 1
                        last_champion_zone = "動熱區"
                    elif champion in last_pred[4:]:
                        extra_hits += 1
                        last_champion_zone = "補碼區"
                    else:
                        last_champion_zone = "未預測組合"

                    if champion in hot_pool:
                        hot_pool_hits += 1
                        if champion not in last_pred:
                            last_hot_pool_hit = True

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

            if training_mode or len(history) >= 5:
                prediction = generate_prediction(current_stage)
                predictions.append(prediction)

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        stage=current_stage,
        bet_stage=actual_bet_stage,
        training=training_mode,
        history=history,
        hot_hits=hot_hits,
        hot_pool_hits=hot_pool_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests,
        last_hot_pool_hit=last_hot_pool_hit,
        last_champion_zone=last_champion_zone,
        rhythm_state=rhythm_state)

@app.route('/toggle')
def toggle():
    global training_mode, hot_hits, hot_pool_hits, dynamic_hits, extra_hits
    global all_hits, total_tests, current_stage, actual_bet_stage, predictions
    training_mode = not training_mode
    hot_hits = hot_pool_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = actual_bet_stage = 1
    predictions = []
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hot_hits, hot_pool_hits, dynamic_hits, extra_hits
    global all_hits, total_tests, current_stage, actual_bet_stage, rhythm_history, rhythm_state
    history.clear()
    predictions.clear()
    hot_hits = hot_pool_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = actual_bet_stage = 1
    rhythm_history.clear()
    rhythm_state = "未知"
    return redirect('/')

def generate_prediction(stage):
    global hot_pool
    recent = history[-3:]
    flat = [n for group in recent for n in group]

    freq = Counter(flat)
    reversed_flat = flat[::-1]
    score = {}
    for idx, n in enumerate(reversed_flat):
        score[n] = score.get(n, 0) + (3 - idx // 3) + freq[n] * 2
    sorted_hot = sorted(score.items(), key=lambda x: (-x[1], -reversed_flat.index(x[0])))
    hot_pool = [n for n, _ in sorted_hot[:4]]
    hot = hot_pool[:2]

    flat_dynamic = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dynamic)
    dynamic_pool = sorted(freq_dyn.items(), key=lambda x: (-x[1], -flat_dynamic[::-1].index(x[0])))
    dynamic = [n for n, _ in dynamic_pool[:2]]

    extra_count = 3 if stage in [1, 2, 3] else 2
    used = set(hot + dynamic)
    available = [n for n in range(1, 11) if n not in used]
    random.shuffle(available)

    recent_unique = set(flat)
    safe_pool = [n for n in available if n in recent_unique]
    cold_pool = [n for n in available if n not in recent_unique]

    extra = random.sample(safe_pool, min(extra_count, len(safe_pool)))
    if len(extra) < extra_count and cold_pool:
        extra += random.sample(cold_pool, min(1, extra_count - len(extra)))
    if len(extra) < extra_count:
        remaining_pool = [n for n in range(1, 11) if n not in hot + dynamic + extra]
        random.shuffle(remaining_pool)
        extra += remaining_pool[:extra_count - len(extra)]

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
