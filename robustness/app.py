import os
import json

from flask import Flask, request, abort
from flask_cors import CORS

from robustness import robustness_check

app = Flask(__name__)
CORS(app)


@app.route('/', methods=['POST'])
def robustness_api():
    try:
        s3_url = request.json['aws_endpoint_url']
        bucket_name = request.json['training_results_bucket']
        s3_username = request.json['aws_access_key_id']
        s3_password = request.json['aws_secret_access_key']
        model_id = request.json['model_id']
    except:
        abort(400)
    return json.dumps(robustness_check(s3_url, bucket_name, s3_username, s3_password, model_id))

@app.route('/', methods=['OPTIONS'])
def robustness_api_options():
    return "200"


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
