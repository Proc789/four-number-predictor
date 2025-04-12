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
rhythm_history = []
rhythm_state = "未知"
was_observed = False
observation_message = ""
hot_pool = []
last_error_message = ""

def parse_input(val):
    if val == '0' or val == 0:
        return 10
    try:
        return int(val)
    except:
        return 10

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>預測器 - 追關版</title>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>預測器 - 追關版</h2>
  <div>版本：app-hotboost-v5-rhythm（修正版：節奏 + 公版UI + 自動跳格）</div>
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
  {% if last_champion_zone %}<div>冠軍號碼開在：{{ last_champion_zone }}</div>{% endif %}
  {% if observation_message %}<div style='color: gray;'>{{ observation_message }}</div>{% endif %}
  {% if error_message %}<div style='color: red;'>錯誤：{{ error_message }}</div>{% endif %}
  <div>熱號池節奏狀態：{{ rhythm_state }}</div>
  {% if training %}
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
        {% for row in history[-10:] %}<li>第 {{ loop.index }} 期：{{ row }}</li>{% endfor %}
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
        first = parse_input(request.args.get('first', ''))
        second = parse_input(request.args.get('second', ''))
        third = parse_input(request.args.get('third', ''))
        current = [first, second, third]
        history.append(current)
        process_input(current, is_observe=True)
    except:
        pass
    stage_to_use = actual_bet_stage if 1 <= actual_bet_stage <= 4 else 1
    prediction = generate_prediction(stage_to_use)
    predictions.append(prediction)
    return redirect('/')

@app.route('/toggle')
def toggle():
    global training_mode, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, actual_bet_stage, predictions, hot_pool_hits
    training_mode = not training_mode
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = hot_pool_hits = 0
    current_stage = actual_bet_stage = 1
    predictions = []
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, actual_bet_stage, hot_pool_hits
    history.clear()
    predictions.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = hot_pool_hits = 0
    current_stage = actual_bet_stage = 1
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def index():
    global was_observed, observation_message, last_error_message
    prediction = predictions[-1] if predictions else None
    last_prediction = predictions[-2] if len(predictions) >= 2 else None
    last_error_message = ""

    if request.method == 'POST':
        try:
            first = parse_input(request.form['first'])
            second = parse_input(request.form['second'])
            third = parse_input(request.form['third'])
            current = [first, second, third]
            history.append(current)
            process_input(current, is_observe=False)
            stage_to_use = current_stage if 1 <= current_stage <= 4 else 1
            prediction = generate_prediction(stage_to_use)
            predictions.append(prediction)
            was_observed = False
            observation_message = ""
        except:
            prediction = ['格式錯誤']
            last_error_message = "輸入號碼必須是 1 到 10"

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
        rhythm_state=rhythm_state,
        observation_message=observation_message,
        error_message=last_error_message)

def process_input(current, is_observe=False):
    global current_stage, actual_bet_stage
    global hot_hits, dynamic_hits, extra_hits, all_hits, total_tests
    global last_hot_pool_hit, last_champion_zone, rhythm_history, rhythm_state
    global hot_pool, predictions

    if len(predictions) < 1:
        return

    champion = current[0]
    last_pred = predictions[-1]
    hit = champion in last_pred

    if not is_observe:
        if hit:
            if training_mode:
                all_hits += 1
            current_stage = 1
            actual_bet_stage = 1
        else:
            current_stage += 1
            actual_bet_stage += 1
            if current_stage > 4:
                history.clear()
                predictions.clear()
                current_stage = actual_bet_stage = 1

    # ✅ 無論是否統計模式，都更新節奏狀態
    if champion in hot_pool:
        if training_mode:
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

def generate_prediction(stage):
    recent = history[-3:]
    flat = [n for group in recent for n in group]
    freq = Counter(flat)
    hot = [n for n, _ in freq.most_common(4)][:2]

    flat_dynamic = [n for n in flat if n not in hot]
    freq_dyn = Counter(flat_dynamic)
    dynamic_pool = sorted(freq_dyn.items(), key=lambda x: (-x[1], -flat_dynamic[::-1].index(x[0])))
    dynamic = [n for n, _ in dynamic_pool[:2]]

    global hot_pool
    hot_pool = [n for n, _ in freq.most_common(4)]

    used = set(hot + dynamic)
    pool = [n for n in range(1, 11) if n not in used]
    random.shuffle(pool)

    extra_count = 3 if stage in [1, 2, 3] else 2
    extra = pool[:extra_count]

    while len(hot + dynamic + extra) < (2 + 2 + extra_count):
        for n in range(1, 11):
            if n not in (hot + dynamic + extra):
                extra.append(n)
            if len(hot + dynamic + extra) == (2 + 2 + extra_count):
                break

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
