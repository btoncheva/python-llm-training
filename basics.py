# basics.py

def describe_person(person):
    name = person.get("name", "Unknown")
    age = person.get("age", 0)
    languages = person.get("languages", [])

    print(f"Name: {name}")
    print(f"Age: {age}")
    print(f"Languages known:")
    for lang in languages:
        print(f"  - {lang}")

people = [
    {"name": "Alice", "age": 30, "languages": ["Java", "Python"]},
    {"name": "Bob",   "age": 25, "languages": ["Python", "Go"]},
]

for person in people:
    describe_person(person)
    print("---")