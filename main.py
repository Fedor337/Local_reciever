import json
import os

import requests
import yadisk


YANDEX_TOKEN = os.environ["YANDEX_TOKEN"]


class IpifyIp:
    IPIFY_URL = "https://api.ipify.org/?format=json"

    def __init__(self, timeout: int = 100):
        self.timeout = timeout

    def get_ip(self) -> str:
        response = requests.get(self.IPIFY_URL, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["ip"]


class IpInfoCity:
    IPINFO_GEO_URL = "https://ipinfo.io/{ip}/geo"

    def __init__(self, timeout: int = 100):
        self.timeout = timeout

    def get_city(self, ip: str) -> str:
        url = self.IPINFO_GEO_URL.format(ip=ip)
        response = requests.get(url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()["city"]


class JsonSaver:
    def __init__(self):
        self.data = {}

    def create_json(self, our_ip: str, our_city: str) -> None:
        self.data["ip"] = our_ip
        self.data["city"] = our_city

        with open("info_about_local.json", "w", encoding="utf-8") as file:
            json.dump(self.data, file, ensure_ascii=False)


class YandexDiskJson:
    def __init__(self, client: yadisk.Client):
        self.client = client

    def get_list_files(self, path: str) -> list[str]:
        return [
            item.name
            for item in self.client.listdir(f"disk:{path}")
        ]

    def mkdir(self, dest_dir: str, name_dir: str) -> None:
        try:
            if name_dir not in self.get_list_files(dest_dir):
                self.client.mkdir(f"/{name_dir}")
                self.client.upload(
                    "info_about_local.json",
                    f"disk:/{name_dir}/info_about_local.json",
                )
                print(
                    f"Папка {name_dir} успешно создана "
                    "и json уже внутри!"
                )
        except requests.exceptions.HTTPError as error:
            if error.response.status_code == 409:
                self.client.upload(
                    "info_about_local.json",
                    f"disk:/{name_dir}/info_about_local.json",
                    overwrite=True,
                )

    def upload_json(self) -> None:
        self.client.upload(
            "info_about_local.json",
            "disk:/AIE-8/info_about_local.json",
        )
        print("JSON загружен на диск успешно!")


def main() -> None:
    current_ip = IpifyIp().get_ip()
    current_city = IpInfoCity().get_city(current_ip)

    JsonSaver().create_json(current_ip, current_city)

    with yadisk.Client(token=YANDEX_TOKEN) as client:
        disk = YandexDiskJson(client)
        disk.mkdir("/", "AIE-8")


if __name__ == "__main__":
    main()










