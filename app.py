# app-hotboost-v5-rhythm（觀察期穩定版 + 完整 UI）
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
observation_next = False
hot_pool = []

observation_message = ""

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>預測器 - 追關版</title>
</head>
<body style='max-width: 400px; margin: auto; padding: 20px; font-family: sans-serif;'>
  <h2>預測器 - 追關版</h2>
  <div>版本：app-hotboost-v5-rhythm（下注追蹤 + 熱號池節奏 + 觀察開關）</div><br>
  <form method='POST'>
    <input name='first' placeholder='冠軍' required style='width: 100%; padding: 8px;' inputmode='numeric'><br><br>
    <input name='second' placeholder='亞軍' required style='width: 100%; padding: 8px;' inputmode='numeric'><br><br>
    <input name='third' placeholder='季軍' required style='width: 100%; padding: 8px;' inputmode='numeric'><br><br>
    <button type='submit' style='width: 100%; padding: 10px;'>提交</button>
  </form>
  <br>
  <a href='/observe'><button>觀察本期</button></a>
  <a href='/toggle'><button>開關統計模式</button></a>
  <a href='/reset'><button>清除所有資料</button></a>
  <br><br>
  {% if prediction %}
    <div><strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關 / 建議下注第 {{ bet_stage }} 關）</div>
  {% endif %}
  {% if last_prediction %}
    <div><strong>上期預測號碼：</strong> {{ last_prediction }}</div>
  {% endif %}
  {% if last_champion_zone %}
    <div>冠軍號碼開在：{{ last_champion_zone }}</div>
  {% endif %}
  {% if observation_message %}
    <div style='color: gray;'>{{ observation_message }}</div>
  {% endif %}
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
        {% for row in history[-10:] %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}
</body>
</html>
"""

@app.route('/toggle')
def toggle():
    global training_mode, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, actual_bet_stage, predictions
    training_mode = not training_mode
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = actual_bet_stage = 1
    predictions = []
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, actual_bet_stage
    history.clear()
    predictions.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = actual_bet_stage = 1
    return redirect('/')

# generate_prediction 補上

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

    return sorted(hot + dynamic + extra)

if __name__ == '__main__':
    app.run(debug=True)
