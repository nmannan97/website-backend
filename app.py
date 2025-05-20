from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
CORS(app)

# SQLite database path
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'scores.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

score_length = 10

# Score model
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)

# Create table
with app.app_context():
    db.create_all()

# Insert a score at startup using SQLAlchemy
with app.app_context():
    if not Score.query.filter_by(value=0).first():
        db.session.add(Score(value=0))
        db.session.commit()
        print("Inserted score 95 using SQLAlchemy")

@app.route('/submit-score', methods=['POST', 'GET'])
def submit_score():
    if request.method == 'POST':
        data = request.get_json()
        score_val = data.get('score')

        if score_val is None:
            return jsonify({"error": "Score not provided"}), 400

        # Get top 10 scores in descending order
        top_scores = Score.query.order_by(Score.value.desc()).limit(score_length).all()

        # Check if there's room (fewer than 10) or if the new score is better than the lowest
        if len(top_scores) < score_length or score_val > top_scores[-1].value:
            # Add new score
            new_score = Score(value=score_val)
            db.session.add(new_score)
            db.session.commit()

            # If we now have more than 10, remove the lowest one
            updated_scores = Score.query.order_by(Score.value.desc()).all()
            if len(updated_scores) > score_length:
                lowest_score = updated_scores[-1]
                db.session.delete(lowest_score)
                db.session.commit()

            return jsonify({"message": "Score saved", "score": score_val}), 200
        else:
            return jsonify({"message": "Score too low to be saved", "score": score_val}), 200

    elif request.method == 'GET':
        # Return top 10 scores
        top_scores = Score.query.order_by(Score.value.desc()).limit(score_length).all()
        scores = [s.value for s in top_scores]
        return jsonify({"scores": scores}), 200


if __name__ == '__main__':
    app.run(debug=True)
