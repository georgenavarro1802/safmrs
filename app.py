import os
import sys
import pandas as pd

from flask import Flask, request, jsonify, render_template

app = Flask(__name__)


def resource_path(relative_path):
    """ Get absolute path to resource, works for both development and PyInstaller bundle """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Load the CSV file into a DataFrame
csv_file_path = resource_path('SAFMR_2025.csv')
df = pd.read_csv(csv_file_path)


# Format currency values for display
def format_currency(amount):
    if isinstance(amount, str):
        amount = float(amount.replace('$', '').replace(',', ''))
    return f"${amount:,.0f}"


# Clean up the column names
df.columns = [col.strip().replace('\n', ' ') for col in df.columns]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/get_fmr', methods=['POST'])
def get_fmr():
    try:
        data = request.json
        zipcode = data.get('zipcode')
        if not zipcode:
            return jsonify({'error': 'ZIP code is required'}), 400

        result = df[df['ZIP Code'] == int(zipcode)]
        if result.empty:
            return jsonify({'error': f"No SAFMR data found for ZIP code {zipcode}"}), 404

        row = result.iloc[0]
        hud_area = row['HUD Fair Market Rent Area Name']

        bedroom_types = {
            '0BR': 'Studio',
            '1BR': '1 Bed',
            '2BR': '2 Bed',
            '3BR': '3 Bed',
            '4BR': '4 Bed'
        }

        fmr_data = []
        for br, name in bedroom_types.items():
            std_col = f'SAFMR {br}'
            min_col = f'SAFMR {br} - 90% Payment Standard'
            max_col = f'SAFMR {br} - 110% Payment Standard'

            if std_col in row.index:
                fmr_data.append({
                    'bedroom': name,
                    'standard': format_currency(row[std_col]),
                    'minimum': format_currency(row[min_col]),
                    'maximum': format_currency(row[max_col])
                })

        return jsonify({'zipcode': zipcode, 'hud_area': hud_area, 'fmr_data': fmr_data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
