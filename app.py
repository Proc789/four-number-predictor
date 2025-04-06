# app.py
from flask import Flask, render_template_string, request
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
current_stage = 1

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>4碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>4碼預測器</h2>
  <div style="font-size: 14px; color: #666;">版本：熱號2 + 補碼2</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>

  {% if prediction %}
    <div style='margin-top: 20px;'><strong>本期預測號碼：</strong> {{ prediction }}（第 {{ stage }} 關）</div>
  {% endif %}
  <br>
  <div style='text-align: left;'>
    <strong>最近輸入紀錄：</strong>
    <ul>
      {% for row in history_data %}<li>{{ row }}</li>{% endfor %}
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

            if len(history) >= 3:
                flat = [n for group in history[-3:] for n in group]
                freq = Counter(flat)
                top_hot = sorted(freq.items(), key=lambda x: (-x[1], -flat[::-1].index(x[0])))[:3]
                hot = [n for n, _ in top_hot][:2]
                used = set(hot)
                pool = [n for n in range(1, 11) if n not in used]
                random.shuffle(pool)
                extra = pool[:2]
                result = sorted(hot + extra)
                prediction = result
                predictions.append(result)

                champion = current[0]
                if last_prediction and champion in last_prediction:
                    current_stage = 1
                else:
                    current_stage += 1

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        history_data=history[-10:],
        stage=current_stage)

if __name__ == '__main__':
    app.run(debug=True)
