#!/usr/bin/env python
# pylint: disable=C0116,W0613

#Copyright 2022 Queenzeina Productions (quuezeinaproductions@gmail.com)

#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

#######     Easy Help Bot v1.1      #######

import logging
import datetime
import json
import uuid
from typing import Tuple, cast

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    InvalidCallbackData,
    PicklePersistence,
    MessageHandler,
    Filters,
    ConversationHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

NAME, NUMBER, TEXT = range(3)

file = open("config.json", "r")
configuration = json.loads(file.read())
numbers = configuration["numbers"]
file.close()

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    jobs = configuration["autotexting"]

    update.message.reply_text(
        'Come ti posso aiutare:', reply_markup=build_keyboard())

    for i in jobs:
        job = jobs[i]
        remove_job_if_exists(i, context)
        context.job_queue.run_daily(
            alarm, job['time'], job['days'], context=chat_id, name=i)


def answer(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    button = cast(Tuple[int], query.data)

    if button == 'Indietro':
        query.edit_message_text('Come ti posso aiutare:',
                                reply_markup=build_keyboard())
    else:
        query.edit_message_text(
            f"Ecco a te il numero da chiamare\n\n              +39{numbers[button]}\n\n👌",
            reply_markup=build_keyboard(True),
        )


def build_keyboard(back=False) -> InlineKeyboardMarkup:
    if back == True:
        return InlineKeyboardMarkup.from_column(
            [InlineKeyboardButton('Indietro', callback_data=('Indietro'))]
        )
    else:
        return InlineKeyboardMarkup.from_column(
            [InlineKeyboardButton(i, callback_data=(i)) for i in numbers]
        )


def alarm(context: CallbackContext) -> None:
    job = context.job
    obj = configuration["autotexting"][job.name]
    context.bot.send_message(job.context, text=obj["text"])


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def set_job(update: Update, context: CallbackContext) -> int:
    if is_admin(update):
        echohandling(False)
        update.message.reply_text(
            'Usa /cancel per annullare\nOra del messaggio in formato <hh:mm>?')
        return NAME
    else:
        return ConversationHandler.END


def set_time(update: Update, context: CallbackContext) -> int:
    global time
    time = datetime.datetime.strptime(update.message.text, "%H:%M")
    update.message.reply_text(
        'In che giorni deve funzionare, espressi in numeri (lunedì=0) di defaul lunedì-venerdì (0,1,2,3,4)?')

    return NUMBER


def set_days(update: Update, context: CallbackContext) -> int:
    global days
    s = update.message.text

    if s == '':
        days = (0, 1, 2, 3, 4)
    else:
        days = tuple(map(int, s.split(',')))
    update.message.reply_text(
        'Testo del messaggio?')
    return TEXT


def set_text(update: Update, context: CallbackContext) -> int:
    jobname = str(uuid.uuid4())
    configuration['autotexting'][jobname] = {
        'time': time,
        'days': days,
        'text': update.message.text
    }

    update.message.reply_text('Messaggio automatico impostato!')
    echohandling(True)
    return ConversationHandler.END


def unset(update: Update, context: CallbackContext) -> None:
    if is_admin(update):
        if context.args[0] != '':
            index = []
            for i in configuration["autotexting"]:
                index.append(i)
            jobname = index[int(context.args[0])]
            job_removed = remove_job_if_exists(jobname, context)
            text = 'Messaggio automatico rimosso!' if job_removed else 'Non hai messaggi automatici impostati'
        else:
            text = 'Troppo pochi argomenti\n/unset <NUMERO>\nComanda /show per ricevere la lista numerata'
        update.message.reply_text(text)


def show(update: Update, context: CallbackContext) -> None:
    conf = configuration['autotexting']
    text = 'Hai i seguenti messaggi automatici impostati:\n'
    count = 0
    for i in conf:
        count += 1
        text += (str(count) + ' ' +
                 str(conf[i]["time"]) + ' ' + str(conf[i]["days"]))
    update.message.reply_text(text)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        '/start avvia il bot\n/add aggiunge il numero\n'
        '/del elimina il numero\n/edit modifica il numero\n'
        '/update salva la configurazione\n/reset resetta la configurazione'
        '/set imposta il messaggio automatico\n'
        '/unset <NUMERO> rimuove il messaggio automatico\n'
        '/show mostra la lista numerata di messaggi automatici\n'
        '/admin <COMANDO> ... per la gestione degli amministratori\n'
    )


def handle_invalid_button(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    update.effective_message.edit_text(
        'Ci scusiamo per il disagio il servizio non è più disponibile😕\nPer favore invia /start per aggiornare il bot.'
    )


def add_number(update: Update, context: CallbackContext) -> int:
    if is_admin(update):
        echohandling(False)
        update.message.reply_text(
            'Usa /cancel per annullare\nNome a cui associare il numero?'
        )
        return NAME
    else:
        return ConversationHandler.END


def name(update: Update, context: CallbackContext) -> int:
    global temp
    temp = update.message.text
    update.message.reply_text(
        'Numero telefonico?'
    )
    return NUMBER


def phonenumber(update: Update, context: CallbackContext) -> int:
    numbers[temp] = update.message.text

    update.message.reply_text(
        'Numero aggiunto!'
    )

    echohandling(True)
    return ConversationHandler.END


def del_number(update: Update, context: CallbackContext) -> int:
    if is_admin(update):
        echohandling(False)
        update.message.reply_text(
            'Usa /cancel per annullare\nNome da cancellare?'
        )
        return NAME
    else:
        return ConversationHandler.END


def namedel(update: Update, context: CallbackContext) -> int:
    numbers.pop(update.message.text)

    update.message.reply_text(
        'Numero cancellato!'
    )

    echohandling(True)
    return ConversationHandler.END


def edit_number(update: Update, context: CallbackContext) -> int:
    if is_admin(update):
        echohandling(False)
        update.message.reply_text(
            'Usa /cancel per annullare\nNome da modificare?'
        )
        return NAME
    else:
        return ConversationHandler.END


def numberedit(update: Update, context: CallbackContext) -> int:
    numbers[temp] = update.message.text

    update.message.reply_text(
        'Numero modificato!'
    )
    echohandling(True)
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Modifica Annullata'
    )

    echohandling(True)
    return ConversationHandler.END

def echohandling(state: bool) -> None:
    if state:
        updater.dispatcher.add_handler(echohandler)
    else:
        updater.dispatcher.remove_handler(echohandler)


def write(update: Update, context: CallbackContext) -> None:
    if is_admin(update):
        file = open("config.json", "w")
        file.write(json.dumps(configuration))
        file.close()
        update.message.reply_text('Configurazione aggiornata')
        start(update, context)

def reset(update: Update, context: CallbackContext) -> None:
    if is_admin(update):
        global file, configuration, numbers
        file = open("config.json", "r")
        configuration = json.loads(file.read())
        numbers = configuration["numbers"]
        file.close()
        update.message.reply_text('Configurazione ripristinata')
        start(update, context)

def admin(update: Update, context: CallbackContext) -> None:
    try:
        cmd = context.args[0]
    except (IndexError, ValueError):
        cmd = ""
    user = update.message.from_user
    admins = configuration["admin"]["admins"]
    if cmd == "register":
        try:
            if is_admin(update):
                update.message.reply_text('Sei già un amministratore')
            elif context.args[1] == configuration["admin"]["password"]:
                admins.append(user["username"])
                update.message.reply_text('Ora sei un amministratore')
            else:
                update.message.reply_text(
                    'Password di amministrazione errata')
        except (IndexError, ValueError):
            update.message.reply_text('Numero errato di argomenti')
            admin_help(update)
    elif cmd == "help" or cmd == "":
        admin_help(update)
    elif is_admin(update):
        if cmd == "passwd":
            try:
                if context.args[1] == configuration["admin"]["password"]:
                    configuration["admin"]["password"] = context.args[2]
                    update.message.reply_text('Password aggiornata!')
                else:
                    update.message.reply_text(
                        'Password di amministrazione errata')
            except (IndexError, ValueError):
                update.message.reply_text('Numero errato di argomenti')
                admin_help(update)
        elif cmd == "remove":
            try:
                admins.remove(context.args[1])
                update.message.reply_text('Amministratore rimosso!')
            except (IndexError, ValueError):
                update.message.reply_text('Numero errato di argomenti')
                admin_help(update)
        elif cmd == "show":
            text = ""
            for i in admins:
                text += (str(i) + "\n")
            update.message.reply_text(text)
        elif cmd == "telephone":
            try:
                if context.args[1] != configuration["admin"]["telephone"]:
                    update.message.reply_text('Numero telefonico aggiornato!')
                else:
                    update.message.reply_text('Il numero è lo stesso!')
            except (IndexError, ValueError):
                update.message.reply_text('Numero errato di argomenti')
                admin_help(update)
        else:
            update.message.reply_text('Comando non riconosciuto')
    else:
        update.message.reply_text('Non sei un amministratore')


def admin_help(update: Update) -> None:
    update.message.reply_text(
        '/admin <COMANDO> ...\n\nCOMANDI:\n\n'
        'register <PASSWORD> registra l\'utente come amministratore\n\n'
        'passwd <VECCHIAPASSWORD> <NUOVAPASSWORD> cambia password\n\n'
        'remove <USERNAME> per rimuovere l\'amministratore\n\n'
        'show per mostrare gli amministratori\n\n'
        'telephone per cambiare il numero di telefono dell\'amministratore'
    )


def is_admin(update: Update) -> bool:
    admins = configuration["admin"]["admins"]
    user = update.message.from_user
    return (user["username"] in admins)


def echo(update: Update, context: CallbackContext) -> None:
    text = f'Mi spiace non sono in grado di aiutarti😕\nProva a contattare il numero: {configuration["admin"]["telephone"]}'
    update.message.reply_text(text)


def main() -> None:
    global echohandler, updater
    # We use persistence to demonstrate how buttons can still work after the bot was restarted
    persistence = PicklePersistence(
        filename='arbitrarycallbackdatabot.pickle', store_callback_data=True
    )
    # Create the Updater and pass it your bot's token.
    updater = Updater("5687197897:AAGmX0cxlbw3pPNDEyBIhIff-i-MrtIZgFM",
                      persistence=persistence, arbitrary_callback_data=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('help', help_command))
    updater.dispatcher.add_handler(CommandHandler('update', write))
    updater.dispatcher.add_handler(CommandHandler('unset', unset))
    updater.dispatcher.add_handler(CommandHandler('show', show))
    updater.dispatcher.add_handler(CommandHandler('admin', admin))
    updater.dispatcher.add_handler(CommandHandler('reset', reset))

    echohandler = MessageHandler(Filters.text & ~Filters.command, echo)
    updater.dispatcher.add_handler(echohandler)

    updater.dispatcher.add_handler(CallbackQueryHandler(
        handle_invalid_button, pattern=InvalidCallbackData))
    updater.dispatcher.add_handler(CallbackQueryHandler(answer))

    conv_add = ConversationHandler(
        entry_points=[CommandHandler('add', add_number)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, name)],
            NUMBER: [MessageHandler(Filters.regex('^(.........?)$'), phonenumber)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    conv_del = ConversationHandler(
        entry_points=[CommandHandler('del', del_number)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, namedel)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    conv_edit = ConversationHandler(
        entry_points=[CommandHandler('edit', edit_number)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, name)],
            NUMBER: [MessageHandler(Filters.regex('^(.........?)$'), numberedit)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    conv_set = ConversationHandler(
        entry_points=[CommandHandler('set', set_job)],
        states={
            NAME: [MessageHandler(Filters.regex('^(..:..)$'), set_time)],
            NUMBER: [MessageHandler(Filters.text & ~Filters.command, set_days)],
            TEXT: [MessageHandler(Filters.text & ~Filters.command, set_text)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    updater.dispatcher.add_handler(conv_add)
    updater.dispatcher.add_handler(conv_del)
    updater.dispatcher.add_handler(conv_edit)
    updater.dispatcher.add_handler(conv_set)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
