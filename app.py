from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import heapq

app = Flask(__name__)

CACHE_FILE = "cache.json"
SEARCHES_FILE = "searches.json"  # Arquivo para armazenar as buscas

# Função para salvar o cache em um arquivo JSON
def save_cache_to_file():
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)
    print("Cache salvo no arquivo")  # Log

# Função para carregar o cache a partir do arquivo JSON
def load_cache_from_file():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

# Função para salvar as buscas em um arquivo JSON
def save_searches_to_file():
    with open(SEARCHES_FILE, 'w') as f:
        json.dump(searches, f)
    print("Buscas salvas no arquivo")  # Log

# Função para carregar as buscas a partir do arquivo JSON
def load_searches_from_file():
    if os.path.exists(SEARCHES_FILE):
        with open(SEARCHES_FILE, 'r') as f:
            return json.load(f)
    return {}

# Carregando o cache e as buscas no início do programa
cache = load_cache_from_file()
searches = load_searches_from_file()

# Função para buscar o ID do ator
def get_actor_id(actor_name):
    api_key = os.getenv('TMDB_API_KEY')
    url = f"https://api.themoviedb.org/3/search/person?api_key={api_key}&query={actor_name}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            print(f"Encontrado ID {data['results'][0]['id']} para o ator {actor_name}")  # Log
            return data['results'][0]['id']
    print(f"ID não encontrado para o ator {actor_name}")  # Log
    return None

# Função para buscar os filmes de um ator
def get_actor_movies(actor_id):
    if actor_id in cache:
        print(f"Usando cache para os filmes do ator {actor_id}")  # Log
        return cache[actor_id]
    
    api_key = os.getenv('TMDB_API_KEY')
    url = f"https://api.themoviedb.org/3/person/{actor_id}/movie_credits?api_key={api_key}"
    response = requests.get(url)
    
    if response.status_code == 200:
        movies = [
            movie for movie in response.json().get('cast', [])
            if 'release_date' in movie  # Exclui séries e documentários
        ]
        
        sorted_movies = sorted(movies, key=lambda movie: movie.get('popularity', 0), reverse=True)
        top_movies = sorted_movies[:20]  # Limita a 20 filmes mais populares
        movies_dict = {movie['id']: movie['title'] for movie in top_movies}
        
        print(f"Filmes encontrados para o ator {actor_id}: {list(movies_dict.values())}")  # Log
        cache[actor_id] = movies_dict  # Armazena no cache
        save_cache_to_file()  # Salva o cache em disco
        return movies_dict

    print(f"Nenhum filme encontrado para o ator {actor_id}")  # Log
    return {}

# Função A* para encontrar o caminho mais curto entre dois atores
def a_star_search(actor1_id, actor2_id, max_depth=7):
    print(f"Iniciando busca A* entre os atores {actor1_id} e {actor2_id}")  # Log
    queue = [(0, actor1_id, [])]
    visited = set()

    while queue:
        estimated_cost, current_actor_id, path = heapq.heappop(queue)

        if current_actor_id in visited:
            continue
        
        visited.add(current_actor_id)
        current_movies = get_actor_movies(current_actor_id)

        if not current_movies:
            continue

        for movie_id, movie_title in current_movies.items():
            new_path = path + [(current_actor_id, movie_title)]
            
            movie_credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={os.getenv('TMDB_API_KEY')}"
            response = requests.get(movie_credits_url)
            if response.status_code == 200:
                cast = response.json().get('cast', [])
                for actor in cast:
                    if actor['id'] == actor2_id:
                        # Armazena a busca na direção original e inversa
                        searches[f"{actor1_id}-{actor2_id}"] = new_path + [(actor2_id, get_actor_name(actor2_id))]
                        searches[f"{actor2_id}-{actor1_id}"] = new_path + [(actor1_id, get_actor_name(actor1_id))]
                        save_searches_to_file()  # Salva as buscas em disco
                        print(f"Rota encontrada: {new_path + [(actor2_id, get_actor_name(actor2_id))]}")  # Log
                        return new_path + [(actor2_id, get_actor_name(actor2_id))]
                    if actor['id'] not in visited:
                        estimated_new_cost = len(new_path) + 1
                        heapq.heappush(queue, (estimated_new_cost, actor['id'], new_path))

    print("Nenhuma rota encontrada")  # Log
    return None

# Função para obter o nome do ator pelo ID
def get_actor_name(actor_id):
    api_key = os.getenv('TMDB_API_KEY')
    url = f"https://api.themoviedb.org/3/person/{actor_id}?api_key={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('name', 'Unknown Actor')
    return 'Unknown Actor'

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Rota para buscar filmes em comum
@app.route('/filmes_comuns', methods=['POST'])
def filmes_comuns():
    ator1 = request.form['ator1']
    ator2 = request.form['ator2']
    
    if not ator1 or not ator2:
        return render_template('index.html', error="Você precisa fornecer dois atores.")
    
    ator1_id = get_actor_id(ator1)
    ator2_id = get_actor_id(ator2)
    
    if not ator1_id or not ator2_id:
        return render_template('index.html', error="Não foi possível encontrar um ou ambos os atores.")
    
    # Primeiro verifica se há filmes em comum
    ator1_filmes = get_actor_movies(ator1_id)
    ator2_filmes = get_actor_movies(ator2_id)
    filmes_comuns = set(ator1_filmes.keys()) & set(ator2_filmes.keys())
    
    if filmes_comuns:
        # Coleta todos os filmes em comum
        filmes_em_comum = [ator1_filmes[filme_id] for filme_id in filmes_comuns]
        filmes_em_comum_str = ", ".join(filmes_em_comum)  # Converte a lista em uma string
        print(f"Filmes comuns encontrados: {filmes_em_comum}")  # Log
        return render_template('index.html', error=f"Filmes em comum: {filmes_em_comum_str}")
    
    # Se não houver filmes em comum, busca o caminho
    if f"{ator1_id}-{ator2_id}" in searches:
        print(f"Usando busca armazenada para {ator1} e {ator2}")  # Log
        caminho = " -> ".join([f"{get_actor_name(actor_id)} em '{movie}'" for actor_id, movie in searches[f"{ator1_id}-{ator2_id}"]])
        return render_template('index.html', error=f"Rota encontrada (armazenada): {caminho}")

    route = a_star_search(ator1_id, ator2_id)
    if route:
        caminho = " -> ".join([f"{get_actor_name(actor_id)} em '{movie}'" for actor_id, movie in route])
        return render_template('index.html', error=f"Rota encontrada: {caminho}")
    else:
        return render_template('index.html', error="Não foi encontrado nenhum filme em comum nem rota entre os atores.")


@app.route('/buscar_atores', methods=['GET'])
def buscar_atores():
    query = request.args.get('query')
    api_key = os.getenv('TMDB_API_KEY')
    url = f"https://api.themoviedb.org/3/search/person?api_key={api_key}&query={query}&include_adult=false"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Mapeia os resultados para incluir apenas o necessário
        resultados = [{
            'name': ator['name'],
            'profile_path': ator['profile_path']  # Inclui o caminho da imagem
        } for ator in data['results']]
        return jsonify({'results': resultados})
    
    return jsonify({'results': []})


if __name__ == "__main__":
    app.run()
