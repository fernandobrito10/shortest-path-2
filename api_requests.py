import requests

url = "https://api.themoviedb.org/3/configuration"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjMGJmZmViNmZlZTdiYjVhZDE0ZjU0MjQ0OGY0ODMwMCIsIm5iZiI6MTcyODMwMTg2NS44MjI4OTEsInN1YiI6IjY3MDNjOWNlY2M5MDRmMTJkOTEzOTQxNCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.F9jQ2kIk7yvJRXFB51AQYnAV5agEom_HDoeW2WSMLKs"
}

response = requests.get(url, headers=headers)

print(response.text)