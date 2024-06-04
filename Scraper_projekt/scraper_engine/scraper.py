import asyncio
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from flask import Flask, request, jsonify
from multiprocessing import Pool, cpu_count

app = Flask(__name__)

async def scrape_data(url):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, requests.get, url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = {}

    data['nazwa'] = [tag.text.strip() for tag in soup.find_all('h1', class_='e1i3khom9 ooa-1ed90th er34gjf0')]
    data['cena'] = [tag.text.strip() for tag in soup.find_all('h3', class_='e1i3khom16 ooa-1n2paoq er34gjf0')]
    data['informacja'] = [tag.text.strip() for tag in soup.find_all('p', class_='e1i3khom10 ooa-1tku07r er34gjf0')]
    data['przebieg'] = [tag.text.strip() for tag in soup.find_all('dd', {'data-parameter': 'mileage'})]
    data['paliwo'] = [tag.text.strip() for tag in soup.find_all('dd', {'data-parameter': 'fuel_type'})]
    data['rok'] = [tag.text.strip() for tag in soup.find_all('dd', {'data-parameter': 'year'})]
    data['skrzynia'] = [tag.text.strip() for tag in soup.find_all('dd', {'data-parameter': 'gearbox'})]
    data['link'] = [tag.find('a')['href'] for tag in soup.find_all('h1', class_='e1i3khom9 ooa-1ed90th er34gjf0') if tag.find('a')]
    data['zdjecie'] = [tag['src'] for tag in soup.find_all('img', class_='e17vhtca4 ooa-2zzg2s') if 'src' in tag.attrs]

    cars = [{key: value[i] for key, value in data.items()} for i in range(len(data['nazwa']))]

    return cars

async def save_to_mongodb(data, collection):
    client = MongoClient('mongodb://root:example@mongo:27017/')
    db = client['test_database']
    coll = db[collection]

    for item in data:
        if not coll.find_one({'link': item['link']}):
            coll.insert_one(item)
            print("Added to MongoDB:", item['link'])
        else:
            print("Link already exists in the database. Skipping:", item['link'])

def scrape_and_save(url):
    try:
        cars = asyncio.run(scrape_data(url))
        asyncio.run(save_to_mongodb(cars, 'car_collection'))
    except Exception as e:
        print(f"Error processing {url}: {e}")

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    urls = data.get('urls')
    if urls and isinstance(urls, list) and all(isinstance(url, str) for url in urls):
        with Pool(cpu_count()) as pool:
            pool.map(scrape_and_save, urls)
        return jsonify({'status': 'success'})
    return jsonify({'status': 'failed', 'reason': 'no urls provided or invalid format'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
