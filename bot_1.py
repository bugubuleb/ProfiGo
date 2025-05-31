import json
import random
import matplotlib.pyplot as plt
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Загрузка вопросов, вузов и RIASEC-направлений
with open('questions.json', 'r', encoding='utf-8') as f:
    questions = json.load(f)
with open('universities.json', 'r', encoding='utf-8') as f:
    universities = json.load(f)
with open('riasec_specialties.json', 'r', encoding='utf-8') as f:
    riasec_specialties = json.load(f)

riasec_questions = questions['riasec']
values_questions = questions['values']
all_questions = riasec_questions + values_questions

# Направления для начального вопроса
directions = {
    "Техника и инженерия": "R",
    "Наука и исследования": "I",
    "Искусство и творчество": "A",
    "Социальная работа и образование": "S",
    "Бизнес и управление": "E",
    "Организация и аналитика": "C"
}

# Возможные предметы ЕГЭ (на основе universities.json)
ege_subjects = [
    "русский", "математика", "физика", "химия", "биология", "информатика",
    "обществознание", "история", "литература", "иностранный язык", "вступительные"
]

# Города
cities = ["Москва", "Санкт-Петербург", "Казань"]

# Приоритет направлений по ценностям
value_priorities = {
    "Доход": ["Бизнес-информатика", "Прикладная информатика", "Экономика", "Менеджмент", "Юриспруденция"],
    "Стабильность": ["Государственное и муниципальное управление", "Юриспруденция", "Экономика"],
    "Творческая свобода": ["Журналистика", "Дизайн", "Издательское дело", "Реклама и связи с общественностью"],
    "Социальная значимость": ["Психология", "Психолого-педагогическое образование", "Социология"],
    "Карьерный рост": ["Бизнес-информатика", "Менеджмент", "Экономика"],
    "Баланс работы и жизни": ["Туризм", "Филология", "Экология и природопользование"]
}


# Функции для работы с JSON
def load_users():
    try:
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# Начало теста
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    users = load_users()

    if chat_id in users and users[chat_id].get('completed', False):
        await update.message.reply_text(
            "Ты уже проходил тест. Используй /myresults, чтобы увидеть результаты, или /restart, чтобы пройти заново.")
    else:
        question_order = list(range(len(all_questions)))
        random.shuffle(question_order)
        users[chat_id] = {
            'current_question': 0,
            'completed': False,
            'initial_directions': [],
            'answers': [],
            'question_order': question_order,
            'current_options': {},
            'university_test': {'stage': None}
        }
        save_users(users)
        await update.message.reply_text(
            "Привет! 👋 Давай узнаем, какое направление обучения тебе подходит. Сначала выбери направления, в которых ты хотел бы работать.")
        await ask_initial_directions(update, context, chat_id)


# Перезапуск теста
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    users = load_users()

    question_order = list(range(len(all_questions)))
    random.shuffle(question_order)
    users[chat_id] = {
        'current_question': 0,
        'completed': False,
        'initial_directions': [],
        'answers': [],
        'question_order': question_order,
        'current_options': {},
        'university_test': {'stage': None}
    }
    save_users(users)
    await update.message.reply_text(
        "Тест сброшен! Давай начнем заново. Выбери направления, в которых ты хотел бы работать.")
    await ask_initial_directions(update, context, chat_id)


# Начальный вопрос
async def ask_initial_directions(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: str):
    users = load_users()
    user = users.get(chat_id, {'initial_directions': []})
    selected_directions = user['initial_directions']

    remaining_directions = [d for d in directions.keys() if d not in selected_directions]
    keyboard = [[direction] for direction in remaining_directions] + [["Готово"]]

    await update.message.reply_text(
        f"В каких направлениях ты хотел бы работать? Выбери все подходящие варианты, затем нажми 'Готово'.\nВыбрано: {', '.join(selected_directions) if selected_directions else 'ничего не выбрано'}.",
        reply_markup={'keyboard': keyboard, 'one_time_keyboard': True}
    )


# Обработка начального вопроса
async def handle_initial_directions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    answer_text = update.message.text
    users = load_users()

    if chat_id not in users:
        question_order = list(range(len(all_questions)))
        random.shuffle(question_order)
        users[chat_id] = {
            'current_question': 0,
            'completed': False,
            'initial_directions': [],
            'answers': [],
            'question_order': question_order,
            'current_options': {},
            'university_test': {'stage': None}
        }

    user = users[chat_id]

    if answer_text == "Готово":
        if not user['initial_directions']:
            await update.message.reply_text("Выбери хотя бы одно направление перед тем, как нажать 'Готово'.")
            await ask_initial_directions(update, context, chat_id)
        else:
            user['current_question'] = 1
            save_users(users)
            await update.message.reply_text("Отлично! Теперь ответь на 50 вопросов теста.")
            await ask_question(update, context, 1, chat_id)
    elif answer_text in directions:
        if answer_text not in user['initial_directions']:
            user['initial_directions'].append(answer_text)
            save_users(users)
        await ask_initial_directions(update, context, chat_id)
    else:
        await update.message.reply_text("Пожалуйста, выбери одно из предложенных направлений или 'Готово'.")
        await ask_initial_directions(update, context, chat_id)


# Задавание вопроса профориентационного теста
async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question_index: int, chat_id: str):
    users = load_users()
    user = users.get(chat_id)

    if not user or 'question_order' not in user:
        await update.message.reply_text("Пожалуйста, начни тест с команды /start.")
        return

    if question_index <= len(all_questions):
        question_idx = user['question_order'][question_index - 1]
        question = all_questions[question_idx]

        options = list(question['options'].items())
        random.shuffle(options)
        options_dict = dict(options)
        options_text = [value for _, value in options]

        keyboard = [[option] for option in options_text]
        await update.message.reply_text(
            question['question'],
            reply_markup={'keyboard': keyboard, 'one_time_keyboard': True}
        )
        user['current_options'] = options_dict
        save_users(users)
    else:
        await complete_test(update, context)


# Обработка ответа
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    answer_text = update.message.text
    users = load_users()

    if chat_id not in users:
        await update.message.reply_text("Пожалуйста, начни тест с команды /start.")
        return

    user = users[chat_id]
    current_question = user['current_question']
    university_test = user.get('university_test', {'stage': None})

    # Профориентационный тест
    if current_question == 0:
        await handle_initial_directions(update, context)
    elif current_question <= len(all_questions):
        question_idx = user['question_order'][current_question - 1]
        question_type = 'riasec' if question_idx < len(riasec_questions) else 'values'

        current_options = user.get('current_options', {})
        try:
            answer_key = next(key for key, value in current_options.items() if value == answer_text)
            user['answers'].append({'question_type': question_type, 'answer': answer_key})
            user['current_question'] = current_question + 1
            save_users(users)
            await ask_question(update, context, user['current_question'], chat_id)
        except StopIteration:
            await update.message.reply_text("Пожалуйста, выбери один из предложенных вариантов.")
            await ask_question(update, context, current_question, chat_id)
    # Тест на выбор вуза
    elif university_test['stage'] == 'subjects':
        selected_subjects = [s.strip().lower() for s in answer_text.split(',')]
        invalid_subjects = [s for s in selected_subjects if s not in ege_subjects]
        if invalid_subjects:
            await update.message.reply_text(
                f"Некоторые предметы ({', '.join(invalid_subjects)}) не найдены. Выбери из: {', '.join(ege_subjects)}. Укажи предметы через запятую.")
            return
        user['university_test']['subjects'] = selected_subjects
        user['university_test']['stage'] = 'city'
        save_users(users)
        keyboard = [[city] for city in cities]
        await update.message.reply_text("В каком городе ты хочешь учиться?",
                                        reply_markup={'keyboard': keyboard, 'one_time_keyboard': True})
    elif university_test['stage'] == 'city':
        if answer_text not in cities:
            await update.message.reply_text(f"Пожалуйста, выбери город: {', '.join(cities)}.")
            keyboard = [[city] for city in cities]
            await update.message.reply_text("В каком городе ты хочешь учиться?",
                                            reply_markup={'keyboard': keyboard, 'one_time_keyboard': True})
            return
        user['university_test']['city'] = answer_text
        user['university_test']['stage'] = 'paid'
        save_users(users)
        keyboard = [["Да"], ["Нет"]]
        await update.message.reply_text("Рассматриваешь ли ты платное обучение?",
                                        reply_markup={'keyboard': keyboard, 'one_time_keyboard': True})
    elif university_test['stage'] == 'paid':
        if answer_text not in ["Да", "Нет"]:
            await update.message.reply_text("Пожалуйста, выбери 'Да' или 'Нет'.")
            keyboard = [["Да"], ["Нет"]]
            await update.message.reply_text("Рассматриваешь ли ты платное обучение?",
                                            reply_markup={'keyboard': keyboard, 'one_time_keyboard': True})
            return
        user['university_test']['paid'] = answer_text == "Да"
        save_users(users)
        await recommend_universities(update, context)


# Завершение профориентационного теста
async def complete_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    users = load_users()
    user = users.get(chat_id)

    if not user or not user['answers']:
        await update.message.reply_text("Ты еще не проходил тест. Начни с команды /start.")
        return

    # Анализ RIASEC
    riasec_answers = [a['answer'] for a in user['answers'] if a['question_type'] == 'riasec']
    riasec_scores = {typ: riasec_answers.count(typ) for typ in 'RIASEC'}
    top_riasec = sorted(riasec_scores, key=riasec_scores.get, reverse=True)[:2]

    # Анализ ценностей
    values_answers = [a['answer'] for a in user['answers'] if a['question_type'] == 'values']
    values_scores = {val: values_answers.count(val) for val in
                     ["Доход", "Стабильность", "Творческая свобода", "Социальная значимость", "Карьерный рост",
                      "Баланс работы и жизни"]}
    top_values = sorted(values_scores, key=values_scores.get, reverse=True)[:2]

    # Сравнение начальных направлений
    initial_riasec = {directions[d] for d in user['initial_directions']}
    match = initial_riasec.issuperset(top_riasec) or initial_riasec.intersection(top_riasec)

    # Визуализация
    plt.figure(figsize=(8, 4))
    plt.bar(riasec_scores.keys(), riasec_scores.values(), color='skyblue')
    plt.title('Твой профиль RIASEC')
    plt.savefig('riasec.png')
    plt.close()

    plt.figure(figsize=(8, 4))
    plt.bar(values_scores.keys(), values_scores.values(), color='lightgreen')
    plt.title('Твои ценности')
    plt.savefig('values.png')
    plt.close()

    # Отправка результатов
    recommendations = generate_recommendations(top_riasec, top_values, user['initial_directions'], match)
    await update.message.reply_text(f"Твой профиль: {''.join(top_riasec)}. Твои ценности: {', '.join(top_values)}.")
    await update.message.reply_text(recommendations)
    await update.message.reply_photo(open('riasec.png', 'rb'))
    await update.message.reply_photo(open('values.png', 'rb'))

    # Инициализация теста на выбор вуза
    users[chat_id] = {
        'completed': True,
        'riasec_profile': ''.join(top_riasec),
        'top_values': top_values,
        'university_test': {
            'stage': 'subjects',
            'subjects': [],
            'city': None,
            'paid': None
        }
    }
    save_users(users)
    await update.message.reply_text(
        "Отлично! Теперь давай подберём вуз и направление. Какие предметы ЕГЭ ты сдаёшь или планируешь сдавать? Укажи через запятую (например: русский, математика, физика). Доступные предметы: " + ', '.join(
            ege_subjects))


# Генерация профориентационных рекомендаций
def generate_recommendations(top_riasec, top_values, initial_directions, match):
    base_recommendation = ""
    if set(top_riasec) == {'R', 'I'}:
        if "Доход" in top_values:
            base_recommendation = "Тебе подойдут направления: Информационные технологии, Инженерия. Профессии: Программист, Инженер."
        else:
            base_recommendation = "Тебе подойдут направления: Наука, Техника. Профессии: Ученый, Техник."
    elif set(top_riasec) == {'A', 'S'}:
        if "Творческая свобода" in top_values:
            base_recommendation = "Тебе подойдут направления: Дизайн, Искусство. Профессии: Дизайнер, Художник."
        else:
            base_recommendation = "Тебе подойдут направления: Социальная работа, Образование. Профессии: Социальный работник, Учитель."
    else:
        base_recommendation = f"Твой профиль: {''.join(top_riasec)}. Рекомендуем рассмотреть направления, связанные с {', '.join(top_riasec)}."

    if match:
        return f"{base_recommendation}\nОтлично! Направления, которые ты выбрал в начале ({', '.join(initial_directions)}), совпадают с результатами теста. Ты на правильном пути!"
    else:
        return f"{base_recommendation}\nТвои начальные предпочтения ({', '.join(initial_directions)}) не совсем совпадают с результатами теста. Рекомендуем обратить внимание на направления, предложенные тестом!"


# Рекомендации по вузам
async def recommend_universities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    users = load_users()
    user = users.get(chat_id)

    if not user or not user.get('university_test'):
        await update.message.reply_text("Пожалуйста, начни тест с команды /start.")
        return

    riasec_profile = user.get('riasec_profile', '')
    top_values = user.get('top_values', [])
    subjects = user['university_test']['subjects']
    city = user['university_test']['city']
    paid = user['university_test']['paid']

    # Фильтрация направлений
    recommendations = []
    for university in universities:
        if university['city'] != city:
            continue
        for specialty in university['specialties']:
            # Проверка предметов (все требуемые предметы должны быть в списке пользователя, или должен быть "вступительные")
            if "вступительные" not in specialty['ege_subjects'] and not all(
                    subject in subjects for subject in specialty['ege_subjects']):
                continue
            # Проверка RIASEC
            if not any(specialty['name'] in riasec_specialties[typ] for typ in riasec_profile):
                continue
            # Проверка платного/бюджетного
            if not paid and (specialty['budget_places'] is None or specialty['budget_places'] == 0):
                continue
            # Приоритет по ценностям
            value_score = sum(1 for value in top_values if specialty['name'] in value_priorities.get(value, []))

            recommendations.append({
                'university': university['university_name'],
                'specialty': specialty['name'],
                'city': university['city'],
                'budget_score': specialty['budget_score'],
                'paid_score': specialty['paid_score'],
                'budget_places': specialty['budget_places'],
                'paid_places': specialty['paid_places'],
                'cost': specialty['cost'],
                'ege_subjects': specialty['ege_subjects'],
                'study_mode': specialty['study_mode'],
                'value_score': value_score
            })

    # Сортировка по ценностям и выбор до 5
    recommendations = sorted(recommendations, key=lambda x: x['value_score'], reverse=True)[:5]

    # Формирование ответа
    if not recommendations:
        await update.message.reply_text(
            "К сожалению, подходящих направлений не найдено. Попробуй изменить предметы, город или рассмотреть платное обучение с помощью /restart.")
    else:
        response = "Рекомендованные направления для поступления:\n\n"
        for rec in recommendations:
            response += f"🏛️ {rec['university']} ({rec['city']})\n"
            response += f"📚 Направление: {rec['specialty']}\n"
            response += f"📋 Требуемые предметы: {', '.join(rec['ege_subjects'])}\n"
            response += f"📖 Форма обучения: {rec['study_mode'] or 'не указана'}\n"
            if rec['budget_places']:
                response += f"🆓 Бюджет: {rec['budget_places']} мест, проходной балл: {rec['budget_score'] or 'не указан'}\n"
            if paid and rec['paid_places']:
                response += f"💸 Платное: {rec['paid_places']} мест, проходной балл: {rec['paid_score'] or 'не указан'}, стоимость: {rec['cost'] or 'не указана'} руб./год\n"
            response += "\n"
        await update.message.reply_text(response)

    # Очистка временных данных
    users[chat_id] = {
        'completed': True,
        'riasec_profile': user['riasec_profile'],
        'top_values': user['top_values']
    }
    save_users(users)


# Просмотр результатов
async def myresults(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)
    users = load_users()

    if chat_id in users and users[chat_id].get('completed', False):
        riasec_profile = users[chat_id]['riasec_profile']
        top_values = users[chat_id]['top_values']

        riasec_scores = {typ: 1 if typ in riasec_profile else 0 for typ in 'RIASEC'}
        plt.figure(figsize=(8, 4))
        plt.bar(riasec_scores.keys(), riasec_scores.values(), color='skyblue')
        plt.title('Твой профиль RIASEC')
        plt.savefig('riasec.png')
        plt.close()

        values_scores = {val: 1 if val in top_values else 0 for val in
                         ["Доход", "Стабильность", "Творческая свобода", "Социальная значимость", "Карьерный рост",
                          "Баланс работы и жизни"]}
        plt.figure(figsize=(8, 4))
        plt.bar(values_scores.keys(), values_scores.values(), color='lightgreen')
        plt.title('Твои ценности')
        plt.savefig('values.png')
        plt.close()

        await update.message.reply_text(f"Твой профиль: {riasec_profile}. Твои ценности: {', '.join(top_values)}.")
        await update.message.reply_text(generate_recommendations(list(riasec_profile), top_values, [], True))
        await update.message.reply_photo(open('riasec.png', 'rb'))
        await update.message.reply_photo(open('values.png', 'rb'))
    else:
        await update.message.reply_text(
            "Ты еще не завершил тест. Начни с команды /start или продолжи отвечать на вопросы!")


# Основная функция
def main():
    app = Application.builder().token("8002126599:AAF30u86GTRehtsqndQ_flLyBf8v2qvs6bQ").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("myresults", myresults))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    app.run_polling()


if __name__ == '__main__':
    main()