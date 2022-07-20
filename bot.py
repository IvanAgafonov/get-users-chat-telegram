# importing all required libraries
import datetime
import random

from boto.s3.connection import S3Connection
import os
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest, GetChannelsRequest
from telethon.tl.types import InputPeerUser, InputPeerChannel, ChannelParticipantsSearch, UserStatusOffline, \
    ChannelParticipantsBots, ChannelParticipantsContacts, ChannelParticipantsBanned, ChannelParticipantsRecent, \
    ChannelParticipantsAdmins, ChannelParticipantsKicked, PeerChat
from telethon import TelegramClient, sync, events
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest, GetFullChatRequest
import asyncio
from telethon import functions, types
import time

# get your api_id, api_hash, token
# from telegram as described above
api_id = os.environ['api_id']
api_hash = os.environ['api_hash']

# your phone number
phone = os.environ['phone']

# creating a telegram session and assigning
# it to a variable client
client = TelegramClient('session', api_id, api_hash)
count = 0
lock = False

# connecting and building the session
client.connect()

# in case of script ran first time it will
# ask either to input token or otp sent to
# number or sent or your telegram id 
if not client.is_user_authorized():
    client.send_code_request(phone)

    # signing in the client
    client.sign_in(phone, input('Enter the code: '))


async def get_dialog_by_name(name):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if hasattr(dialog, "entity"):
            if hasattr(dialog.entity, "title"):
                if dialog.entity.title == name:
                    return dialog
    return None


# username | first_name + last_name | status
async def get_members(dialog):
    offset = 0
    limit = 200
    all_participants = []

    if not dialog.is_channel:
        participants = await client.get_participants(dialog, aggressive=True)
        all_participants = participants
    else:
        while True:
            participants = await client(GetParticipantsRequest(
                dialog, ChannelParticipantsSearch(''), offset, limit, hash=0
            ))
            if not participants.users:
                break
            all_participants.extend(participants.users)
            offset += len(participants.users)
    user_names = []
    fio_names = []
    status_names = []
    all_participants.sort(key=lambda x: x.status.was_online.strftime("%d.%m.%Y %H:%M:%S") if
    isinstance(x.status, UserStatusOffline) else type(x.status).__name__)
    for participant in all_participants:
        user_names.append(participant.username)
        fio_names.append(
            participant.first_name + " " + (participant.last_name if participant.last_name is not None else ""))
        status_names.append(participant.status)
    message = "№;Date last seen;Username;NickName\n"
    for i in range(len(user_names)):
        message += str(i + 1) + ";"
        if isinstance(status_names[i], UserStatusOffline):
            message += status_names[i].was_online.strftime("%d.%m.%Y %H:%M:%S") + ";"
        else:
            message += type(status_names[i]).__name__ + ";"
        if user_names[i] is None:
            message += "None;"
        else:
            message += "@" + user_names[i] + ";"
        message += fio_names[i] + "\n"

    return message


async def get_dialog_by_id(id):
    dialogs = await client.get_dialogs()
    for dialog in dialogs:
        if hasattr(dialog, "entity"):
            if hasattr(dialog.entity, "id"):
                if dialog.entity.id == id:
                    return dialog
    return None


@client.on(events.NewMessage(pattern='выгрузка'))
async def handler(event):
    global lock

    if event.is_private:
        if lock == False:
            lock = True
            try:
                message = event.message.message
                sender = await event.get_input_sender()
                await event.reply("Обработка...")
                if sender.user_id in (311302034, 375707303):
                    await getCsv()
                    await client.send_file(sender, "users.csv")
                    deleteCsv()
            except Exception as err:
                print(err)
            finally:
                lock = False


async def getCsv():
    chat_name = os.environ['group_name']
    chat = await get_dialog_by_name(chat_name)
    res = await get_members(chat)
    file = open('users.csv', 'wb')
    file.write(res.encode('cp1251', 'ignore'))
    file.close()


def deleteCsv():
    os.remove('users.csv')


client.run_until_disconnected()
