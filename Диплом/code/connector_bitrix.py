import requests
import json
import datetime
import base64
from PIL import Image
import io
from io import BytesIO
import Settings as set

################

def get_user(tg_id_user: int):
    """
    :param tg_name: имя в тлеграмме
    :return: [id из bitrix и ФИО]
    """
    try:
        teg = set.TG_NAME[tg_id_user][1]
    except:
        return not None
    r = requests.get(set.BASE_URL + set.WH_USER + str(teg)).json()
    js = r['result'][0]
    user_name = f"{set.TG_NAME[tg_id_user][1]}|{js['LAST_NAME']} {js['NAME']}".split("|")
    return user_name

# a = get_user(313476377)
# print(a)

def get_val_of_list(name_field) -> dict:  #'PROPERTY_251' 'PROPERTY_254'
    '''
    :param name_field: Кодовое название поля
    :return: возвращает словарь ключ значение поля который имеет формат Списка
    '''
    json_routes = {
            'IBLOCK_TYPE_ID': 'lists', # 'lists_socnet'
            'IBLOCK_ID': set.KEY_ROUTE,
            'FIELD_ID' : name_field}
    r = requests.post(set.BASE_URL + set.WH_FIELDS, json=json_routes)
    js_test = r.json() ['result']
    try:
        result = js_test['L']['DISPLAY_VALUES_FORM']
        return result
    except:
        None


def get_key_area(dict_area:dict, name_area):
    '''
    :param dict_area:  словарь
    :param name_area: какое то значение из словоря в данном случае название полощадки
    :return: получаем ключ по знаению
    '''
    return list(dict_area.keys())[list(dict_area.values()).index(name_area)]


def replace_status_name(text: str) -> str:
    new_text = text \
        .replace(set.ST_SM_PROVERKA, 'На проверке гл. инспектора') \
        .replace(set.ST_SM_NOVAY, 'Новая') \
        .replace(set.ST_SM_INWORK, 'В работе') \
        .replace(set.ST_SM_INCONFIRM, 'На подтверждении')
    return str(new_text)


def get_field_route_by_id(id, field='NAME'):
    """
    :param id: запись маршрута
    :param field:  Поле которое надо вернуть
    :return:  если параметр field не указан то по  умолчанию возврщает поле NAME  иначе другое поле  с проверкой на словарь
    """
    json_routes_by_id = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': set.KEY_ROUTE,
        'FILTER': {'=ID': id}
    }
    r = requests.post(set.BASE_URL + set.WH_ROUTES, json=json_routes_by_id)  # , json=json_reg_test
    js_test = r.json()['result'][0]
    if type(js_test[field]) is dict:
        return list(js_test[field].values())[0]
    else:
        return js_test[field]


def update_status_route(id_route):
    '''
    :param id_route: id маршрута
    :return:  обновляет статус маршрута на
    '''
    url_get = set.BASE_URL + set.WH_ROUTES
    url_update = set.BASE_URL + set.WH_ROUTES_UPDATE
    # получаем елемент со значениями
    json_fields_element = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': set.KEY_ROUTE,
        'FILTER': {'=ID': id_route}}
    response_get = requests.post(url_get, json=json_fields_element)  #
    # обновляем  js
    js = response_get.json()['result'][0]
    js[set.FIELD_STATUS] = set.ST_R_CLOSED
    json_status_update = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': set.KEY_ROUTE,
        'ELEMENT_ID': id_route}

    json_status_update['FIELDS'] = js
    #new_js = json.dumps(json_status_update, indent=4,ensure_ascii=False)

    response_update = requests.post(url_update, json=json_status_update)
    return  response_update


def get_area_or_work(id_user, name_area=0, status=set.ST_R_ACTIVE) -> list:
    '''
    :param id_user:  Id  юзера битрикс
    :param name_area:
    :param status:
    :return:
    '''
    url = set.BASE_URL + set.WH_ROUTES
    json_parametr_area = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': set.KEY_ROUTE,
        'ELEMENT_ORDER': {"ID": "ASC"}
    }
    dict_area = get_val_of_list(set.FIELD_AREA)
    last_id = '0'
    full_list = []
    key_area = get_key_area(dict_area, name_area) if name_area != 0 else ''
    area_or_work = 1 if name_area != 0 else 0
    if id_user != None:
        filter_area = {'FILTER': {#'f'={set.FIELD_INSPEC}': id_user,
                                  f'={set.FIELD_STATUS}': status,
                                  '>ID': '0'}}
        filter_work = {'FILTER': {f'={set.FIELD_AREA}': key_area}}  # поиск  работ на выбранной площадке
        filters = {'FILTER': filter_area['FILTER'] | filter_work['FILTER']} if name_area != 0 else filter_area
        parametr = json_parametr_area | filters if filter_area else None
        #print(parametr)
        while last_id is not None:
            parametr['FILTER']['>ID'] = last_id
            #print(parametr)
            response = requests.post(url, json=parametr)  #
            js = response.json()['result']
            if js:
                for i in js:
                    full_list.append(i)
                    last_id = i["ID"]
            else:
                last_id = None

        base_list = []
        for i in full_list:
            row = f'{list([x for x in i[set.FIELD_AREA].values()])[0]}' \
                  f'|{i["NAME"]}' \
                # f'|{in_list.append(list([x for x in i["PROPERTY_251"].values()])[0])}' #status'
            base_list.append(row.split('|'))
        list_area = []
        for area in base_list:
            try:
                dict_area[area[area_or_work]]
                if dict_area[area[area_or_work]] not in list_area:
                        list_area.append(dict_area[area[area_or_work]])
            except:
                if area[area_or_work] not in list_area:
                        list_area.append(area[area_or_work])

        return sorted(list_area)
    else:
        None


def get_id_work(id_user, name_area, name_work):
    '''
    :param id_user: id пользователя битрикс
    :param name_area: название площадки
    :param name_work: название работы (название работ могут повтарятся на разных площадках
    :return:  возвращает Id  номер работы которую выбрал  пользователь
    '''
    dict_area = get_val_of_list(set.FIELD_AREA)
    json_id_work = {
        'IBLOCK_TYPE_ID': 'lists',
        'IBLOCK_ID': set.KEY_ROUTE,
        'FILTER': {f'={set.FIELD_AREA}': get_key_area(dict_area, name_area),
                   '=NAME': name_work,
                   #f'={set.FIELD_INSPEC}': id_user,
                   },
    }
    r = requests.post(set.BASE_URL + set.WH_ROUTES, json=json_id_work)  # , json=json_reg_test
    if r.json()['result']:
        js_table = r.json()['result'][0]
        return js_table['ID']
    else:
        return None


def get_reg_list(id_type_work):  # 18078
    '''
    :param id_type_work: id работы
    :return:  возвращает список замечаний  на данной работе
    '''
    json_reg = {
        'entityTypeId': set.KEY_SMART,
        'select': ['id', 'createdTime', 'title', 'ufCrm5Way', 'ufCrm5PicIncons', 'ufCrm5TaskDef', 'assignedById',
                   'ufCrm5PlanDate', 'stageId'],
        'filter': {  # '!=assignedById':'',
            # '=id':'4',
            'ufCrm5Way': str(id_type_work),
            'stageId': [set.ST_SM_INCONFIRM, set.ST_SM_NOVAY, set.ST_SM_INWORK, set.ST_SM_PROVERKA]
        }
    }
    r = requests.post(set.BASE_URL + set.WH_REG, json=json_reg)  # , json=json_reg_test
    js_test = r.json()
    final_list = []
    for i in js_test['result']['items']:
        final_list.append(list(i.values()))
    return final_list


def get_comment_photo_url(id_comment):  # 18078
    '''
    :param id_comment:
    :return:  получаем список фотографий которые сделанны в этом коментарии
    '''
    json_photo_url = {
        'entityTypeId': set.KEY_SMART,
        'select': ['ufCrm5PicIncons'],
        'filter': {'=id': id_comment}
    }
    r = requests.post(set.BASE_URL + set.WH_REG, json=json_photo_url)  # , json=json_reg_test
    js_url = r.json()['result']['items'][0]['ufCrm5PicIncons']
    check_data = js_url
    if js_url:
        list_photo = []
        for i in js_url:
            list_photo.append(i['urlMachine'])
        data = requests.get(list_photo[0]).content
        im = Image.open(BytesIO(data))
        return im
    else:
        return None


def save_comment(inspector_id: int, route_id: int, assigned_id: int, comment: str, photo=None):
    ''' сохраняем коментарий '''
    json_reg_save = {
        'entityTypeId': set.KEY_SMART,
        'fields': {
            'createdTime': str(datetime.datetime.now()),  # дата создания
            'title': 'Замечание из телеграмм бота',  # название замечания
            'ufCrm5Way': route_id,  # код из маршрутa
            'ufCrm5TaskDef': comment,  # коментарий / описание
            'assignedById': assigned_id,  # Отвесвенный ( из маршрутов)
            'ufCrm5Insp': inspector_id,  # инспектор
            # 'ufCrm5PlanDate': str(datetime.datetime.now()),
            # 'createdBy': 3498, # Кем создан (инспектор)
            'stageId': set.ST_SM_PROVERKA}, # ставим статус при создании
    }
    # если  есть фото то в json  добавляются список фоток
    if photo is not None:
        json_reg_save['fields'].update(
            {'ufCrm5PicIncons': ['0', ['photo_1.jpg', str(base64.b64encode(photo).decode())]]})
    return requests.post(set.BASE_URL + set.WH_ADD_SMART, json=json_reg_save)  # , json=json_reg_test


def confirm_coment(id_coment, confirm=True):
    """
    Принять или отклонить замечание указав Id замечания, если отклонить замечание то ввести доп аргумент confirm=False
    :param id_coment:
    :param confirm: по умолчанию True подтверждение / False отклонить
    :return: отправляет  вебхук в битрикс
    """
    json_reg_update = {
        'entityTypeId': set.KEY_SMART,
        'id': id_coment,
        'fields': {
            'stageId': set.ST_SM_SUCCSES if confirm else set.ST_SM_NOVAY},
    }
    return requests.post(set.BASE_URL + set.WH_UPDATE_SMART, json=json_reg_update)  # , json=json_reg_test

##################################
########### ТЕСТЫ ################
##################################

# a = get_val_of_list(set.FIELD_AREA)
# print(a)

# a = get_user(313476377)
# print(a)
#
# area = get_area_or_work(get_user(313476377)) # площадки
# print(area)

# work = get_area_or_work(3498, 'ОФИС')
# print(work)

# id_w = get_id_work(3498,'ОФИС','Тест 1 ')
# print(id_w)

# f = get_comment_photo_url(29)
# print(f)

# areas = update_status_route(18115)
# print(areas)

# otv = get_field_route_by_id(id_w,set.FIELD_RESP_WORK)
# print(otv)


# id_work = get_id_work(3498, 'ОФИС', 'Вертикальная планировка парковки (выемка грунта, обратная отсыпка песком, работы по договору), монтаж наружных сетей')
# print(id_work)
#
# reg = get_reg_list(19076)
# for i in reg:
#
#     print(i)

###### Получить площадки #########
# last_id = '0'
# full_list = []
# while last_id is not None:
#     json_routes_test = {
#         'IBLOCK_TYPE_ID': 'lists', # 'lists_socnet'
#         'IBLOCK_ID': set.KEY_ROUTE,
#         'ELEMENT_ORDER' : {"ID": "ASC"},
#         'FILTER': {
#             '>ID': '0',
#             #'=NAME': 'Изготовление и монтаж Фасада',
#                     }
#         }
#     json_routes_test['FILTER']['>ID'] = last_id
#     r = requests.post(set.BASE_URL + set.WH_ROUTES, json=json_routes_test)  # , json=json_reg_test
#     js_test = r.json() ['result']
#     if js_test:
#         for indx,i in enumerate(js_test):
#             full_list.append(i)
#             last_id = i["ID"]
#     else:
#         last_id = None
#
# for indx, l in enumerate(full_list):
#     print(indx,l)
# print()
######################
#
# json_reg_test = {
#     'entityTypeId': set.KEY_SMART,
#     'fields': {
#         'createdTime': str(datetime.datetime.now()), # дата создания
#         'title': 'из питона', # коментарии
#         'ufCrm5Way': 18117, # код из маршрутов
#         #'ufCrm5PicIncons':'', # фото
#         'ufCrm5TaskDef':'тест 4',
#         'assignedById': 3498, # Отвесвенный ( из маршрутов)
#         #'createdBy': 3498, # Кем создан (инспектор)
#         'ufCrm5Insp': 3498, # инспектор
#         'ufCrm5PlanDate': str(datetime.datetime.now()),
#         'stageId': set.ST_SM_PROVERKA},
# }
# r = requests.post(set.BASE_URL + set.WH_ADD_SMART, json=json_reg_test)  # , json=json_reg_test
# for i in r.json():
#     print(i)


# json_reg_test = {
#     'entityTypeId': set.KEY_SMART,
#     'select': ['*'],
#     'filter': {  # '!=assignedById':'',
#         # '=id':'4',
#         #'ufCrm5Way': 18117,
#     }
# }
#
# r = requests.post(set.BASE_URL + set.WH_REG, json=json_reg_test)  # , json=json_reg_test
# js_test = r.json()['result']['items']
# for i in js_test:
#     print(i)


