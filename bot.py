from datetime import datetime
import time
import threading
import discord
from discord.ext import commands, tasks
import csv
import psycopg2
import os
import pytz
import asyncio
import redis

DATABASE_URL = os.environ['DATABASE_URL']

config = open('./TOKEN.md')
TOKEN = config.read()
offdays = [2,5]
bot=commands.Bot(command_prefix='cat, ')
target_channel_id = 
pst = pytz.timezone('America/Los_Angeles')

r = redis.from_url(os.environ.get("REDIS_URL"))




activities = {
# '10:00' : 'work',
  '13:00' : 'exercise',
  '14:00' : 'programming',
  '20:00' : 'meditation',
  '21:00' : 'creative',
  '00:00' : 'save',
}

def rget(key):
  return r.get(key).decode("utf-8")


def add_record(record):
  conn = psycopg2.connect(DATABASE_URL, sslmode='require')
  cursor = conn.cursor()
  cursor.execute("INSERT INTO logs (date, activity, duration, comment) VALUES (%s, %s, %s, %s)", record)
  conn.commit()
  conn.close()

def is_done(activity):
  conn = psycopg2.connect(DATABASE_URL, sslmode='require')
  cursor = conn.cursor()
  date = datetime.now(pst).date()
  cursor.execute("SELECT * FROM logs WHERE date=%(date)s AND activity = %(activity)s", {"activity": activity, "date":date})
  result = cursor.fetchall()
  conn.close()
  return bool(result)

def add_activity(activity, t):
  conn = psycopg2.connect(DATABASE_URL, sslmode='require')
  cursor = conn.cursor()
  cursor.execute("INSERT INTO activities (activity, time, duration) VALUES (%s, %s, %s)", [activity, time, duration])
  conn.commit()
  conn.close()

def get_records():
  conn = psycopg2.connect(DATABASE_URL, sslmode='require')
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM logs WHERE date=current_date-1")
  time_spent_data=cursor.fetchall()
  conn.close()
  return time_spent_data

def get_schedule():
  return r.hgetall("schedule")


def get_tasks(activity):
  tasks = r.hgetall("activity")
  if tasks:
    return tasks
  return False
    

@bot.command()
async def start(ctx, *args):
  current_activity = r.get("current")
  activity_start = r.get("start")
  channel = bot.get_channel(target_channel_id)
  
  if current_activity:
    await channel.send('<@2> \n' + "今は" + current_activity.decode("utf-8") + 'じゃないか？' )
    return

  await channel.send('呼吸して?')
  msg = await bot.wait_for('message', check=lambda message: message.author == ctx.message.author)
  if(msg.content == "y" or msg.content == "Y"):
    await channel.send("<@25\n" + "集中しろ" )
    await asyncio.sleep(5 * 60)

  r.set("current", args[0])
  activity_start = datetime.now()
  current_time = datetime.now(pst)
  current_time = current_time.strftime("%H:%M")
  r.set("start", str(activity_start))
  await channel.send('<@25220 \n' + current_time + 'に' + args[0] + 'を始める。' )

@bot.command()
async def done(ctx, *args):
  channel = bot.get_channel(target_channel_id)
  current_activity = r.get("current")


  
  if current_activity:
    end = datetime.now()
    if(len(args) > 0):
      duration = int(args[0])
    else:
      activity_start = r.get("start").decode("utf-8")
      activity_start = datetime.strptime(activity_start, '%Y-%m-%d %H:%M:%S.%f')

      duration = end - activity_start
      duration = duration.seconds/60

    now = datetime.now(pst)
    await channel.send("報告。")
    msg = await bot.wait_for('message', check=lambda message: message.author == ctx.message.author)
    comment = msg.content
    add_record([now.strftime("%D"), current_activity.decode("utf-8"), duration, comment])
    await channel.send("今は" + current_activity.decode("utf-8") + "に" + str(round(duration)) + "分を費やした, お疲れ様でした。")
    r.set("current", "")
    return
  await channel.send("活動なし。")




@bot.command()
async def setting(ctx, *args):
  await ctx.channel.send("次回をどうする？")
  msg = await bot.wait_for('message', check=lambda message: message.author == ctx.message.author)
  r.set(args[0], msg.content)
  await ctx.channel.send("はい")


@bot.command()
async def repeat(ctx, *args):
	response = ""

	for arg in args:
		response = response + " " + arg

	await ctx.channel.send(response)


@bot.command()
async def ZA(ctx, *args):
  if (args[0] != "WAARUDO"):
    return

  channel = bot.get_channel(target_channel_id)
  r.set("timestop", "true")
  await channel.send(str('時よ止まれ！'))

@bot.command()
async def resume(ctx, *args):
  channel = bot.get_channel(target_channel_id)
  r.set("timestop", "false")
  await channel.send(str('そして時は動き出す。'))



def get_tasks(activity):
  tasks = r.smembers(activity)
  if tasks:
    return tasks
  return False

async def embed_tasks(activity):
  channel = bot.get_channel(target_channel_id)
  embed=discord.Embed(title="Tasks for " + activity, color=0x7A2F8F)
  tasks = r.smembers(activity)
  i = 0
  for item in tasks:
    embed.add_field(name=i, value=item.decode("utf-8"))
    i = i + 1
  await channel.send(embed=embed)

# Core bot, runs actions at set times of day

@tasks.loop(seconds = 60)
async def scheduled():
  now = datetime.now(pst)
  current_time = now.strftime("%H:%M")
  channel = bot.get_channel(target_channel_id)
  current_activity = r.get("current")


  if (current_time == "00:00"):
    embed=discord.Embed(title="今の日々", description="Time spent in minutes", color=0x7A2F8F)
    time_spent_data = get_records()
    for item in time_spent_data:
      embed.add_field(name=item[1], value=round(item[2]))
    await channel.send(embed=embed)
    return
  if(True):
    return


  if (datetime.today().weekday() in offdays):
    return

  if current_time in activities:
    if (current_activity and current_activity == activities[current_time]):
      return

    if (is_done(activities[current_time])):
      return

    if (current_activity):
      await channel.send(" \n" + current_activity.decode("utf-8") + "を続ける？")
      return

    await channel.send("<@25\n" + activities[current_time] + "の時間。" )
    # try:
    #     msg = await bot.wait_for('message', check=lambda message: message.content == "Ja", timeout=11 * 60)
    # except:
    #     await channel.send('今日を休むか？')
    #     current_activity = ""
    #     return

    # activity_start = datetime.now(pst)
    # current_time = activity_start.strftime("%H:%M")
    # await channel.send('<@252202099494879243> \n' + current_time.format(msg) + 'に' + current_activity + 'を始める。' )
    # await asyncio.sleep(21 * 60)
    # await channel.send("<@252202099494879243> \n" + "終わり、か？")

    
@scheduled.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

scheduled.start()
bot.run(TOKEN)
