import pytest
from my_project.app import create_app
from my_project.database import db

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Welcome to My Project" in response.data
