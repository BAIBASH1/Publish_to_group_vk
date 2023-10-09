import random
import os
import shutil
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv


BASE_URL_VKAPI = 'https://api.vk.com/method/'


def get_amount_xckd():
    url_xkcd = 'https://xkcd.com/info.0.json'
    response = requests.get(url_xkcd)
    response.raise_for_status()
    amount_xckd = response.json()['num']
    return amount_xckd


def download_new_xkcd(num_xkcd):
    url_xkcd = f'https://xkcd.com/{num_xkcd}/info.0.json'
    response = requests.get(url_xkcd)
    response.raise_for_status()
    xkcd_inf = response.json()
    xkcd_text = xkcd_inf['alt']
    xkcd_image_url = xkcd_inf['img']
    image = requests.get(xkcd_image_url)
    image.raise_for_status()
    os.makedirs('Files', exist_ok=True)
    with open(f'Files/image{num_xkcd}.jpg', 'ab') as file:
        file.write(image.content)
    with open(f'Files/message{num_xkcd}.txt', 'a') as file:
        file.write(xkcd_text)


def get_url_for_upload(main_params):
    api_url_upload = urljoin(BASE_URL_VKAPI, 'photos.getWallUploadServer')
    response_upload = requests.get(api_url_upload, params=main_params)
    response_upload.raise_for_status()
    url_for_download = response_upload.json()['response']['upload_url']
    return url_for_download


def save_image(main_params, params_for_save):
    url_for_save = urljoin(BASE_URL_VKAPI, 'photos.saveWallPhoto')
    params = {
        **main_params,
        **params_for_save
    }
    response_save = requests.get(url_for_save, params=params)
    response_save.raise_for_status()
    save_inf = response_save.json()
    image_id = save_inf['response'][0]['id']
    owner_id = save_inf['response'][0]['owner_id']
    return image_id, owner_id


def upload_and_save_photo(main_params, url_for_download, group_id, num_xkcd):
    with open(f'Files/image{num_xkcd}.jpg', 'rb') as file:
        files_upload = {
            'photo': file
        }
        params_for_upload = {
            **main_params,
            'group_id': group_id
        }
        response_upload = requests.post(url_for_download, params=params_for_upload, files=files_upload)
        response_upload.raise_for_status()
    params_for_save = response_upload.json()
    image_id, owner_id = save_image(main_params, params_for_save)
    return image_id, owner_id


def post_photo(main_params, group_id, image_id, owner_id, num_xkcd):
    url_for_post = urljoin(BASE_URL_VKAPI, 'wall.post')
    with open(f'Files/message{num_xkcd}.txt', 'r') as file:
        xkcd_text = file.read()
    params = {
        **main_params,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'attachments': f'photo{owner_id}_{image_id}',
        'message': xkcd_text
    }
    response_post = requests.post(url_for_post, params=params)
    response_post.raise_for_status()
    shutil.rmtree("Files")


def main():
    load_dotenv()
    vk_group_id = os.environ['VK_GROUP_ID']
    main_params = {
        'access_token': os.environ['VK_API_ACCESS_TOKEN'],
        'v': '5.150',
    }
    amount_xckd = get_amount_xckd()
    num_xkcd = random.randint(1, amount_xckd)
    download_new_xkcd(num_xkcd)
    url_for_upload = get_url_for_upload(main_params)
    image_id, owner_id = upload_and_save_photo(main_params, url_for_upload, vk_group_id, num_xkcd)
    post_photo(main_params, vk_group_id, image_id, owner_id, num_xkcd)


if __name__ == '__main__':
    main()
