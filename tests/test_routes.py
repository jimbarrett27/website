from app.routes import fetch_project_euler_solution
import pytest


from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    yield app.test_client()
         
def test_project_euler_route(client):

    problem_numbers_and_solutions = {
        1: 233168,
        2: 4613732,
        3: 6857,
        4: 906609,
        5: 232792560,
        6: 25164150,
        7: 104743,
        # 8: 23514624000,
        9: 31875000,
        10: 142913828922,
        # 11: 70600674,
        12: 76576500,
        # 13: 5537376230,
        14: 837799,
        15: 137846528820,
        16: 1366,
        17: 21124,
        # 18: 1074,
        19: 171,
        20: 648,
        21: 31626,
        # 22: 871198282,
        23: 4179871,
        # 50: 997651,
        # 67: 7273
    }

    for problem_number, correct_answer in problem_numbers_and_solutions.items():
        resp = client.get(f'/project_euler_solution/{problem_number}')
        answer = int(resp.data.decode('utf-8'))
        assert answer == correct_answer

