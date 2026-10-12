import json
#import os

import requests
#import yadisk


YANDEX_TOKEN = "YOUR_YANDEX_TOKEN"


class IpifyIp:
    """Клиент для получения внешнего IP-адреса через api.ipify.org.

    Attributes:
        timeout: Таймаут HTTP-запроса в секундах.
    """
    IPIFY_URL = "https://api.ipify.org/?format=json"

    def __init__(self, timeout: int = 100):
        """Инициализировать клиент.
        
        Args:
            timeout: Таймаут HTTP-запроса в секундах. По умолчанию 100.
        """
        self.timeout = timeout

    def get_ip(self) -> str:
        '''Вернуть текущий внешний IP-адрес
        
        Возвращает:
            Строка с IPv4-адресом, например ``"8.8.8.8"``.
        '''
        response = requests.get(self.IPIFY_URL, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["ip"]


class IpInfoCity:
    """Клиент для получения города по IP-адресу через ipinfo.io. """
    IPINFO_GEO_URL = "https://ipinfo.io/{ip}/geo"

    def __init__(self, timeout: int = 100):
        """Инициализировать клиент.
                
        Args:
             timeout: Таймаут HTTP-запроса в секундах. По умолчанию 100.
        """
        self.timeout = timeout

    def get_city(self, ip: str) -> str:
        """Получить город по внешнему IP-адресу.
                        
        Args:
            ip: Внешний IP-адрес.
        Возвращает:
            Строка с названием города.
        """
        url = self.IPINFO_GEO_URL.format(ip=ip)
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["city"]


class JsonSaver:
    """Класс, который создает json-файл содержащий внешний IP-адрес и название города."""
    def __init__(self):
        """Иннициализировать класс и создать словарь."""
        self.data = {}

    def create_json(self, our_ip: str, our_city: str) -> None:
        """Создать json-файл.
        
        Args:
            our_ip: Внешний IP-адрес.
            our_city: Название города.
        """
        self.data["ip"] = our_ip
        self.data["city"] = our_city

        with open("info_about_local.json", "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False)


class YandexDiskJson:
    """Клиент, который создает по указанным путям папку на яндекс диске и json-файл 
    с внешним IP-адресом и названием города.
    """

    API = "https://cloud-api.yandex.net/v1/disk/resources"
    headers = {
                "Authorization": f"OAuth {YANDEX_TOKEN}"
            }

    def __init__(self):
        pass
        """Иннициализировать клиент"""

    def get_list_files(self, path: str) -> list[str]:
        """Получить список файлов по желаемому пути.
        
        Args:
            path: дирректория, которую мы хотим просмотреть.
        """
        params = {"path": path}

        response = requests.get(self.API, headers=self.headers, params=params)

        if response.status_code != 200:
            print(f"Ошибка: {response.json().get('message')}")
            return []

        return response.json()["_embedded"]["items"]

    def mkdir(self, dest_dir: str, name_dir: str) -> None:
        """Создать папку по желаемому пути, пересоздав её при необходимости.
        
        Args:
            dest_dir: путь, где мы хотим создать новую папку.
            name_dir: имя папки, которую хотим создать.
        """
        full_path = f"{dest_dir.rstrip('/')}/{name_dir}"

        delete_params = {"path": full_path, "permanent": "true"}
        delete_dir = requests.delete(
            self.API,
            headers=self.headers,
            params=delete_params
        )
        if delete_dir.status_code in (202, 204, 404):
            pass
        else:
            raise RuntimeError(
                f"Не удалось удалить '{full_path}': "
                f"{delete_dir.status_code} {delete_dir.text}"
            )

        create_params = {"path": full_path}
        create_dir = requests.put(self.API, headers=self.headers, params=create_params)

        if create_dir.status_code == 201:
            return
        raise RuntimeError(
            f"Не удалось создать папку '{full_path}': "
            f"{create_dir.status_code} {create_dir.text}"
        )

    def upload_json(self, dest_json: str, name_json: str) -> None:
        """Загрузить json-файл на Яндекс.Диск.
        
        Args:
            dest_json: путь к папке на Диске, куда кладём файл.
            name_json: имя json-файла (он же — локальный файл).
        """
        full_path = f"{dest_json.rstrip('/')}/{name_json.lstrip('/')}"

        upload_params = {"path": full_path, "overwrite": "true"}
        upload_json = requests.get(
            f"{self.API}/upload",
            headers=self.headers,
            params=upload_params
        )
        if upload_json.status_code != 200:
            raise RuntimeError(
                f"Не удалось получить ссылку для загрузки '{full_path}': "
                f"{upload_json.status_code} {upload_json.text}"
            )

        href = upload_json.json()["href"]

        with open(name_json.lstrip("/"), "rb") as file:
            put_json = requests.put(href, files={"file": file})

        if put_json.status_code not in (200, 201):
            raise RuntimeError(
                f"Не удалось загрузить '{full_path}': "
                f"{put_json.status_code} {put_json.text}"
            )


def main() -> None:
    current_ip = IpifyIp().get_ip()
    current_city = IpInfoCity().get_city(current_ip)
    JsonSaver().create_json(current_ip, current_city)

    yandex_disk = YandexDiskJson()
    yandex_disk.mkdir("/", "AIE-8")
    yandex_disk.upload_json("/AIE-8", "info_about_local.json")


if __name__ == "__main__":
    main()
