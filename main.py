from flask import Flask, jsonify
from firebase_admin import credentials, firestore, initialize_app
from difflib import SequenceMatcher

app = Flask(__name__)

# initialize firebase
cred = credentials.Certificate("key.json")
default_app = initialize_app(cred)
db = firestore.client()

@app.route('/')
def hello_world():
    return '<h1>Hello, World!</h1>'

# in route of a user id
@app.route('/recommendations/<userId>', methods=['GET'])
def user(userId):
    # get user data from firestore
    user = db.collection('users').document(userId).get().to_dict()

    # get a snapshot of the pets collection
    pets = db.collection('pets').get()
    pets = [pet.to_dict() for pet in pets]

    # get user preferences
    preferences = db.collection('preferences').document(userId).get().to_dict()

    if preferences is None:
        return jsonify({'error': 'No preferences found'}), 500

    # get recommendations
    recommendations = get_recommendations(preferences, pets)

    if recommendations is None:
        return jsonify({'error': 'No recommendations found'}), 500

    return jsonify(recommendations)


def get_recommendations(preferences, pets):
    # for each pet, calculate a match score
    for pet in pets:
        print(pet)
        pet['score'] = score_pet(pet, preferences)
    # sort pets by match score
    pets.sort(key=lambda pet: pet['score'], reverse=True)
    return pets

def score_pet(pet, preferences):
    
    scores = []
    if preferences['type'] is not None:
        scores.append(score_type(pet, preferences))
    if preferences['size'] is not None:
        scores.append(score_size(pet, preferences))
    if preferences['breed'] is not None:
        scores.append(score_breed(pet, preferences))
    if preferences['colors'] is not None:
        scores.append(score_colors(pet, preferences))
    if preferences['features'] is not None:
        scores.append(score_features(pet, preferences))
    return sum(scores) / len(scores)

def score_type(pet, preference):
    # return 1 if pet type matches preference type, 0 otherwise
    return 1 if isSimilar(pet['type'], preference['type']) else 0

def score_size(pet, preference):
    # return 1 if pet size matches preference size, 0 otherwise
    # use isSimilar function to compare strings
    return 1 if isSimilar(pet['size'], preference['size']) else 0


def score_breed(pet, preference):   
    # return 1 if pet breed matches preference breed, 0 otherwise
    # use isSimilar function to compare strings
    return 1 if isSimilar(pet['breed'], preference['breed']) else 0

def score_colors(pet, preference):
    # return 1 if pet colors match preference colors, 0 otherwise
    # use isSimilar function to compare strings
    # calculate the average of all colors
    score = 0
    for color in pet['colors']:
        score += max([isSimilar(color, pref_color) for pref_color in preference['colors']])
    return score / len(preference['colors'])

def score_features(pet, preference):
    score = 0
    for feature in pet['features']:
        score += max([isSimilar(feature, pref_feature) for pref_feature in preference['features']])
    return score / len(preference['features'])

def normalize_string(value):
    temp = value.lower().strip()
    normal_chars = {
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'ü': 'u',
        'ñ': 'n'
    }
    for special_char, normal_char in normal_chars.items():
        temp = temp.replace(special_char, normal_char)
    return temp
    
def isSimilar(word, target):
    word = normalize_string(word)
    target = normalize_string(target)
    return SequenceMatcher(None, word, target).ratio() > 0.8

if __name__ == '__main__':
    app.run(debug=True, port=5000)