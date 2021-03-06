import json
import argparse

from robustness import robustness_check

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--s3_url', type=str, help='Object storage endpoint')
    parser.add_argument('--bucket_name', type=str, help='Object storage bucket name')
    parser.add_argument('--s3_username', type=str, help='Object storage access key id')
    parser.add_argument('--s3_password', type=str, help='Object storage access key secret')
    parser.add_argument('--epsilon', type=float, help='Epsilon value for the FGSM attack')
    parser.add_argument('--model_id', type=str, help='Training model id')
    parser.add_argument('--metric_path', type=str, help='Path for robustness check output')
    args = parser.parse_args()

    s3_url = args.s3_url
    bucket_name = args.bucket_name
    s3_username = args.s3_username
    s3_password = args.s3_password
    epsilon = args.epsilon
    metric_path = args.metric_path
    model_id = args.model_id

    metrics = robustness_check(s3_url, bucket_name, s3_username, s3_password, model_id, epsilon)

    with open(metric_path, "w") as report:
        report.write(json.dumps(metrics))
