import importlib
from itertools import groupby
from telegram import InputMediaPhoto
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto, InputTextMessageContent, InputMediaPhoto
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import InlineQueryHandler,CallbackQueryHandler, ChosenInlineResultHandler
from pymongo import MongoClient, ReturnDocument
import urllib.request
import random
from datetime import datetime, timedelta
from threading import Lock
import time
from Botttt import dispatcher,updater

from Botttt.modules import ALL_MODULES
client = MongoClient('mongodb+srv://animedatabaseee:BFm9zcCex7a94Vuj@cluster0.zyi6hqg.mongodb.net/?retryWrites=true&w=majority')
db = client['Waifus_lol']
collection = db['anime_characters_lol']

# Get the collection for user totals
user_totals_collection = db['user_totals_lmaoooo']
user_collection = db["user_collection_lmaoooo"]

group_user_totals_collection = db['group_user_totalssssss']


# List of sudo users
sudo_users = ['6404226395', '6185531116', '5298587903', '5798995982', '5150644651', '5813998595', '5813403535', '6393627898', '5952787198', '6614280216','6248411931','5216262234','1608353423']


# Create a dictionary of locks
locks = {}
# Counter for messages in each group
message_counters = {}
spam_counters = {}
# Last sent character in each group
last_characters = {}

# Characters that have been sent in each group
sent_characters = {}

# Keep track of the user who guessed correctly first in each group
first_correct_guesses = {}

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Botttt.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module



def get_next_sequence_number(sequence_name):
    # Get a handle to the sequence collection
    sequence_collection = db.sequences

    # Use find_one_and_update to atomically increment the sequence number
    sequence_document = sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 1}}, 
        return_document=ReturnDocument.AFTER
    )

    # If this sequence doesn't exist yet, create it
    if not sequence_document:
        sequence_collection.insert_one({'_id': sequence_name, 'sequence_value': 0})
        return 0

    return sequence_document['sequence_value']

def upload(update: Update, context: CallbackContext) -> None:
    # Check if user is a sudo user
    if str(update.effective_user.id) not in sudo_users:
        update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        # Extract arguments
        args = context.args
        if len(args) != 4:
            update.message.reply_text('Incorrect format. Please use: /upload img_url Character-Name Anime-Name Rarity')
            return

        # Replace '-' with ' ' in character name and convert to title case
        character_name = args[1].replace('-', ' ').title()
        anime = args[2].replace('-', ' ').title()

        # Check if image URL is valid
        try:
            urllib.request.urlopen(args[0])
        except:
            update.message.reply_text('Invalid image URL.')
            return

        # Check if rarity is valid
        rarity_map = {1: "⚪ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium"}
        try:
            rarity = rarity_map[int(args[3])]
        except KeyError:
            update.message.reply_text('Invalid rarity. Please use 1, 2, 3, or 4.')
            return

        # Generate ID
        id = str(get_next_sequence_number('character_id')).zfill(4)

        # Insert new character
        character = {
            'img_url': args[0],
            'name': character_name,
            'anime': anime,
            'rarity': rarity,
            'id': id
        }
        
        # Send message to channel
        message = context.bot.send_photo(
            chat_id='-1001915956222',
            photo=args[0],
            caption=f'<b>Character Name:</b> {character_name}\n<b>Anime Name:</b> {anime}\n<b>Rarity:</b> {rarity}\n<b>ID:</b> {id}\nAdded by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
            parse_mode='HTML'
        )

        # Save message_id to character
        character['message_id'] = message.message_id
        collection.insert_one(character)

        update.message.reply_text('Successfully uploaded.')
    except Exception as e:
        update.message.reply_text('Unsuccessfully uploaded.')
        
def update(update: Update, context: CallbackContext) -> None:
    # Check if user is a sudo user
    if str(update.effective_user.id) not in sudo_users:
        update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        # Extract arguments
        args = context.args
        if len(args) < 3:
            update.message.reply_text('Incorrect format. Please use: /update ID Field Value')
            return

        # Get the field and value to update
        field = args[1]
        value = ' '.join(args[2:])

        # Check if rarity is being updated
        if field.lower() == 'rarity':
            rarity_map = {1: "⚪ Common", 2: "🟣 Rare", 3: "🟡 Legendary", 4: "🟢 Medium"}
            try:
                value = rarity_map[int(value)]
            except KeyError:
                update.message.reply_text('Invalid rarity. Please use 1, 2, 3, or 4.')
                return

        # Update character with given ID
        result = collection.find_one_and_update({'id': args[0]}, {'$set': {field: value}}, return_document=ReturnDocument.AFTER)

        if result:
            # Update message in channel
            context.bot.edit_message_caption(
                chat_id='-1001915956222',
                message_id=result['message_id'],
                caption=f'<b>Character Name:</b> {result["name"]}\n<b>Anime Name:</b> {result["anime"]}\n<b>Rarity:</b> {result["rarity"]}\n<b>ID:</b> {result["id"]}\nAdded by <a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>',
                parse_mode='HTML'
            )
            update.message.reply_text('Successfully updated.')
        else:
            update.message.reply_text('No character found with given ID.')
    except Exception as e:
        update.message.reply_text('Failed to update character.')

def delete(update: Update, context: CallbackContext) -> None:
    # Check if user is a sudo user
    if str(update.effective_user.id) not in sudo_users:
        update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        # Extract arguments
        args = context.args
        if len(args) != 1:
            update.message.reply_text('Incorrect format. Please use: /delete ID')
            return

        # Delete character with given ID
        character = collection.find_one_and_delete({'id': args[0]})

        if character:
            # Delete message from channel
            context.bot.delete_message(chat_id='-1001915956222', message_id=character['message_id'])
            update.message.reply_text('Successfully deleted.')
        else:
            update.message.reply_text('No character found with given ID.')
    except Exception as e:
        update.message.reply_text('Failed to delete character.')


def anime(update: Update, context: CallbackContext) -> None:
    try:
        # Get all unique anime names
        anime_names = collection.distinct('anime')

        # Send message with anime names
        update.message.reply_text('\n'.join(anime_names))
    except Exception as e:
        update.message.reply_text('Failed to fetch anime names.')


def total(update: Update, context: CallbackContext) -> None:
    try:
        # Extract arguments
        args = context.args
        if len(args) != 1:
            update.message.reply_text('Incorrect format. Please use: /total Anime-Name')
            return

        # Replace '-' with ' ' in anime name
        anime_name = args[0].replace('-', ' ')

        # Get all characters of the given anime
        characters = collection.find({'anime': anime_name})

        # Create a list of character names and IDs
        character_list = [f'Character Name: {character["name"]}\nID: {character["id"]}' for character in characters]

        # Send message with character names and IDs
        update.message.reply_text('\n\n'.join(character_list))
    except Exception as e:
        update.message.reply_text('Failed to fetch characters.')

def change_time(update: Update, context: CallbackContext) -> None:
    # Check if user is a group admin
    user = update.effective_user
    chat = update.effective_chat

    if chat.get_member(user.id).status not in ('administrator', 'creator'):
        update.message.reply_text('You do not have permission to use this command.')
        return

    try:
        # Extract arguments
        args = context.args
        if len(args) != 1:
            update.message.reply_text('Incorrect format. Please use: /changetime NUMBER')
            return

        # Check if the provided number is greater than or equal to 100
        new_frequency = int(args[0])
        if new_frequency < 100:
            update.message.reply_text('The message frequency must be greater than or equal to 100.')
            return

        # Change message frequency for this chat in the database
        chat_frequency = user_totals_collection.find_one_and_update(
            {'chat_id': str(chat.id)},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        update.message.reply_text(f'Successfully changed character appearance frequency to every {new_frequency} messages.')
    except Exception as e:
        update.message.reply_text('Failed to change character appearance frequency.')









def group_leaderboard(update: Update, context: CallbackContext) -> None:
    # Get the chat ID
    chat_id = update.effective_chat.id

    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton('My Group Rank', callback_data='group_leaderboard_myrank')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get group leaderboard data
    leaderboard_data = group_user_totals_collection.find({'group_id': chat_id}).sort('total_count', -1).limit(10)

    # Start of the leaderboard message
    leaderboard_message = "***TOP 10 MOST GUESSED USERS IN THIS GROUP***\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = user.get('first_name', 'Unknown')
        count = user['total_count']
        leaderboard_message += f'➟ {i}. [{first_name}](https://t.me/{username}) - {count}\n'

    # Choose a random photo URL
    photo_urls = [
        "https://graph.org/file/38767e79402baa8b04125.jpg",
        "https://graph.org/file/9bbee80d02c720004ab8d.jpg",
        "https://graph.org/file/cd0d8ca9bcfe489a23f82.jpg",
        "https://graph.org//file/e65e9605f3beb5c76026b.jpg",
        "https://graph.org//file/88c0fc2309930c591d98b.jpg"
    ]
    photo_url = random.choice(photo_urls)

    # Send photo with caption
    update.message.reply_photo(photo=photo_url, caption=leaderboard_message, reply_markup=reply_markup, parse_mode='Markdown')



def group_leaderboard_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    # Get user's total count in this group
    user_total_count = group_user_totals_collection.find_one({'group_id': query.message.chat.id, 'user_id': query.from_user.id})['total_count']

    # Get sorted list of total counts in this group
    sorted_counts = sorted(group_user_totals_collection.find({'group_id': query.message.chat.id}, {'total_count': 1, '_id': 0}), key=lambda x: x['total_count'], reverse=True)

    # Get user's rank in this group
    user_rank = [i for i, x in enumerate(sorted_counts) if x['total_count'] == user_total_count][0] + 1

    query.answer(f'Your rank in this group is {user_rank}.', show_alert=True)



def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0

    if query.isdigit():
        user = user_collection.find_one({'id': int(query)})

        if user:
            # Get the next batch of characters
            characters = user['characters'][offset:offset+50]

            # Check if there are more characters
            if len(characters) > 50:
                # If so, remove the extra character and set the next offset
                characters = characters[:50]
                next_offset = str(offset + 50)
            else:
                # If not, set next_offset to None to indicate no more results
                next_offset = None

            results = []
            added_characters = set()
            for character in characters:
                if character['name'] not in added_characters:
                    anime_characters_guessed = sum(c['anime'] == character['anime'] for c in user['characters'])
                    total_anime_characters = collection.count_documents({'anime': character['anime']})

                    results.append(
                        InlineQueryResultPhoto(
                            id=character['id'],
                            photo_url=character['img_url'],
                            thumb_url=character['img_url'],
                            caption=f"🌻 <b><a href='tg://user?id={user['id']}'>{user.get('username', user['id'])}</a></b>'s Character\n\n<b>Name:</b> {character['name']} " + (f"(x{character.get('count', 1)})" if character.get('count', 1) > 1 else "") + f"\n<b>Anime:</b> {character['anime']} ({anime_characters_guessed}/{total_anime_characters})\n\n🆔: {character['id']}",
                            parse_mode='HTML'
                        )
                    )
                    added_characters.add(character['name'])

            update.inline_query.answer(results, next_offset=next_offset)
        else:
            update.inline_query.answer([InlineQueryResultArticle(
                id='notfound', 
                title="User not found", 
                input_message_content=InputTextMessageContent("User not found")
            )])
    else:
        all_characters = list(collection.find({}).skip(offset).limit(51))
        if len(all_characters) > 50:
            all_characters = all_characters[:50]
            next_offset = str(offset + 50)
        else:
            next_offset = None

        results = []
        for character in all_characters:
            users_with_character = list(user_collection.find({'characters.id': character['id']}))
            total_guesses = sum(character.get("count", 1) for user in users_with_character)

            results.append(
                InlineQueryResultPhoto(
                    id=character['id'],
                    photo_url=character['img_url'],
                    thumb_url=character['img_url'],
                    caption=f"<b>Look at this character!</b>\n\n⟹ <b>{character['name']}</b>\n⟹ <b>{character['anime']}</b>\n🆔: {character['id']}\n\n<b>Guessed {total_guesses} times In Globally</b>",
                    parse_mode='HTML'
                )
            )
        update.inline_query.answer(results, next_offset=next_offset)



def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Check if an ID was provided
    if not context.args:
        update.message.reply_text('Please provide a character ID.')
        return

    character_id = context.args[0]

    # Get the user document
    user = user_collection.find_one({'id': user_id})
    if not user:
        update.message.reply_text('You have not guessed any characters yet.')
        return

    # Check if the character is in the user's collection
    character = next((c for c in user['characters'] if c['id'] == character_id), None)
    if not character:
        update.message.reply_text('This character is not in your collection.')
        return

    # Replace the old favorite with the new one
    user['favorites'] = [character_id]

    # Update user document
    user_collection.update_one({'id': user_id}, {'$set': {'favorites': user['favorites']}})

    update.message.reply_text(f'Character {character["name"]} has been added to your favorites.')
    

def leaderboard(update: Update, context: CallbackContext) -> None:
    # Create inline keyboard
    keyboard = [
        [InlineKeyboardButton('My Rank', callback_data='leaderboard_myrank')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Get global leaderboard data
    leaderboard_data = user_collection.find().sort('total_count', -1).limit(10)

    # Start of the leaderboard message
    leaderboard_message = "***TOP 10 MOST GUESSED USERS***\n\n"

    for i, user in enumerate(leaderboard_data, start=1):
        username = user.get('username', 'Unknown')
        first_name = user.get('first_name', 'Unknown')
        count = user['total_count']
        # Mention the user with a hyperlink to their Telegram profile
        leaderboard_message += f'➟ {i}. [{first_name}](https://t.me/{username}) - {count}\n'

    # Choose a random photo URL
    photo_urls = [
        "https://graph.org/file/38767e79402baa8b04125.jpg",
        "https://graph.org/file/9bbee80d02c720004ab8d.jpg",
        "https://graph.org/file/cd0d8ca9bcfe489a23f82.jpg",
        "https://graph.org//file/e65e9605f3beb5c76026b.jpg",
        "https://graph.org//file/88c0fc2309930c591d98b.jpg"
    ]
    photo_url = random.choice(photo_urls)

    # Send photo with caption
    update.message.reply_photo(photo=photo_url, caption=leaderboard_message, reply_markup=reply_markup, parse_mode='Markdown')


def leaderboard_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query

    # Get user's total count
    user_total_count = user_collection.find_one({'id': query.from_user.id})['total_count']

    # Get sorted list of total counts
    sorted_counts = sorted(user_collection.find({}, {'total_count': 1, '_id': 0}), key=lambda x: x['total_count'], reverse=True)

    # Get user's rank
    user_rank = [i for i, x in enumerate(sorted_counts) if x['total_count'] == user_total_count][0] + 1

    query.answer(f'Your rank is {user_rank}.', show_alert=True)




def harem(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    # Get the user's collection
    user = user_collection.find_one({'id': user_id})
    if not user:
        update.message.reply_text('You have not guessed any characters yet.')
        return

    # Get the list of characters and sort by anime name
    characters = sorted(user['characters'], key=lambda x: x['anime'])

    # Group the characters by anime
    grouped_characters = {k: list(v) for k, v in groupby(characters, key=lambda x: x['anime'])}

    # Start of the harem message
    harem_message = f"<a href='tg://user?id={user_id}'>{update.effective_user.first_name}</a>'s Collection\n\n"

    # Iterate over the grouped characters
    for anime, characters in grouped_characters.items():
        # Get the total number of characters from this anime
        total_characters = collection.count_documents({'anime': anime})

        # Add the anime name and the number of collected characters to the message
        harem_message += f'{anime} - {len(characters)} / {total_characters}\n'

        # Sort the characters by ID and take only the first five
        characters = sorted(characters, key=lambda x: x['id'])[:5]

        # Add the character details to the message
        for character in characters:
            count = character.get('count')
            if count is not None:
                harem_message += f'ID: {character["id"]} - {character["name"]} × {count}\n'
            else:
                harem_message += f'ID: {character["id"]} - {character["name"]}\n'

        harem_message += '\n'
        total_count = len(user['characters'])
    # Create an InlineKeyboardButton named 'All Characters'
    keyboard = [[InlineKeyboardButton(f"See All Characters ({total_count})", switch_inline_query_current_chat=str(user_id))]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # If a favorite character is set, send its image with harem message as caption
    if 'favorites' in user and user['favorites']:
        fav_character_id = user['favorites'][0]
        fav_character = next((c for c in user['characters'] if c['id'] == fav_character_id), None)
        
        if fav_character and 'img_url' in fav_character:
            update.message.reply_photo(photo=fav_character['img_url'], parse_mode='HTML', caption=harem_message, reply_markup=reply_markup)
        else:
            update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)
    else:
        update.message.reply_text(harem_message, parse_mode='HTML', reply_markup=reply_markup)



def main() -> None:
    
    
    dispatcher.add_handler(CommandHandler('upload', upload, run_async=True))
    dispatcher.add_handler(CommandHandler('update', update, run_async=True))
    
    dispatcher.add_handler(CommandHandler('delete', delete, run_async=True))
    
    dispatcher.add_handler(CommandHandler('animee', anime, run_async=True))
    dispatcher.add_handler(CommandHandler('total', total, run_async=True))
    dispatcher.add_handler(CommandHandler('changetime', change_time, run_async=True))

     
    dispatcher.add_handler(InlineQueryHandler(inlinequery, run_async=True))
    dispatcher.add_handler(CommandHandler('fav', fav, run_async=True))
    dispatcher.add_handler(CommandHandler('globaltop', leaderboard))
    dispatcher.add_handler(CallbackQueryHandler(leaderboard_button, pattern='^leaderboard_'))
    dispatcher.add_handler(CommandHandler('grouptop', group_leaderboard))
    dispatcher.add_handler(CallbackQueryHandler(group_leaderboard_button, pattern='^group_leaderboard_myrank$'))
    dispatcher.add_handler(CommandHandler('collection', harem, run_async=True))
    #  command handlers to the dispatcher
    
    updater.start_polling(
            timeout=15,
            read_latency=4,
            drop_pending_updates=True,
            
    )
    
    updater.idle()
    
if __name__ == '__main__':
    
    main()
    
