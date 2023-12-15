"""
Attempt to make Telegram scraping via class
"""
import os

from dotenv import load_dotenv
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest


load_dotenv()


class TelegramScraper:
    """
    Telegram scraper class
    """

    def __init__(self):
        self.client = TelegramClient(
            "scraper", os.getenv("API_ID"), os.getenv("API_HASH")
        )
        self.client.start()

    async def connect(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(os.getenv("PHONE"))
            await self.client.sign_in(os.getenv("PHONE"), input("Enter the code: "))

    async def scrape_chanel(self, chanel_name):
        all_messages = []
        offset_id = 0
        limit = 100
        total_messages = 0
        total_count_limit = 0
        while True:
            history = await self.client(
                GetHistoryRequest(
                    peer=chanel_name,
                    offset_id=offset_id,
                    offset_date=None,
                    add_offset=0,
                    limit=limit,
                    max_id=0,
                    min_id=0,
                    hash=0,
                )
            )
            if not history.messages:
                break
            messages = history.messages
            for message in messages:
                all_messages.append(message.to_dict())
                print(all_messages)

            offset_id = messages[len(messages) - 1].id
            if total_count_limit != 0 and total_messages >= total_count_limit:
                break
        return await all_messages


if __name__ == "__main__":
    scraper = TelegramScraper()
    scraper.connect()
    messages = scraper.scrape_chanel("The Bell")
    print(messages)
    scraper.client.log_out()
