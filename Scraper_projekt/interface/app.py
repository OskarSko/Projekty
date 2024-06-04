import json
import time
import docker
from flask import Flask, request, redirect, render_template, jsonify, url_for
from pymongo import MongoClient
import requests

app = Flask(__name__)
client = docker.from_env()

def get_db():
    client = MongoClient('mongodb://root:example@mongo:27017/')
    db = client['test_database']
    return db

@app.route('/')
def index():
    with open('links.json', 'r') as f:
        links = json.load(f)
    brands = list(links.keys())
    
    db = get_db()
    collection = db['car_collection']
    cars = list(collection.find({}, {'_id': 0}))
    return render_template("index.html", brands=brands, cars=cars)

@app.route('/cars')
def cars():
    db = get_db()
    collection = db['car_collection']
    cars = list(collection.find({}, {'_id': 0}))
    return jsonify(cars)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    db = get_db()
    collection = db['car_collection']
    
    cars = list(collection.find({'nazwa': {'$regex': query, '$options': 'i'}}, {'_id': 0}))
    
    return jsonify(cars)

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if request.method == 'POST':
        brands = request.form.getlist('brand')  # Get multiple selected brands
        with open('links.json', 'r') as f:
            links = json.load(f)
        
        selected_links = [links[brand] for brand in brands if brand in links]
        
        if selected_links:
            container = client.containers.get('projekt_scraper-scraper_engine-1')
            container.restart()  # Restart container to ensure the latest code is running
            time.sleep(5)  # Give some time for the container to restart
            
            flat_links = [url for sublist in selected_links for url in sublist]  # Flatten the list of lists
            
            response = requests.post('http://projekt_scraper-scraper_engine-1:5001/scrape', json={'urls': flat_links})
            if response.status_code == 200:
                return redirect(url_for('index'))
            else:
                return f"Scraping failed: {response.text}", 500
        else:
            return "No valid brands found", 404
    else:
        with open('links.json', 'r') as f:
            links = json.load(f)
        brands = list(links.keys())
        return render_template('scrape.html', brands=brands)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
