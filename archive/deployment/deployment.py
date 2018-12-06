import json
import argparse

from app import run_safe

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3_url', type=str, help='Object storage endpoint')
    parser.add_argument('--bucket_name', type=str, help='Object storage bucket name')
    parser.add_argument('--s3_username', type=str, help='Object storage access key id')
    parser.add_argument('--s3_password', type=str, help='Object storage access key secret')
    parser.add_argument('--model_id', type=str, help='Training model id')
    parser.add_argument('--metric_path', type=str, help='Path for robustness check output')
    parser.add_argument('--seldon_ip', type=str, help='IP for the seldon service')
    args = parser.parse_args()

    s3_url = args.s3_url
    bucket_name = args.bucket_name
    s3_username = args.s3_username
    s3_password = args.s3_password
    metric_path = args.metric_path
    model_id = args.model_id
    seldon_ip = args.seldon_ip

    formData = {
        "public_ip": seldon_ip,
        "aws_endpoint_url": s3_url,
        "aws_access_key_id": s3_username,
        "aws_secret_access_key": s3_password,
        "training_results_bucket": bucket_name,
        "model_file_name": "model.pt",
        "deployment_name": model_id,
        "training_id": model_id,
        "container_image": "tomcli/seldon-gender:0.5",
        "check_status_only": False
    }

    metrics = run_safe(formData, "POST")
    print(metrics)

    with open(metric_path, "w") as report:
        report.write(json.dumps(metrics))
