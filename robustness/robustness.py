"""Robustness check module."""

import numpy as np
import numpy.linalg as la
import boto3
import botocore

import torch
import torch.utils.data
from torch.autograd import Variable

from art.classifiers.pytorch import PyTorchClassifier
from art.attacks.fast_gradient import FastGradientMethod


class ThreeLayerCNN(torch.nn.Module):

    """
    Input: 128x128 face image (eye aligned).
    Output: 1-D tensor with 2 elements. Used for binary classification.
    Parameters:
        Number of conv layers: 3
        Number of fully connected layers: 2
    """

    def __init__(self):
        super(ThreeLayerCNN,self).__init__()
        self.conv1 = torch.nn.Conv2d(3,6,5)
        self.pool = torch.nn.MaxPool2d(2,2)
        self.conv2 = torch.nn.Conv2d(6,16,5)
        self.conv3 = torch.nn.Conv2d(16,16,6)
        self.fc1 = torch.nn.Linear(16*4*4,120)
        self.fc2 = torch.nn.Linear(120,2)


    def forward(self, x):
        x = self.pool(torch.nn.functional.relu(self.conv1(x)))
        x = self.pool(torch.nn.functional.relu(self.conv2(x)))
        x = self.pool(torch.nn.functional.relu(self.conv3(x)))
        x = x.view(-1, 16*4*4)
        x = torch.nn.functional.relu(self.fc1(x))
        x = self.fc2(x)
        return x


def get_metrics(model, x_original, x_adv_samples, y):
    model_accuracy_on_non_adversarial_samples, y_pred = evaluate(model, x_original, y)
    model_accuracy_on_adversarial_samples, y_pred_adv = evaluate(model, x_adv_samples, y)

    pert_metric = get_perturbation_metric(x_original, x_adv_samples, y_pred, y_pred_adv, ord=2)
    conf_metric = get_confidence_metric(y_pred, y_pred_adv)

    data = {
        "model accuracy on test data": float(model_accuracy_on_non_adversarial_samples),
        "model accuracy on adversarial samples": float(model_accuracy_on_adversarial_samples),
        "confidence reduced on correctly classified adv_samples": float(conf_metric),
        "average perturbation on misclassified adv_samples": float(pert_metric)
    }
    return data, y_pred, y_pred_adv


def evaluate(model, X_test, y_test):
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    test = torch.utils.data.TensorDataset(Variable(torch.FloatTensor(X_test.astype('float32'))), Variable(torch.LongTensor(y_test.astype('float32'))))
    test_loader = torch.utils.data.DataLoader(test, batch_size=64, shuffle=False)
    model.eval()
    correct = 0
    accuracy = 0
    y_pred = []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            predictions = torch.softmax(outputs.data, dim=1).detach().numpy()
            correct += predicted.eq(labels.data.view_as(predicted)).sum().item()
            y_pred += predictions.tolist()
        accuracy = 1. * correct / len(test_loader.dataset)
    y_pred = np.array(y_pred)
    return accuracy, y_pred


def get_perturbation_metric(x_original, x_adv, y_pred, y_pred_adv, ord=2):
    idxs = (np.argmax(y_pred_adv, axis=1) != np.argmax(y_pred, axis=1))

    if np.sum(idxs) == 0.0:
        return 0

    perts_norm = la.norm((x_adv - x_original).reshape(x_original.shape[0], -1), ord, axis=1)
    perts_norm = perts_norm[idxs]

    return np.mean(perts_norm / la.norm(x_original[idxs].reshape(np.sum(idxs), -1), ord, axis=1))


# This computes the change in confidence for all images in the test set
def get_confidence_metric(y_pred, y_pred_adv):
    y_classidx = np.argmax(y_pred, axis=1)
    y_classconf = y_pred[np.arange(y_pred.shape[0]), y_classidx]

    y_adv_classidx = np.argmax(y_pred_adv, axis=1)
    y_adv_classconf = y_pred_adv[np.arange(y_pred_adv.shape[0]), y_adv_classidx]

    idxs = (y_classidx == y_adv_classidx)

    if np.sum(idxs) == 0.0:
        return 0

    idxnonzero = y_classconf != 0
    idxs = idxs & idxnonzero

    return np.mean((y_classconf[idxs] - y_adv_classconf[idxs]) / y_classconf[idxs])

def get_s3_item(client, bucket, s3_path, name):
    try:
        client.Bucket(bucket).download_file(s3_path, name)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise


def robustness_check(s3_url, bucket_name, s3_username, s3_password, model_id, epsilon=0.2):

    global network_definition_filename, weights_filename, dataset_filename

    cos = boto3.resource("s3",
                         endpoint_url=s3_url,
                         aws_access_key_id=s3_username,
                         aws_secret_access_key=s3_password)

    dataset_filenamex = "x_test.npy"
    dataset_filenamey = "y_test.out"
    weights_filename = "model.pt"
    get_s3_item(cos, bucket_name, model_id + '/' + dataset_filenamex, dataset_filenamex)
    get_s3_item(cos, bucket_name, model_id + '/' + dataset_filenamey, dataset_filenamey)
    get_s3_item(cos, bucket_name, model_id + '/' + weights_filename, weights_filename)

    # load & compile model
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    model = ThreeLayerCNN().to(device)
    model.load_state_dict(torch.load(weights_filename))
    loss_fn = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # create pytorch classifier
    classifier = PyTorchClassifier((0, 1), model, loss_fn, optimizer, (1,3,64,64), 2)

    # load data set
    x = np.load(dataset_filenamex)
    y = np.loadtxt(dataset_filenamey)

    # craft adversarial samples using FGSM
    crafter = FastGradientMethod(classifier, eps=epsilon)
    x_samples = crafter.generate(x)

    # obtain all metrics (robustness score, perturbation metric, reduction in confidence)
    metrics, y_pred_orig, y_pred_adv = get_metrics(model, x, x_samples, y)

    print("metrics:", metrics)
    return metrics
