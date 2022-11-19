# importing packages
from distutils.cmd import Command
import json, discord
from discord.ext import commands, tasks
from discord.utils import get
import ast, aiohttp


class RustHackReport(commands.Cog):
    def __init__(self, client):
        print("[Cog] RustHackReport initiated")
        self.client = client
    
    with open("./json/config.json", "r") as f:
        config = json.load(f)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Getting rules")
        rules = await self.get_rules()
        print("Deleting rules")
        await self.delete_all_rules(rules)
        print("Setting rules")
        await self.set_rules()
        print("Starting twitter stream")
        await self.twitter_stream()
    
    async def get_rules(self):
        bearer_token = self.config['twitter_token']
        auth = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "v2FilteredStreamPython"
        }
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        async with aiohttp.ClientSession(headers=auth) as session:
                async with session.get(url=url) as r:
                    response = await r.json()
        return response
    
    async def delete_all_rules(self, rules):
        if rules is None or "data" not in rules:
            return None

        ids = list(map(lambda rule: rule["id"], rules["data"]))
        payload = {"delete": {"ids": ids}}
        bearer_token = self.config['twitter_token']
        auth = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "v2FilteredStreamPython"
        }
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        async with aiohttp.ClientSession(headers=auth) as session:
                async with session.get(url=url, json=payload) as r:
                    response = await r.json()
        return response


    async def set_rules(self):
        # You can adjust the rules if needed
        sample_rules = [
            {"value": "from:rusthackreport"},
        ]
        payload = {"add": sample_rules}
        bearer_token = self.config['twitter_token']
        auth = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "v2FilteredStreamPython"
        }
        url = "https://api.twitter.com/2/tweets/search/stream/rules"
        async with aiohttp.ClientSession(headers=auth) as session:
                async with session.get(url=url, json=payload) as r:
                    response = await r.json()
        return response
    async def twitter_stream(self):
        bearer_token = self.config['twitter_token']
        auth = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "v2FilteredStreamPython"
        }
        url = 'https://api.twitter.com/2/tweets/search/stream'
        session_timeout =  aiohttp.ClientTimeout(total=None,sock_connect=None,sock_read=None)
        async with aiohttp.ClientSession(raise_for_status=True, headers=auth, timeout=session_timeout) as session:
            async with session.get(url) as r:
                async for line in r.content:
                    c = line.decode("utf-8")
                    c = c[:-2]
                    if c:
                        mydict = ast.literal_eval(c)
                        tweetid = mydict['data']['id']
                        tweettext = mydict['data']['text']
                        url = await self.create_url(tweetid)
                        tweetdeets = await self.connect_to_endpoint(url)
                        steamurl = tweetdeets['data'][0]['entities']['urls'][0]['expanded_url']
                        color = '0x992d22'
                        tweeturl = f"https://twitter.com/rusthackreport/status/{tweetid}"
                        embed = discord.Embed(title=f"Rust Hack Report", color=int(color, base=16))
                        embed.add_field(name="Tweet",value=f"```{tweettext}```", inline=False)
                        embed.add_field(name="Links",value=f"[Steam]({steamurl}) | [Tweet]({tweeturl})")
                        embed.set_footer(text="Tweet brought to you by Gnomeslayer#5551")
                        channel = self.client.get_channel(self.config['report_channel'])
                        await channel.send(embed=embed)
        
    async def create_url(self, tweetid):
        tweet_fields = "tweet.fields=attachments,author_id,context_annotations,conversation_id,created_at,entities"
        media_fields = "media.fields=url"
        ids = f"ids={tweetid}"
        url = "https://api.twitter.com/2/tweets?{}&{}&{}".format(ids, tweet_fields, media_fields)
        return url
    
    async def connect_to_endpoint(self,url):
        bearer_token = self.config['twitter_token']
        auth = {
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "v2FilteredStreamPython"
        }
        async with aiohttp.ClientSession(headers=auth) as session:
            async with session.get(url=url) as r:
                response = await r.json()
        data = response
        return data
        
async def setup(client):
    await client.add_cog(RustHackReport(client))
