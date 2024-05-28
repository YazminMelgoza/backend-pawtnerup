from flask import Flask, jsonify
from firebase_admin import credentials, firestore, initialize_app
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import hstack
import pandas as pd
import numpy as np
import random


app = Flask(__name__)

# initialize firebase
cred = credentials.Certificate("key.json")
default_app = initialize_app(cred)
db = firestore.client()

@app.route('/')
def hello_world():
    return '<h1>Hello, World!</h1>'

@app.route('/recommendations/<userId>', methods=['GET'])
def user(userId):
    # Simulate user data
    user = {'id': userId, 'name': f'User{userId}'}
    
    # Simulate user preferences
    preferences = {
        'type': 'dog',
        'size': 'medium',
        'sex': 'male',
        'breed': 'breed2',
        'colors': ['black', 'white'],
        'features': ['friendly', 'playful']
    }
    
    # Generate pets data for testing
    pets = generate_pets_data(40)
    # Preprocess pets data
    pets_df, tfidf_vectorizers, categorical_columns = preprocess_data(pets)
    
    # Get recommendations
    recommendations = get_recommendations(preferences, pets, tfidf_vectorizers, categorical_columns)

    if not recommendations:
        return jsonify({'error': 'No recommendations found'}), 404

    return jsonify(recommendations)


def preprocess_data(pets):
    # Convert the data to a DataFrame
    df = pd.DataFrame(pets)
    
    # One-hot encode categorical features
    categorical_features = ['type', 'size', 'sex']
    df_categorical = pd.get_dummies(df[categorical_features])
    
    # Create TfidfVectorizer for 'breed', 'colors' and 'features' with a fixed vocabulary
    tfidf_vectorizer_breeds = TfidfVectorizer()
    tfidf_vectorizer_colors = TfidfVectorizer()
    tfidf_vectorizer_features = TfidfVectorizer()

    breeds_features = df['breed'].apply(lambda x: ' '.join([x]))
    colors_features = df['colors'].apply(lambda x: ' '.join(x))
    features_features = df['features'].apply(lambda x: ' '.join(x))

    tfidf_breeds = tfidf_vectorizer_breeds.fit_transform(breeds_features)
    tfidf_colors = tfidf_vectorizer_colors.fit_transform(colors_features)
    tfidf_features = tfidf_vectorizer_features.fit_transform(features_features)
    
    # Combine all features into a single matrix
    combined_features = hstack([df_categorical, tfidf_breeds, tfidf_colors, tfidf_features])

    tfidf_vectorizers = {
        'breeds': tfidf_vectorizer_breeds,
        'colors': tfidf_vectorizer_colors,
        'features': tfidf_vectorizer_features
    }

    return combined_features, tfidf_vectorizers, df_categorical.columns

def preprocess_preferences(preferences, tfidf_vectorizers, categorical_columns):
    # Convert the preferences to a DataFrame with each preference as a column
    preferences_df = pd.DataFrame([preferences])
    
    # One-hot encode the categorical features
    df_categorical = pd.get_dummies(preferences_df[['type', 'size', 'sex']])
    
    # Ensure all categorical columns are present
    for col in categorical_columns:
        if col not in df_categorical.columns:
            df_categorical[col] = 0

    df_categorical = df_categorical[categorical_columns]
    
    # Use TfidfVectorizer for 'breed', 'colors' and 'features'
    breeds_features = tfidf_vectorizers['breeds'].transform(preferences_df['breed'].apply(lambda x: ' '.join([x])))
    colors_features = tfidf_vectorizers['colors'].transform(preferences_df['colors'].apply(lambda x: ' '.join(x)))
    features_features = tfidf_vectorizers['features'].transform(preferences_df['features'].apply(lambda x: ' '.join(x)))
    
    combined_features = hstack([df_categorical, breeds_features, colors_features, features_features])
    
    return combined_features

def get_recommendations(preferences, pets, tfidf_vectorizers, categorical_columns):
    # Preprocess pets data
    pets_df, tfidf_vectorizers, categorical_columns = preprocess_data(pets)
    
    # Preprocess preferences data
    preferences_df = preprocess_preferences(preferences, tfidf_vectorizers, categorical_columns)
    
    # Train KNN model
    knn = NearestNeighbors(n_neighbors=10, metric='cosine')
    knn.fit(pets_df)
    
    # Find the top 10 recommendations
    distances, indices = knn.kneighbors(preferences_df)
    recommendations = [pets[i] for i in indices[0]]
    
    return recommendations

def generate_pets_data(n=40):
    pet_types = ['cat', 'dog']
    sizes = ['small', 'medium', 'large']
    sexes = ['male', 'female']
    breeds = ['breed1', 'breed2', 'breed3', 'breed4', 'breed5', 'randomBreed1', 'randomBreed2']
    colors = ['black', 'white', 'brown', 'gray', 'golden']
    features = ['friendly', 'playful', 'calm', 'energetic', 'quiet']
    
    pets = []
    
    for i in range(n):
        pet = {
            'id': f'pet{i}',
            'name': f'Pet{i}',
            'type': random.choice(pet_types),
            'sex': random.choice(sexes),
            'ageInYears': random.randint(1, 10),
            'size': random.choice(sizes),
            'breed': random.choice(breeds),
            'features': random.sample(features, k=random.randint(1, len(features))),
            'colors': random.sample(colors, k=random.randint(1, len(colors))),
            'imageURLs': [f'http://example.com/image{i}.jpg'],
            'shelterId': f'shelter{random.randint(1, 5)}',
            'adoptionStatus': 'available',
            'story': f'This is the story of Pet{i}.',
            'publishedAt': random.randint(1609459200, 1672531199)  # Timestamps for the year 2021
        }
        pets.append(pet)
    
    return pets

if __name__ == '__main__':
    app.run(debug=True, port=5000)