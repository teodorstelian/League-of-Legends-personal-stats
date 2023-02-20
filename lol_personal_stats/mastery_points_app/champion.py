import requests


class Champion:

    def retrieve_id_and_name(self):
        """
            Method where we retrieve the id and names of all the champions
        :return: A dictionary containing the champion id and name
        """
        champion_url = "http://ddragon.leagueoflegends.com/cdn/13.1.1/data/en_US/champion.json"
        champion_response = requests.get(champion_url)
        champion_data = champion_response.json()
        return {champion["key"]: champion["name"] for champion in champion_data["data"].values()}
