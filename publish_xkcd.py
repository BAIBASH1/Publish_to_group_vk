import random
import os
import shutil
from pathlib import Path
from urllib.parse import urljoin
import requests
from dotenv import load_dotenv


BASE_URL_VKAPI = 'https://api.vk.com/method/'


class VkApiError(Exception):
    def __init__(self, error_code, error_message):
        self.code = error_code
        self.message = error_message

    def __str__(self):
        return f'error_code: {self.code}, error_message: {self.message}'


def catch_error(parsed_response):
    if parsed_response.get('error'):
        error_code = parsed_response['error']['error_code']
        error_message = parsed_response['error']['error_msg']

        raise VkApiError(error_code, error_message)



def get_amount_xckd():
    url_xkcd = 'https://xkcd.com/info.0.json'
    response = requests.get(url_xkcd)
    response.raise_for_status()
    amount_xckd = response.json()['num']
    return amount_xckd


def download_new_xkcd(xkcd_num):
    url_xkcd = f'https://xkcd.com/{xkcd_num}/info.0.json'
    response = requests.get(url_xkcd)
    response.raise_for_status()
    xkcd_inf = response.json()
    xkcd_text = xkcd_inf['alt']
    xkcd_image_url = xkcd_inf['img']
    xkcd_image = requests.get(xkcd_image_url)
    xkcd_image.raise_for_status()
    path_to_image = Path('Files', f'image{xkcd_num}.jpg')
    with open(path_to_image, 'ab') as file:
        file.write(xkcd_image.content)
    return xkcd_text, path_to_image


def get_upload_url(vk_api_access_token, vk_api_version):
    url_for_upload_request = urljoin(BASE_URL_VKAPI, 'photos.getWallUploadServer')
    params = {
        'access_token': vk_api_access_token,
        'v': vk_api_version
    }
    upload_response = requests.get(url_for_upload_request, params=params)
    upload_response.raise_for_status()
    parsed_response = upload_response.json()
    catch_error(parsed_response)
    upload_url = parsed_response['response']['upload_url']
    return upload_url


def save_image(vk_api_access_token, vk_api_version, server, photo, hash_for_save):
    url_for_save = urljoin(BASE_URL_VKAPI, 'photos.saveWallPhoto')
    params = {
        'access_token': vk_api_access_token,
        'v': vk_api_version,
        'server': server,
        'photo': photo,
        'hash': hash_for_save
    }
    save_response = requests.get(url_for_save, params=params)
    save_response.raise_for_status()
    parsed_save_response = save_response.json()
    catch_error(parsed_save_response)
    image_id = parsed_save_response['response'][0]['id']
    owner_id = parsed_save_response['response'][0]['owner_id']
    return image_id, owner_id


def upload_photo(vk_api_access_token, vk_api_version, upload_url, vk_group_id, path_to_image):
    with open(path_to_image, 'rb') as file:
        upload_files = {
            'photo': file
        }
        params_for_upload = {
            'access_token': vk_api_access_token,
            'v': vk_api_version,
            'group_id': vk_group_id
        }
        upload_response = requests.post(upload_url, params=params_for_upload, files=upload_files)
    upload_response.raise_for_status()
    params_for_save = upload_response.json()
    catch_error(params_for_save)
    server = params_for_save['server']
    photo = params_for_save['photo']
    hash_for_save = params_for_save['hash']
    return server, photo, hash_for_save


def post_photo(vk_api_access_token, vk_api_version, vk_group_id, image_id, owner_id, xkcd_text):
    url_for_post = urljoin(BASE_URL_VKAPI, 'wall.post')
    params = {
        'access_token': vk_api_access_token,
        'v': vk_api_version,
        'owner_id': f'-{vk_group_id}',
        'from_group': 1,
        'attachments': f'photo{owner_id}_{image_id}',
        'message': xkcd_text
    }
    post_response = requests.post(url_for_post, params=params)
    post_response.raise_for_status()
    parsed_post_response = post_response.json()
    catch_error(parsed_post_response)



def main():
    try:
        load_dotenv()
        vk_group_id = os.environ['VK_GROUP_ID']
        vk_api_access_token = os.environ['VK_API_ACCESS_TOKEN']
        vk_api_version = '5.150'
        xkcd_amount = get_amount_xckd()
        xkcd_num = random.randint(1, xkcd_amount)
        os.makedirs('Files', exist_ok=True)
        xkcd_text, path_to_image = download_new_xkcd(xkcd_num)
        upload_url = get_upload_url(vk_api_access_token, vk_api_version)
        server, photo, hash_for_save = upload_photo(vk_api_access_token, vk_api_version, upload_url, vk_group_id, path_to_image)
        image_id, owner_id = save_image(vk_api_access_token, vk_api_version, server, photo, hash_for_save)
        post_photo(vk_api_access_token, vk_api_version, vk_group_id, image_id, owner_id, xkcd_text)
    finally:
        shutil.rmtree("Files")


if __name__ == '__main__':
    main()
