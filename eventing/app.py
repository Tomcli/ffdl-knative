import os
import json

from flask import Flask, request, abort
from flask_cors import CORS
import requests
import argparse

app = Flask(__name__)
CORS(app)

# Server approach
# @app.route('/eventing', methods=['OPTIONS'])
# def eventing_api_options():
#     return "200"
#
#
# @app.route('/eventing', methods=['POST'])
# def eventing_api_post():
#     try:
#         s3_url = request.json['aws_endpoint_url']
#         output_bucket_name = request.json['training_results_bucket']
#         experiment = request.json['experiment']
#         s3_username = request.json['aws_access_key_id']
#         s3_password = request.json['aws_secret_access_key']
#         model_id = request.json['model_id']
#         postparam = {"aws_endpoint_url": s3_url,
#                      "training_results_bucket": output_bucket_name,
#                      "aws_access_key_id": s3_username,
#                      "aws_secret_access_key": s3_password,
#                      "model_id": model_id,
#                      "deployment_name": experiment,
#                      "model_file_name": "model.pt",
#                      "training_id": model_id,
#                      "container_image": "tomcli/gender-serving:0.1",
#                      "check_status_only": False,
#                      "public_ip": "xxx.xx.xxx.xx"}
#         global sink
#         requests.post(sink, json=postparam)
#     except:
#         abort(400)
#     return json.dumps({"status": "Triggered"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sink', type=str, help='sink object endpoint',
                        default="")
    parser.add_argument('--aws_endpoint_url', type=str, help='')
    parser.add_argument('--training_results_bucket', type=str, help='')
    parser.add_argument('--experiment', type=str, help='')
    parser.add_argument('--aws_access_key_id', type=str, help='')
    parser.add_argument('--aws_secret_access_key', type=str, help='')
    parser.add_argument('--model_id', type=str, help='')

    args = parser.parse_args()
    sink = args.sink
    s3_url = args.aws_endpoint_url
    output_bucket_name = args.training_results_bucket
    experiment = args.experiment
    s3_username = args.aws_access_key_id
    s3_password = args.aws_secret_access_key
    model_id = args.model_id
    postparam = {"aws_endpoint_url": s3_url,
                 "training_results_bucket": output_bucket_name,
                 "aws_access_key_id": s3_username,
                 "aws_secret_access_key": s3_password,
                 "model_id": model_id,
                 "deployment_name": experiment,
                 "model_file_name": "model.pt",
                 "training_id": model_id,
                 "container_image": "tomcli/gender-serving:0.1",
                 "check_status_only": False,
                 "public_ip": "xxx.xx.xxx.xx"}
    requests.post(sink, json=postparam)

    # Server code
    # app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
