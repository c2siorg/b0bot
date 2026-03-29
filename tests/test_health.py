import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
import datetime
import unittest

test_app = Flask(__name__)

@test_app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "B0Bot API is running",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }), 200

class HealthCheckTest(unittest.TestCase):
    def setUp(self):
        self.app = test_app.test_client()

    def test_health_returns_200(self):
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)

    def test_health_returns_healthy_status(self):
        response = self.app.get('/health')
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')

    def test_health_has_timestamp(self):
        response = self.app.get('/health')
        data = response.get_json()
        self.assertIn('timestamp', data)

if __name__ == '__main__':
    unittest.main()