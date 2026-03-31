from flask import Flask, render_template


# my app
app = Flask(__name__)

# route to homepage:
@app.route('/')
def index():
    return render_template('index.html')


if __name__ in '__main__':
    app.run(debug=True)