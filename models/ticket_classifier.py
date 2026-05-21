import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
import os

class TicketClassifier:
    def __init__(self, model_path="models/classifier.joblib"):
        self.model_path = model_path
        self.model = self._load_model()
    
    def _load_model(self):
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)
        return None
    
    def train(self , tickets_json_path= "data/sample_ticket/tickets.json"):
        import json
        with open(tickets_json_path, 'r') as f:
            data = json.load(f)

        df = pd.DataFrame(data)

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
            ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
        ])

        pipeline.fit(df['description'], df['category'])
        joblib.dump(pipeline, self.model_path)
        self.model = pipeline
        print(f"Model trained and saved to {self.model_path}")

    def predict(self, text: str) -> str:
        if self.model is None:
            raise Exception("Model not trained. Need to run train() first.")
        return self.model.predict([text])[0]

ticket_classifier = TicketClassifier()