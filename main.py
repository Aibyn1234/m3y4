from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove()

cancel_button = "Отмена 🚫"
def cansel(message):
    bot.send_message(message.chat.id, "❌ Отменено. Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)

def no_projects(message):
    bot.send_message(message.chat.id, '📝 У тебя пока нет проектов!\nТы можешь добавить один с помощью команды /new_project')

def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

attributes_of_projects = {
    'Имя проекта': ["✏️ Введите новое имя проекта", "project_name"],
    "Описание": ["📄 Введите новое описание проекта", "description"],
    "Ссылка": ["🔗 Введите новую ссылку на проект", "url"],
    "Статус": ["📈 Выберите новый статус проекта", "status_id"]
}

def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    skills = ', '.join(skills) if skills else '❌ Навыки не добавлены'
    bot.send_message(message.chat.id, f"""
📁 {info[0]}
📝 Описание: {info[1]}
🔗 Ссылка: {info[2]}
📈 Статус: {info[3]}
🧠 Навыки: {skills}
""", reply_markup=hideBoard)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 
"""👋 Привет! Я бот-менеджер проектов 🤖
Я помогу тебе:
📌 Хранить информацию о проектах
📈 Следить за прогрессом
🎯 Улучшать навыки

Введи /info чтобы узнать, что я умею! 🚀
""")
    info(message)

@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
"""📌 Список доступных команд:

🆕 /new_project — создать новый проект (имя, описание, ссылка, статус)

📋 /projects — список всех проектов с подробной информацией

💡 /skills — добавь навык к проекту

❌ /delete — удалить проект (удаление безвозвратное!)

🔄 /update_projects — изменить имя, описание, ссылку или статус

ℹ️ /info — показать это сообщение

👋 /start — приветственное сообщение и краткая инструкция

🔚 Для отмены любого действия используй кнопку 'Отмена 🚫'
""")

@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "🆕 Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "📄 Введите описание проекта:")
    bot.register_next_step_handler(message, description_project, data=data)

def description_project(message, data):
    data.append(message.text)
    bot.send_message(message.chat.id, "🔗 Введите ссылку на проект:")
    bot.register_next_step_handler(message, link_project, data=data)

def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()]
    bot.send_message(message.chat.id, "📈 Выберите текущий статус проекта:", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "⚠️ Выбран статус не из списка, попробуй ещё раз!", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    bot.send_message(message.chat.id, '✅ Проект успешно сохранён!', reply_markup=hideBoard)

@bot.message_handler(commands=['skills'])
def skill_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, '🧠 Выбери проект, к которому хочешь добавить навык:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)

def skill_project(message, projects):
    project_name = message.text
    if project_name == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, '⚠️ Такого проекта нет. Выбери из списка:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
        return
    skills = [x[1] for x in manager.get_skills()]
    bot.send_message(message.chat.id, '🧠 Выбери навык:', reply_markup=gen_markup(skills))
    bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if skill == cancel_button:
        cansel(message)
        return
    if skill not in skills:
        bot.send_message(message.chat.id, '⚠️ Неверный навык. Попробуй ещё раз:', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)
    bot.send_message(message.chat.id, f'✅ Навык {skill} добавлен к проекту {project_name}!', reply_markup=hideBoard)

@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n\n".join([f"📁 {x[2]}\n🔗 {x[4]}" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)

@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n\n".join([f"🗑️ {x[2]}\n🔗 {x[4]}" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)

def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id
    if project == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, '⚠️ Такого проекта нет. Попробуй ещё раз:', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'🗑️ Проект {project} удалён!', reply_markup=hideBoard)

@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "🔧 Выбери проект, который хочешь изменить:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)

def update_project_step_2(message, projects):
    project_name = message.text
    if project_name == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "⚠️ Неверный выбор. Попробуй ещё раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    bot.send_message(message.chat.id, "🔧 Что ты хочешь изменить?", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None
    if attribute == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects:
        bot.send_message(message.chat.id, "⚠️ Ошибка. Попробуй ещё раз:", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    if attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup = gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

def update_project_step_4(message, project_name, attribute):
    update_info = message.text
    if update_info == cancel_button:
        cansel(message)
        return
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info not in [x[0] for x in rows]:
            bot.send_message(message.chat.id, "⚠️ Неверный статус. Попробуй ещё раз:", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
        update_info = manager.get_status_id(update_info)
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "✅ Обновление сохранено!", reply_markup=hideBoard)

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects = [x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
    else:
        bot.reply_to(message, "🤖 Тебе нужна помощь?")
        info(message)

if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()
