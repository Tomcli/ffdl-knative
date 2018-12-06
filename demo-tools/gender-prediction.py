from PIL import Image
import numpy as np
import requests
import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--pic_path', type=str, help='Picture Path for the gender prediction')
    parser.add_argument('--model_url', type=str, help='Seldon URL for the gender classification model')
    parser.add_argument('--loop', type=bool, help='Produce traffic with forever loop', default=False)
    args = parser.parse_args()

    pic_path = args.pic_path
    model_url = args.model_url
    loop = args.loop

    images = []
    image = np.array(Image.open(pic_path).resize((64, 64)))[:, :, :3]
    images.append(image.tolist())
    request = {"inputs": images}
    response = requests.post(model_url, json=request)
    print(response.json())

    while loop:
        images = []
        image = np.array(Image.open(pic_path).resize((64, 64)))[:, :, :3]
        images.append(image.tolist())
        request = {"inputs": images}
        response = requests.post(model_url, json=request)
        print(response.json())
