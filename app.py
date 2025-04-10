# 完整補上 /observe 按鈕後端邏輯（app-hotboost-v5-rhythm）
# 修正觀察功能實際觸發後，跳過下注追蹤

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

@app.route('/observe')
def observe():
    global observation_next
    observation_next = True
    return redirect('/')

@app.route('/', methods=['GET', 'POST'])
def index():
    global hot_hits, hot_pool_hits, dynamic_hits, extra_hits, all_hits, total_tests
    global current_stage, actual_bet_stage, training_mode, history, predictions
    global last_hot_pool_hit, last_champion_zone, rhythm_history, rhythm_state
    global was_observed, observation_next

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

            was_observed = observation_next
            observation_next = False  # reset after use

            if len(predictions) >= 1:
                champion = current[0]
                last_pred = predictions[-1]
                hit = champion in last_pred

                if hit:
                    if training_mode:
                        all_hits += 1
                    current_stage = 1
                    actual_bet_stage = 1
                else:
                    current_stage += 1
                    if not was_observed:
                        actual_bet_stage += 1
                    if current_stage > 4:
                        history.clear()
                        predictions.clear()
                        current_stage = actual_bet_stage = 1

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

# 其他區塊與前面一致（reset、toggle、generate_prediction...）
