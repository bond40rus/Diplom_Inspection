inspection_tokken = '**************'

TG_NAME = {
    437924343: ['Суров Михаил Владимирович', 8631],
    31347630878: ['Бондаренко Сергей Сергеевич', 3498],

    }

BASE_URL = '***********'  # токен на webhook bitrix
WH_ROUTES = 'lists.element.get'  #
WH_ROUTES_UPDATE = 'lists.element.update'
WH_USER = "user.get.json?ID="
WH_REG = 'crm.item.list.json?'
WH_ADD_SMART = 'crm.item.add.json?'
WH_UPDATE_SMART = 'crm.item.update.json'
WH_FIELDS = 'lists.field.get'

FIELD_STATUS = 'PROPERTY_250'  # поле со списком статусов маршрутов
FIELD_AREA = 'PROPERTY_288'  # поле со списком площадок
FIELD_INSPEC = 'PROPERTY_253'  # поле инспектора
FIELD_RESP_WORK = 'PROPERTY_252'  # поле ответсвеного за работу

KEY_ROUTE = '45'  # id листа
KEY_SMART = '138'  # id  смарт процесса

ST_R_ACTIVE = 1375  # статус маршрута Активный
ST_R_CLOSED = 1376  # статус маршрута на закрытие
ST_R_CLOSE = 1377  # статус маршрута Закрытый

ST_SM_PROVERKA = 'DT138_8:NEW'  # статус в смарт процессе на проверке главного инспектора
ST_SM_NOVAY = 'DT138_8:PREPARATION'  # статус в смарт новое замечание после согласование гл. инспектора
ST_SM_INWORK = 'DT138_8:CLIENT'  # статус в смарт процессе в работе
ST_SM_INCONFIRM = 'DT138_8:UC_49UOBF'  # статус в смарт процессе на подтверждении
ST_SM_SUCCSES = 'DT138_8:SUCCESS'  # статус в смарт процессе подтверждена
ST_SM_FAIL = 'DT138_8:UC_FAIL'  # статус в смарт процессе не подтверждена

IN_LINE_KEY_HIDE = 'Скрыть'