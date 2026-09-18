import requests
import json

def fetch_todos(user_id):
    url = f"https://jsonplaceholder.typicode.com/todos"
    params = {"userId": user_id}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed: {response.status_code}")
        return []

def save_to_file(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} items to {filename}")

def load_from_file(filename):
    with open(filename, "r") as f:
        return json.load(f)

# Fetch todos for user 1
todos = fetch_todos(1)

# Show first 3
for todo in todos[:3]:
    status = "done" if todo.get("completed") else "pending"
    print(f"[{status}] {todo.get('title')}")

# Save all to file
save_to_file(todos, "todos.json")

# Reload and confirm
reloaded = load_from_file("todos.json")
print(f"Reloaded {len(reloaded)} todos from file")