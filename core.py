from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, ConversationHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from conf.settings import BASE_API_URL, TELEGRAM_TOKEN

import requests
import logging
import os

PORT = int(os.environ.get('PORT', 5000))

logger = logging.getLogger(__name__)
TOKEN = TELEGRAM_TOKEN
SELECT = range(1)


def help(update, context):
    user = update.message.from_user
    response_message = "Olá " + user.first_name + " !!!" + '\n\n' + 'Para começar digite /search + o nome de um filme  \n'

    context.bot.send_message(chat_id=update.message.chat_id, text=response_message)


def search(update, context):
    global films
    parameter = context.args
    user = update.message.from_user
    logger.info("Search of %s: %s", user.first_name, update.message.text)
    logger.info("Search of %s: %s", user.first_name, parameter)
    if isinstance(parameter, list):
        parameter = ' '.join([str(elem) for elem in parameter])
    if ' ' in parameter:
        list_parameter = []
        for item in parameter.split(' '):
            list_parameter.append(item.capitalize())
        parameter = ' '.join(list_parameter)
    else:
        parameter = parameter.capitalize()

    data = requests.get('https://gist.githubusercontent.com/cleitonleonel/3d894a0b2d0643d7918b095fccdae047/raw/4437e426015c460ba63a9fdc334e8228c2c9fdb6/filmes.json').json()

    films = []
    for i, item in enumerate(data):
        try:
            if parameter in str(item['title']):
                films.append(item)
        except:
            pass
    print(films)

    logger.info("Search of %s: %s", user.first_name, parameter)

    logger.info("Films of %s: %s", user.first_name, films)

    list_filmes = []
    for index, film in enumerate(films):
        list_filmes.append(str(index) + ' == ' + film['title'])
    if len(list_filmes) == 0:
        logger.info("Films_list len of %s: %s", user.first_name, len(list_filmes))
        response_message = f'Desculpe {user.first_name}, não encontrei nenhum filme.'
        context.bot.send_message(chat_id=update.message.chat_id, text=response_message)
        return ConversationHandler.END
    update.message.reply_text(
        f'Oi {user.first_name}! Encontrei esses filmes: \n\n'
        + '\n'.join(list_filmes) + '\n\n'
        'Escolha um filme enviando o número correspondente. \n\n'
        'Envie /cancel ou /exit para parar de falar comigo.')

    return SELECT


def select_film(update, context):
    user = update.message.from_user
    selected = update.message.text.replace('/', '')
    if selected.isalpha():
        response_message = 'Ok! Quando quiser um bom filme me chame.'
        context.bot.send_message(chat_id=update.message.chat_id, text=response_message)
        return ConversationHandler.END
    else:
        selected = int(selected)
    try:
        print(films[selected]['url'])
    except:
        return select_film
    filme = films[selected]['url']
    title = films[selected]['title']
    img = films[selected]['img']
    description = films[selected]['description']
    player_url = films[selected]['player']
    try:
        video_url = films[selected]['stream']
    except:
        response_message = 'Desculpe! Não encontrei links para esse filme.'
        context.bot.send_message(chat_id=update.message.chat_id, text=response_message)
        return ConversationHandler.END
    else:
        response_message = video_url
        logger.info(response_message)
        text_html = f"<a href='{response_message}'>{title}</a>"
        if img:
            filename = img.split("/")[-1]
            r = requests.get(img, timeout=0.5)

            if r.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(r.content)
                img = filename

            with open(img, 'rb') as film_picture:
                caption = text_html
                context.bot.send_photo(
                    chat_id=update.message.chat_id,
                    photo=film_picture,
                    caption=caption,
                    parse_mode='HTML'
                )
            os.remove(filename)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text=text_html, parse_mode='HTML')


def skip_select(update, context):
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Ok! Quando quiser um bom filme me chame.')

    return ConversationHandler.END


def unknown(update, context):
    response_message = "Meow? =^._.^="
    context.bot.send_message(chat_id=update.message.chat_id, text=response_message)


def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Tchau! Espero que possamos conversar novamente algum dia.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def exit(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Tchau! Quando quiser um bom filme me chame.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    dispatcher.add_handler(CommandHandler("help", help))

    conv_search = ConversationHandler(
        entry_points=[CommandHandler('search', search, pass_args=True)],

        states={
            SELECT: [MessageHandler(Filters.text, select_film),
                     CommandHandler('skip', skip_select)],
        },

        fallbacks=[CommandHandler('exit', exit)]
    )

    dispatcher.add_handler(conv_search)

    dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    # Start the Bot
    #updater.start_polling()

    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://robot-dev.herokuapp.com/' + TOKEN)

    updater.idle()


if __name__ == "__main__":
    print("press CTRL + C to cancel.")
    main()
