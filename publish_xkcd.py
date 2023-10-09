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
    xkcd_image = requests.get(xkcd_image_url)
    xkcd_image.raise_for_status()
    return xkcd_image, xkcd_text


def get_url_for_upload(vk_api_access_token, vk_api_version):
    api_url_upload = urljoin(BASE_URL_VKAPI, 'photos.getWallUploadServer')
    params = {
        'access_token': vk_api_access_token,
        'v': vk_api_version
    }
    response_upload = requests.get(api_url_upload, params=params)
    response_upload.raise_for_status()
    url_for_download = response_upload.json()['response']['upload_url']
    return url_for_download


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
    save_inf = save_response.json()
    image_id = save_inf['response'][0]['id']
    owner_id = save_inf['response'][0]['owner_id']
    return image_id, owner_id


def upload_photo(vk_api_access_token, vk_api_version, url_for_download, group_id, xkcd_num):
    with open(f'Files/image{xkcd_num}.jpg', 'rb') as file:
        upload_files = {
            'photo': file
        }
        params_for_upload = {
            'access_token': vk_api_access_token,
            'v': vk_api_version,
            'group_id': group_id
        }
        upload_response = requests.post(url_for_download, params=params_for_upload, files=upload_files)
    upload_response.raise_for_status()
    params_for_save = upload_response.json()
    server = params_for_save['server']
    photo = params_for_save['photo']
    hash_for_save = params_for_save['hash']
    return server, photo, hash_for_save


def post_photo(vk_api_access_token, vk_api_version, group_id, image_id, owner_id, xkcd_num):
    url_for_post = urljoin(BASE_URL_VKAPI, 'wall.post')
    with open(f'Files/message{xkcd_num}.txt', 'r') as file:
        xkcd_text = file.read()
    params = {
        'access_token': vk_api_access_token,
        'v': vk_api_version,
        'owner_id': f'-{group_id}',
        'from_group': 1,
        'attachments': f'photo{owner_id}_{image_id}',
        'message': xkcd_text
    }
    post_response = requests.post(url_for_post, params=params)
    post_response.raise_for_status()


def main():
    load_dotenv()
    vk_group_id = os.environ['VK_GROUP_ID']
    vk_api_access_token = os.environ['VK_API_ACCESS_TOKEN']
    vk_api_version = '5.150'
    xkcd_amount = get_amount_xckd()
    xkcd_num = random.randint(1, xkcd_amount)
    xkcd_image, xkcd_text = download_new_xkcd(xkcd_num)
    os.makedirs('Files', exist_ok=True)
    with open(f'Files/image{xkcd_num}.jpg', 'ab') as file:
        file.write(xkcd_image.content)
    with open(f'Files/message{xkcd_num}.txt', 'a') as file:
        file.write(xkcd_text)
    upload_url = get_url_for_upload(vk_api_access_token, vk_api_version)
    server, photo, hash_for_save = upload_photo(vk_api_access_token, vk_api_version, upload_url, vk_group_id, xkcd_num)
    image_id, owner_id = save_image(vk_api_access_token, vk_api_version, server, photo, hash_for_save)
    post_photo(vk_api_access_token, vk_api_version, vk_group_id, image_id, owner_id, xkcd_num)
    shutil.rmtree("Files")



if __name__ == '__main__':
    main()
