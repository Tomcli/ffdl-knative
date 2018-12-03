import os
from aif360.datasets import BinaryLabelDataset
from aif360.metrics import ClassificationMetric
import numpy as np
import argparse
import pandas as pd
import boto3
import botocore
import json

from flask import Flask, request, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def dataset_wrapper(outcome, protected, unprivileged_groups, privileged_groups, favorable_label, unfavorable_label):
    """ A wrapper function to create aif360 dataset from outcome and protected in numpy array format.
    """
    df = pd.DataFrame(data=outcome,
                      columns=['outcome'])
    df['race'] = protected

    dataset = BinaryLabelDataset(favorable_label=favorable_label,
                                 unfavorable_label=unfavorable_label,
                                 df=df,
                                 label_names=['outcome'],
                                 protected_attribute_names=['race'],
                                 unprivileged_protected_attributes=unprivileged_groups)
    return dataset

def get_s3_item(client, bucket, s3_path, name):
    try:
        client.Bucket(bucket).download_file(s3_path, name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


def fairness_check(s3_url, bucket_name, s3_username, s3_password, training_id):

    cos = boto3.resource("s3",
                         endpoint_url=s3_url,
                         aws_access_key_id=s3_username,
                         aws_secret_access_key=s3_password)

    y_test_out = 'y_test.out'
    p_test_out = 'p_test.out'
    y_pred_out = 'y_pred.out'
    get_s3_item(cos, bucket_name, training_id + '/' + y_test_out, y_test_out)
    get_s3_item(cos, bucket_name, training_id + '/' + p_test_out, p_test_out)
    get_s3_item(cos, bucket_name, training_id + '/' + y_pred_out, y_pred_out)


    """Need to generalize the protected features"""

    unprivileged_groups = [{'race': 4.0}]
    privileged_groups = [{'race': 0.0}]
    favorable_label = 0.0
    unfavorable_label = 1.0

    """Load the necessary labels and protected features for fairness check"""

    y_test = np.loadtxt(y_test_out)
    p_test = np.loadtxt(p_test_out)
    y_pred = np.loadtxt(y_pred_out)

    """Calculate the fairness metrics"""

    original_test_dataset = dataset_wrapper(outcome=y_test, protected=p_test,
                                            unprivileged_groups=unprivileged_groups,
                                            privileged_groups=privileged_groups,
                                            favorable_label=favorable_label,
                                            unfavorable_label=unfavorable_label)
    plain_predictions_test_dataset = dataset_wrapper(outcome=y_pred, protected=p_test,
                                                     unprivileged_groups=unprivileged_groups,
                                                     privileged_groups=privileged_groups,
                                                     favorable_label=favorable_label,
                                                     unfavorable_label=unfavorable_label)

    classified_metric_nodebiasing_test = ClassificationMetric(original_test_dataset,
                                                              plain_predictions_test_dataset,
                                                              unprivileged_groups=unprivileged_groups,
                                                              privileged_groups=privileged_groups)
    TPR = classified_metric_nodebiasing_test.true_positive_rate()
    TNR = classified_metric_nodebiasing_test.true_negative_rate()
    bal_acc_nodebiasing_test = 0.5*(TPR+TNR)

    print("#### Plain model - without debiasing - classification metrics on test set")

    metrics = {
        "Classification accuracy": classified_metric_nodebiasing_test.accuracy(),
        "Balanced classification accuracy": bal_acc_nodebiasing_test,
        "Statistical parity difference": classified_metric_nodebiasing_test.statistical_parity_difference(),
        "Disparate impact": classified_metric_nodebiasing_test.disparate_impact(),
        "Equal opportunity difference": classified_metric_nodebiasing_test.equal_opportunity_difference(),
        "Average odds difference": classified_metric_nodebiasing_test.average_odds_difference(),
        "Theil index": classified_metric_nodebiasing_test.theil_index(),
        "False negative rate difference": classified_metric_nodebiasing_test.false_negative_rate_difference()
    }
    print("metrics: ", metrics)
    return metrics

    # with open(metric_path, "w") as report:
    #     report.write(json.dumps(metrics))


@app.route('/', methods=['POST'])
def fairness_api():
    try:
        s3_url = request.json['aws_endpoint_url']
        bucket_name = request.json['training_results_bucket']
        s3_username = request.json['aws_access_key_id']
        s3_password = request.json['aws_secret_access_key']
        training_id = request.json['model_id']
    except:
        abort(400)
    return json.dumps(fairness_check(s3_url, bucket_name, s3_username, s3_password, training_id))


@app.route('/', methods=['OPTIONS'])
def fairness_api_options():
    return "200"

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT', 8080)))
