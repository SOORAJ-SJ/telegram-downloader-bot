import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
import telegram
import requests
from hurry.filesize import filesize
from piratebay_crawler.pb_crawler import crawl
from pahe_crawler.crawler import Crawler
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup as bs

pc = Crawler()
load_dotenv()
api_url = 'https://debrid-link.com/api/v2'
debrid_link_api_key = os.environ.get("debrid_link_api_key")
telegram_bot_token = os.environ.get("telegram_bot_token")
bot_commands = ['info', 'list', 'add &lt;magnet&gt;', 'usage', 'torrent &lt;search query&gt;',
                '🛠pahe &lt;search query&gt;', 'status']
headers = {'Authorization': debrid_link_api_key}
multiple_files = {}
piratebay_url = "https://proxybay.github.io/"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
updater = Updater(token=telegram_bot_token, use_context=True)


def start(update, context):
    commands = ''
    for com in bot_commands:
        commands += com + '\n'
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Hi {update.message.from_user.username}\n<b>Available Commands</b>\n{commands}\nUse /&lt;command&gt;',
        parse_mode='HTML',
        reply_to_message_id=update.message.message_id
    )


def debrid_info(update, context):
    req = requests.get(url=api_url + '/account/infos', headers=headers)
    res = req.json()
    if (res['success']):
        context.bot.send_message(chat_id=update.effective_chat.id, text='Connected')


def debrid_list(update, context):
    multiple_files.clear()
    req = requests.get(url=api_url + '/seedbox/list', headers=headers)
    res = req.json()
    print(res['value'])
    if not res['value']:
        context.bot.send_message(chat_id=update.effective_chat.id, text='No files on server!')
    else:
        for item in res['value']:
            if len(item['files']) == 1:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text=f'<b>{item["name"]}</b>\n'
                                              f'Size {filesize.size(item["totalSize"])}\n'
                                              f'Files {len(item["files"])}\n'
                                              f'Downloaded {item["downloadPercent"]}%\n',
                                         parse_mode='HTML',
                                         reply_to_message_id=update.message.message_id,
                                         reply_markup=telegram.InlineKeyboardMarkup(
                                             [
                                                 [
                                                     telegram.InlineKeyboardButton(
                                                         text='Download 🔽',
                                                         url=item['files'][0]['downloadUrl']
                                                     ),
                                                     telegram.InlineKeyboardButton(
                                                         text='Delete 🚮',
                                                         callback_data=res['value'][0]['id']
                                                     )
                                                 ]
                                             ]
                                         )
                                         )
            else:
                file_id = []
                multiple_files[item['id']] = item['files']
                for files in item['files']:
                    file_id.append(files['id'])
                else:
                    file_id_str = ','.join(file_id)
                    zip_req = requests.post(url=api_url + f'/seedbox/{item["id"]}/zip', headers=headers,
                                            data={'ids': file_id_str})
                    zip_res = zip_req.json()
                    print(zip_res)
                    if zip_res['success']:
                        context.bot.send_message(chat_id=update.effective_chat.id,
                                                 text=f'<b>{item["name"]}</b>\n'
                                                      f'Size {filesize.size(item["totalSize"])}\n'
                                                      f'Files {len(item["files"])}\n'
                                                      f'Downloaded {item["downloadPercent"]}%\n',
                                                 parse_mode='HTML',
                                                 reply_to_message_id=update.message.message_id,
                                                 reply_markup=telegram.InlineKeyboardMarkup(
                                                     [
                                                         [
                                                             telegram.InlineKeyboardButton(
                                                                 text='Download Zip 🔽',
                                                                 url=zip_res['value']['downloadUrl']
                                                             ),
                                                             telegram.InlineKeyboardButton(
                                                                 text='Delete 🚮',
                                                                 callback_data='delete ' + item['id']
                                                             ),
                                                         ],
                                                         [
                                                             telegram.InlineKeyboardButton(
                                                                 text='Download individual files ⏬',
                                                                 callback_data='list ' + item['id']
                                                             )
                                                         ]
                                                     ]
                                                 )
                                                 )
                    else:
                        context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong!")


def debrid_add(update, context):
    print(context.args[0])
    if not context.args:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Magnet url required!',
                                 reply_to_message_id=update.message.message_id)
    else:
        req = requests.post(url=api_url + '/seedbox/add', headers=headers, data={'url': context.args[0]})
        res = req.json()
        print(res)
        if res['success']:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'Downloaded {res["value"]["name"]}\n'
                                          f'Size {filesize.size(res["value"]["totalSize"])}\n'
                                          f'Total Files {len(res["value"]["files"])}\n'
                                          f'Download {res["value"]["downloadPercent"]}',
                                     reply_to_message_id=update.message.message_id
                                     )
        else:
            if res['error'] == 'maxTorrent':
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Maximum number of torrents reached!\nDownload Failed!\nUse /usage to see the Usage.",
                    reply_to_message_id=update.message.message_id
                )
            else:
                context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Bad Magnet\nDownload Failed! ",
                    reply_to_message_id=update.message.message_id
                )
        print(res)


def debrid_delete(fid, update, context):
    print(fid)
    if not fid:
        context.bot.send_message(chat_id=update.effective_chat.id, text="file id is required!")
    else:
        req = requests.delete(f'{api_url}/seedbox/{fid}/remove', headers=headers)
        res = req.json()
        print(res)
        if res['success']:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=update.callback_query.message.message_id
            )
            context.bot.send_message(chat_id=update.effective_chat.id, text="Deleted")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Something went wrong!")


def list_multiple_files(fid, update, context):
    print(multiple_files[fid])
    if fid in multiple_files.keys():
        for files in multiple_files[fid]:
            context.bot.send_message(chat_id=update.effective_chat.id, text=files['downloadUrl'])


def debrid_usage(update, context):
    req = requests.get(url=api_url + '/seedbox/limits', headers=headers)
    res = req.json()
    print(res)
    reset_time = int(res['value']['nextResetSeconds']['value']) / 3600
    used_size = filesize.size(int(res['value']['daySize']['current']))
    total_size = filesize.size(int(res['value']['daySize']['value']))
    monthly_used_size = filesize.size(int(res['value']['monthSize']['current']))
    monthly_totla_size = filesize.size(int(res['value']['monthSize']['value']))
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Used {res['value']['usagePercent']['current']}%\n"
             f"Next reset in {round(reset_time, 2)} HR\n"
             f"Daily Usage {used_size}/{total_size}\n"
             f"Torrents per day {res['value']['dayCount']['current']}/{res['value']['dayCount']['value']}\n"
             f"Torrents in last 30 days {res['value']['monthCount']['current']}/{res['value']['monthCount']['value']}\n"
             f"Monthly Usage {monthly_used_size}/{monthly_totla_size}\n"
    )


# test features
def torrent_search(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=crawl(context.args), parse_mode='HTML')


def pahe_search(update, context):
    logging.info(msg="User{0} Query{1}".format(update.message.from_user, context.args))
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action='upload_photo')
    search_results = pc.find_movies(context.args)
    if len(search_results) > 0:
        for tags in search_results[0:5]:
            context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=tags.select(".post-thumbnail>a>img")[0]['src'],
                caption=f"<b>{tags.select('.post-box-title>a')[0].string}</b>",
                parse_mode="HTML",
                reply_markup=telegram.InlineKeyboardMarkup(
                    [
                        [
                            telegram.InlineKeyboardButton(text="Select",
                                                          callback_data='pahe ' + str(search_results.index(tags)))
                        ]
                    ]
                )
            )
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No results found!😪")
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')


def pahe_select_movie(option, update, context):
    logging.info(msg="Option:{0}".format(option))
    download_box = pc.select_movie(option)
    if 'series' in download_box.keys():
        series_kb = []
        for options in download_box['series']:
            for key, episodes in options.items():
                for episode in episodes:
                    series_kb.append([telegram.InlineKeyboardButton(
                        text=episode,
                        callback_data='series ' + str(key) + ' ' + str(episodes.index(episode) + 1))])
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text="Select an episode / season to download",
                                     reply_markup=telegram.InlineKeyboardMarkup(series_kb)
                                     )
    else:
        pahe_available_hosts(update, context, download_box)


def pahe_select_series(update, context):
    logging.info(msg="Option:{0}".format(update.callback_query.data.split(" ")))
    selected_option = update.callback_query.data.split(" ")
    hosts = pc.select_series_option(selected_option[1], selected_option[2])
    pahe_available_hosts(update, context, hosts)


def pahe_available_hosts(update, context, hosts):
    global post_tabs_ver, li, available_hosts
    if 'movies' in hosts.keys():
        available_hosts = [hosts['movies']]
    else:
        post_tabs_ver = [x for x in hosts.keys()]
        li = [x for x in hosts[post_tabs_ver[0]].keys()]
        available_hosts = hosts[post_tabs_ver[0]][li[0]][int(li[0]) - 1]
    keyboards = []
    box_inner_block = 0
    for host in available_hosts:
        print(len(host))
        for tags in host:
            if tags.name == 'div':
                box_inner_block += 1
                count = 0
                kb_group = []
                size = ''
                for tag in tags:
                    if tag.string is not None:
                        if tag.string.rfind("GB") >= 0 or tag.string.rfind("MB") >= 0:
                            size = ''
                            size += tag.string
                            print("found size", tag.string)
                    if tag.name:
                        count += 1
                        if tag.name in ["span", "b", "strong", "em"]:
                            if tag.string:
                                context.bot.send_message(chat_id=update.effective_chat.id, text=tag.string)
                        if len(tag.name) > 8:
                            if 'movies' in hosts.keys():
                                kb_group.append(
                                    telegram.InlineKeyboardButton(text=tag.string,
                                                                  callback_data='movies_download ' + str(
                                                                      box_inner_block) + ' ' + str(count)))
                            else:
                                kb_group.append(
                                    telegram.InlineKeyboardButton(text=tag.string,
                                                                  callback_data='series_download ' + post_tabs_ver[
                                                                      0] + ' ' + li[0] + ' ' + str(
                                                                      box_inner_block) + ' ' + str(count)))
                        if tag.name == "br" and len(kb_group) > 0:
                            keyboards.append(kb_group)
                            context.bot.send_message(chat_id=update.effective_chat.id,
                                                     text=size if size != '' else 'Available Hosts',
                                                     reply_markup=telegram.InlineKeyboardMarkup(keyboards)
                                                     )
                            kb_group = []
                            keyboards = []
                else:
                    keyboards.append(kb_group)
                    context.bot.send_message(chat_id=update.effective_chat.id,
                                             text=size if size != '' else 'Available Hosts',
                                             reply_markup=telegram.InlineKeyboardMarkup(keyboards)
                                             )
                    print(keyboards)
                    kb_group.clear()
                    keyboards.clear()


def pahe_select_file_host(option, update, context, **kwargs):
    logging.info(msg="Option:{0} \n kwargs:{1}".format(option, kwargs))
    print(option)
    file_url = pc.select_file_host(option, **kwargs)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Click Below To Download",
                             reply_markup=telegram.InlineKeyboardMarkup([
                                 [
                                     telegram.InlineKeyboardButton(text="Download", url=file_url)
                                 ]
                             ])
                             )
    pc.cleanup()


def dev_status(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="<u>Status</u>\n"
                                  "Disabled /pahe commands to do some work",
                             # "- Search torrents\n"
                             # "- Seed and download magnets\n"
                             # "- Working on pahe download links\n",
                             parse_mode="HTML"
                             )


def debrid_callback_handler(update, context):
    callback_data = update.callback_query.data.split(" ")
    if callback_data[0] == "series_download":
        pahe_select_file_host(callback_data[4],
                              update,
                              context,
                              div=callback_data[1],
                              li=callback_data[2],
                              box_inner_block=callback_data[3]
                              )
    if callback_data[0] == 'series':
        pahe_select_series(update, context)
    if callback_data[0] == "pahe":
        pahe_select_movie(callback_data[1],
                          update,
                          context
                          )
    if callback_data[0] == "movies_download":
        pahe_select_file_host(
            callback_data[2],
            update,
            context,
            box_inner_block=callback_data[1]
        )
    if callback_data[0] == 'delete':
        debrid_delete(
            callback_data[1],
            update,
            context
        )
    if callback_data[0] == 'list':
        list_multiple_files(callback_data[1], update, context)


start_handler = CommandHandler('start', start)
debrid_info_handler = CommandHandler('info', debrid_info)
debrid_list_handler = CommandHandler('list', debrid_list)
debrid_add_handler = CommandHandler('add', debrid_add)
debrid_usage_handler = CommandHandler('usage', debrid_usage)
torrent_search_handler = CommandHandler('torrent', torrent_search)
pahe_search_handler = CommandHandler('pahe', pahe_search)
dev_handler = CommandHandler('status', dev_status)

updater.dispatcher.add_handler(start_handler)
updater.dispatcher.add_handler(debrid_info_handler)
updater.dispatcher.add_handler(debrid_list_handler)
updater.dispatcher.add_handler(debrid_add_handler)
updater.dispatcher.add_handler(debrid_usage_handler)
updater.dispatcher.add_handler(torrent_search_handler)
updater.dispatcher.add_handler(pahe_search_handler)
updater.dispatcher.add_handler(CallbackQueryHandler(debrid_callback_handler))
updater.dispatcher.add_handler(dev_handler)

updater.start_polling()
