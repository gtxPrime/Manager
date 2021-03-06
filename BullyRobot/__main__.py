import importlib
import time
import re
from sys import argv
from typing import Optional

from BullyRobot import (
    ALLOW_EXCL,
    OWNER_USERNAME,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    START_IMG,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from BullyRobot.modules import ALL_MODULES
import BullyRobot.modules.sql.users_sql as sql
from BullyRobot.modules.helper_funcs.chat_status import is_user_admin
from BullyRobot.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


PM_START_TEXT = """
*สแดส,\nเน I am ๐๐น๐ฎ๐ฐ๐ธ ๐ฆ๐ผ๐๐ฒ๐ฟ๐ฒ๐ถ๐ด๐ป* [!](https://telegra.ph/file/d41b53919d63247bd2b0d.png)\n*เน I am one of the most powerful bots on Telegram*\nโโโโโโโโโโโโโโโโโโโโโโโโ\nโป แดsแดสs ยป {}\nโป  แดสแดแดs ยป {}\nโโโโโโโโโโโโโโโโโโโโโโโโ\n*เน แดสษชแดแด แดษด แดสแด สแดสแดฉ สแดแดแดแดษด สแดสแดแดก แดแด ษขแดแด ษชษดาแดสแดแดแดษชแดษด แดสแดแดแด แดส แดแดแดแดแดษดแดs.\n*โ
"""

buttons = [
    [
        InlineKeyboardButton(
            text="โ แดแดแด แดแด ษชษด สแดแดส ษขสแดแดแด โ", url="https://t.me/BlackSovereignRoBot?startgroup=true"),
    ],
    [
        InlineKeyboardButton(
            text="โป สแดสแด โป", callback_data="help_back"),
    ],
    [
        InlineKeyboardButton(
            text="โน๏ธ แดสแดแดแด แดแด โน๏ธ", callback_data="fallen_"),
        InlineKeyboardButton(
            text="โน๏ธ sแดแดสแดแด แดแดแดแด โน๏ธ", callback_data="source_"),
    ],
    [
        InlineKeyboardButton(
            text="โน๏ธ sแดแดแดแดสแด โน๏ธ", url=f"https://t.me/{SUPPORT_CHAT}"
        ),
        InlineKeyboardButton(
            text="๐ต๐ป แดแดแด?แดสแดแดแดส ๐ต๐ป", url=f"https://t.me/{OWNER_USERNAME}"
        ),
    ],
]

BullyRobot_IMG = "https://telegra.ph/file/d41b53919d63247bd2b0d.png"

HELP_STRINGS = f"""
๐๐น๐ฎ๐ฐ๐ธ ๐ฆ๐ผ๐๐ฒ๐ฟ๐ฒ๐ถ๐ด๐ป *แดxแดสแดsษชแด?แด ๊ฐแดแดแดแดสแดs*\n*ยป แดสแดแดแดแดแดแด แดสส แดสแด แดแดแดแดแดษดแดs*\n*ยป แดสส แด๊ฐ แดส แดแดแดแดแดษดแดs แดแดษด สแด แดsแดแด แดกษชแดส / แดส !*\n*ยป ษช๊ฐ สแดแด ษขแดแด แดษดส ษชssแดแด แดส สแดษข ษชษด แดษดส แดแดแดแดแดษดแด แดสแดแดsแด สแดแดแดสแด ษชแด แดแด @{SUPPORT_CHAT}*\n\n*ใคใคใคใคใคใคยป แดแดษชษด แดแดแดแดแดษดแด๊ฑ ยซ*\n\nโฒ /start : *๊ฑแดแดสแด๊ฑ แดแด | แดแดแดแดสแดษชษดษข แดแด แดแด สแดแด'แด?แด แดสสแดแดแดส แดแดษดแด ษชแดโ.*\nโฒ /donate : *sแดแดแดแดสแด แดแด สส แดแดษดแดแดษชษดษข ๊ฐแดส แดส สแดสแดแดกแดสแดโ.*\nโฒ /help  : *แดแด?แดษชสแดสสแด แดแดแดแดแดษดแด๊ฑ ๊ฑแดแดแดษชแดษด.*\n*  โฃ ษชษด แดแด : แดกษชสส ๊ฑแดษดแด สแดแด สแดสแดโ ๊ฐแดส แดสส ๊ฑแดแดแดแดสแดแดแด แดแดแดแดสแด๊ฑ.*\n*  โฃ ษชษด ษขสแดแดแด : แดกษชสส สแดแดษชสแดแดแด สแดแด แดแด แดแด, แดกษชแดส แดสส แดสแดแด สแดสแดโ แดแดแดแดสแด๊ฑ.*"""

DONATE_STRING = """[๐๐จ๐ก๐ง ๐๐ข๐๐ค](https://t.me/gtxPrime)"""

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
    imported_module = importlib.import_module("BullyRobot.modules." + module_name)
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


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


@run_async
def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


@run_async
def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="โ", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            update.effective_message.reply_text(
                PM_START_TEXT.format(sql.num_users(), sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_photo(
            START_IMG, caption="ษช แดแด แดสษชแด?แด สแดสส !\n<b>ษช แดษชแดษด'แด sสแดแดแด sษชษดแดแดโ:</b> <code>{}</code>".format(
                uptime
            ),
            parse_mode=ParseMode.HTML,
        )


def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


@run_async
def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "ยป *แดแด?แดษชสแดสสแด แดแดแดแดแดษดแดs ๊ฐแดสโโ* *{}* :\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="โ", callback_data="help_back")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass


@run_async
def Fallen_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "fallen_":
        query.message.edit_text(
            text="""*สแดส,\n\n  แดสษชs ษชs *[๐๐น๐ฎ๐ฐ๐ธ ๐ฆ๐ผ๐๐ฒ๐ฟ๐ฒ๐ถ๐ด๐ป](t.me/BlackSovereignRoBot)\n\n*แด แดแดแดกแดส๊ฐแดส ษขสแดแดแด แดแดษดแดษขแดแดแดษดแด สแดแด สแดษชสแด แดแด สแดสแด สแดแด แดแดษดแดษขแด สแดแดส ษขสแดแดแด แดแด๊ฑษชสส แดษดแด แดแด แดสแดแดแดแดแด สแดแดส ษขสแดแดแด ๊ฐสแดแด ๊ฑแดแดแดแดแดส๊ฑ แดษดแด ๊ฑแดแดแดแดแดส๊ฑ. *\n\nษช สแดแด?แด แดสแด ษดแดสแดแดส ษขสแดแดแด แดแดษดแดษขษชษดษข ๊ฐแดษดแดแดษชแดษด๊ฑ สษชแดแด ๊ฐสแดแดแด แดแดษดแดสแดส, แด แดกแดสษดษชษดษข ๊ฑส๊ฑแดแดแด แดแดแด สแดแด ษช แดแดษชษดสส สแดแด?แด แดสแด แดแดแด?แดษดแดแดแด แดษดแด สแดษดแดส แดษดแดษช๊ฑแดแดแด ๊ฑส๊ฑแดแดแด แดษดแด แดสแด สแดษดษดษชษดษข ๊ฑส๊ฑแดแดแด แดกสษชแดส ๊ฑแด๊ฐแดษขแดแดสแด๊ฑ แดษดแด สแดสแด๊ฑ สแดแดส ษขสแดแดแด ๊ฐสแดแด ๊ฑแดแดแดแดแดส๊ฑ.\n\n๐ แดกสแดแด แดแดษด ษช แดแด :\n\nโฒ  ษช แดแดษด สแด๊ฑแดสษชแดแด แด๊ฑแดส๊ฑ.\n\nโฒ  ษช แดแดษด ษขสแดแดแด แด๊ฑแดส๊ฑ แดกษชแดส แดแด๊ฑแดแดแดษชแดขแดสสแด แดกแดสแดแดแดแด แดแด๊ฑ๊ฑแดษขแด๊ฑ แดษดแด แดแด?แดษด ๊ฑแดแด แด ษขสแดแดแด'๊ฑ สแดสแด๊ฑ.\n\nโฒ  ษช แดแดษด แดกแดสษด แด๊ฑแดส๊ฑ แดษดแดษชส แดสแดส สแดแดแดส แดแดx แดกแดสษด๊ฑ, แดกษชแดส แดแดแดส แดสแดแดแด๊ฐษชษดแดแด แดแดแดษชแดษด๊ฑ ๊ฑแดแดส แด๊ฑ สแดษด, แดแดแดแด, แดษชแดแด, แดแดแด.\n\nโฒ  ษช สแดแด?แด แดษด แดแดแด?แดษดแดแดแด แดษดแดษช-๊ฐสแดแดแด ๊ฑส๊ฑแดแดแด.\n\nโฒ  ษช สแดแด?แด แด ษดแดแดแด แดแดแดแดษชษดษข ๊ฑส๊ฑแดแดแด, สสแดแดแดสษช๊ฑแด๊ฑ, แดษดแด แดแด?แดษด แดสแดแดแดแดแดสแดษชษดแดแด สแดแดสษชแด๊ฑ แดษด แดแดสแดแดษชษด แดแดสแดกแดสแด๊ฑ.\n\nโฒ  ษช แดสแดแดแด ๊ฐแดส แดแดแดษชษด๊ฑ แดแดสแดษช๊ฑ๊ฑษชแดษด๊ฑ สแด๊ฐแดสแด แดxแดแดแดแดษชษดษข แดษดส แดแดแดแดแดษดแด แดษดแด แดแดสแด ๊ฑแดแด๊ฐ๊ฐ๊ฑ.\n\n\n* ษช๊ฐ สแดแด สแดแด?แด แดษดส วซแดแด๊ฑแดษชแดษด แดสแดแดแด ๐๐น๐ฎ๐ฐ๐ธ ๐ฆ๐ผ๐๐ฒ๐ฟ๐ฒ๐ถ๐ด๐ป แดสแดษด แดแดษดแดแดแดแด แด๊ฑ แดแด *[๊ฑแดแดแดแดสแด แดสแดแด](t.me/BlackHarbour) *\n\nแดแดแดแด แดกษชแดส โค๏ธ สส *[๐๐จ๐ก๐ง ๐๐ข๐๐ค](https://t.me/gtxPrime)""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="โ", callback_data="fallen_back")
                 ]
                ]
            ),
        )
    elif query.data == "fallen_back":
        query.message.edit_text(
                PM_START_TEXT.format(sql.num_users(), sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )


@run_async
def Source_about_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text="""*สแดส,*\n\n*แดสษชs ษชs ๐๐น๐ฎ๐ฐ๐ธ ๐ฆ๐ผ๐๐ฒ๐ฟ๐ฒ๐ถ๐ด๐ป*\n\n*สแดสแด ษชs แดส sแดแดสแดแด แดแดแดแด :* [๐ก๐ผ๐ ๐ฃ๐๐ฏ๐น๐ถ๐ฐ ๐ฎ๐ ๐ก๐ผ๐](https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEijvba_fiCSMiKCXwC0RVAP3MzBMOhvSW1XvPEfGMwray_FO4qicvPy54cOns3FYYEQfeHsD-c9ZWMRjAU5AT4hWXIQTAqG0pDa9zj0RbAhLPDwRMR2gphEdoGN6yIj1Eev-PGb3q6IaMIQ38ffH7HkyUdTR8HKKZdXebDirQLAoJH38gZyjMgNJBYUYw/s1000/restricted-area-sign-nhe-37295_wrstr_1000.png)\n\n*แดส sแดแดสแดแด แดแดแดแด ษชs ษชษด แดแดแด?แดสแดแดแดแดษดแด แดษดแด ษดแดแด แดแดแดแดสแดแดแดแด สแดแด*\n*sแด ษชา สแดแด าแดแดษดแด แดษดส สแดษข แดส ษชา สแดแด แดกแดษดษดแด สแดวซแดแดsแด แดษดส าแดแดแดแดสแด, แดฉสแดแดsแด สแดแด แดs แดษดแดแดก แดแด* [๐๐น๐ฎ๐ฐ๐ธ ๐๐ฎ๐ฟ๐ฏ๐ผ๐๐ฟ](https://t.me/BlackHarbour) *แดส สแดแด แดแดษด แดแดษดแดแดแดแด แดส แดแดแด?แดสแดแดฉแดส :* [๐๐ผ๐ต๐ป ๐ช๐ถ๐ฐ๐ธ](https://t.me/gtxPrime)""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="โ", callback_data="source_back")
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        query.message.edit_text(
                PM_START_TEXT.format(sql.num_users(), sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

@run_async
def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="สแดสแดโ",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )
            return
        update.effective_message.reply_text(
            "ยป แดสแดแดsแด แดษด แดแดฉแดษชแดษด าแดส ษขแดแดแดษชษดษข สแดสแดฉ.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="แดแดฉแดษด ษชษด แดฉสษชแด?แดแดแด",
                            url="https://t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="แดแดฉแดษด สแดสแด",
                            callback_data="help_back",
                        )
                    ]
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="โ", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


@run_async
def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="โ",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


@run_async
def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="sแดแดแดษชษดษขsโ",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id
                                ),
                            )
                        ]
                    ]
                ),
            )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


@run_async
def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1356469075 and DONATION_LINK:
            update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.send_photo(f"@{SUPPORT_CHAT}", "https://telegra.ph/file/d41b53919d63247bd2b0d.png", caption="๐๐น๐ฎ๐ฐ๐ธ ๐ฆ๐ผ๐๐ฒ๐ฟ๐ฒ๐ถ๐ด๐ป ษชs แดสษชแด?แด !\n\nแดแดแดแด แดกษชแดส โค๏ธ สส ๐๐จ๐ก๐ง ๐๐ข๐๐ค ๐ฅ")
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test)
    start_handler = CommandHandler("start", start)

    help_handler = CommandHandler("help", get_help)
    help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")

    settings_handler = CommandHandler("settings", get_settings)
    settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")

    about_callback_handler = CallbackQueryHandler(Fallen_about_callback, pattern=r"fallen_")
    source_callback_handler = CallbackQueryHandler(Source_about_callback, pattern=r"source_")

    donate_handler = CommandHandler("donate", donate)
    migrate_handler = MessageHandler(Filters.status_update.migrate, migrate_chats)

    # dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, clean=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
