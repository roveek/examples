const standartErrorMessage = "Что-то пошло не так. Мы уже занимаемся решением проблемы";
const loginFormTimeout = 1500;

class BackendError extends Error {
  constructor(message) {
    super(message);
    this.name = "BackendError";
  }
}

class BaseRequest {
  standartErrorMessage = standartErrorMessage

  constructor() {
    // Все методы, используемые в .then() метода process()
    // потеряют this. Прицепляем this принудительно:
    this.checkResponse = this.checkResponse.bind(this);
    this.enreachRequestData = this.enreachRequestData.bind(this);
    this.preHandleResponseActions = this.preHandleResponseActions.bind(this);
    this.handleResponse = this.handleResponse.bind(this);
    this.postHandleResponseActions = this.postHandleResponseActions.bind(this);
    this.handleError = this.handleError.bind(this);
    this.finallyDo = this.finallyDo.bind(this);
  }

  get command() {
    throw new Error("Not implemented");
  }

  /**
   * Id тега (без "#"), в который будет записана ошибка
   * @returns {string}
   */
  get errorBlockId() {
    return "";
  }

  process(apiUrl, orderId, supplierId) {
    this.preRequest();
    this.request(apiUrl, orderId, supplierId)
      .then(this.checkResponse)
      .then(json => {
        json = this.preHandleResponseActions(json);
        this.handleResponse(json);
        this.postHandleResponseActions(json);
      })
      .catch(this.handleError)
      .finally(this.finallyDo);
    return this;
  }

  preRequest() {
    if (this.errorBlockId) {
      elements("#" + this.errorBlockId).hide();
    }
  }

  /**
   * Отправляет запрос
   * @param {string} apiUrl
   * @param {string} orderId id заказа
   * @param {string} supplierId id поставщика
   * @returns {Promise<Response>} fetch response object
   */
  request(apiUrl, orderId, supplierId) {
    const url = this.composeCommandUrl(apiUrl, this.command);
    let data = getRequestData(orderId, supplierId);
    data = this.enreachRequestData(data);
    let options = baseFetchOptions(JSON.stringify(data));

    return fetch(url, options);
  }

  /**
   * Дополняет данные API-запроса
   * @param {Object} data
   * @returns {Object} дополненные данные запроса
   */
  enreachRequestData(data) {
    return data;
  }

  /**
   * Проверяет ответ на "успешность"
   * @param {Response} response fetch response object
   * @returns {Promise<Object>} success response json
   */
  async checkResponse(response) {
    if (response.ok) {
      return response.json();
    } else {
      return this.handleErrorResponse(response);
    }
  }

  /**
   * Выбрасывает исключение с текстом ответа-ошибки успешно выполенного запроса
   * @param {Response} response
   * @throws {Error}
   */
  async handleErrorResponse(response) {
    let json;
    try {
      json = await response.json();
    } catch (e) {
      // не json
      throw new Error(this.standartErrorMessage);
    }
    throw new BackendError(json.data["error"]);
  }

  /**
   * Действия ДО обработки ответа API
   * @param {Object} json Данные ответа на API-запрос
   */
  preHandleResponseActions(json) {
    return json;
  }

  /**
   * Обработка ответа API
   * @param {Object} json Данные ответа на API-запрос
   */
  handleResponse(json) {
  }

  /**
   * Действия ПОСЛЕ обработки ответа API
   * @param {Object} json Данные ответа на API-запрос
   */
  postHandleResponseActions(json) {
  }

  /**
   * Выводит текст ошибки, возникшей при запросе
   * @param {Error} error
   */
  handleError(error) {
    if (this.errorBlockId) {
      elements("#" + this.errorBlockId).set(error.message).show();
    }
    console.error(error);
  }

  finallyDo() {
  }

  composeCommandUrl(apiUrl, command = this.command) {
    return `${apiUrl}c/${command}`;
  }
}

class Elements {
  hiddenClass = "hidden";

  /**
   * @param {string} selector
   */
  constructor(selector) {
    this.elements = document.querySelectorAll(selector);
  }

  display(style = "revert") {
    this.elements.forEach(element => element.style.display = style);
    return this;
  }

  hide() {
    this.elements.forEach(element => element.classList.add(this.hiddenClass));
    return this;
  }

  show() {
    this.elements.forEach(element => element.classList.remove(this.hiddenClass));
    return this;
  }

  /**
   * @return {boolean} true, если все элементы скрыты
   */
  isHidden() {
    let hidden = [];
    this.elements.forEach(element => hidden.push(element.classList.contains(this.hiddenClass)));
    return hidden.every(Boolean);
  }

  isShown() {
    return !this.isHidden();
  }

  enable() {
    this.elements.forEach(element => element.disabled = false);
    return this;
  }

  disable() {
    this.elements.forEach(element => element.disabled = true);
    return this;
  }

  clear() {
    this.set("");
    return this;
  }

  set(value) {
    this.elements.forEach(element => element.innerHTML = value);
    return this;
  }
}

class Tag {
  /**
   * @param {string} tagName
   */
  constructor(tagName) {
    this.tag = document.createElement(tagName);
  }

  /**
   * @param {HTMLElement|Tag} tag
   * @return {Tag}
   */
  append(tag) {
    if (tag instanceof Tag) {
      this.tag.appendChild(tag.tag);
    } else {
      this.tag.appendChild(tag);
    }
    return this;
  }

  /**
   * @param {string} innerText
   * @return {Tag}
   */
  text(innerText) {
    this.tag.innerText = innerText;
    return this;
  }

  /**
   * @param {string} id
   * @return {Tag}
   */
  id(id) {
    this.tag.id = id;
    return this;
  }

  /**
   * @param {string} className
   * @return {Tag}
   */
  addClass(className) {
    this.tag.classList.add(className);
    return this;
  }

  /**
   * @param {CallableFunction} func
   * @return {Tag}
   */
  do(func) {
    func(this.tag);
    return this;
  }
}

function inputElement(element) {
  return {
    input: element,
    get id() {
      return this.input.value;
    },
    set id(value) {
      this.input.value = value;
    }
  }
}

function element(tagId) {
  return document.getElementById(tagId);
}

function elements(cssSelector) {
  return new Elements(cssSelector);
}

/**
 * Возвращает заготовку отправляемых данных для АПИ-запроса
 * @param {string} orderId
 * @param {string} supplierId
 */
function getRequestData(orderId, supplierId) {
  return {
    order_id: orderId,
    supplier_id: supplierId
  }
}

/**
 * Возвращает параметры АПИ-запроса
 *
 * https://developer.mozilla.org/en-US/docs/Web/API/fetch#parameters
 *
 * @param {Object} body
 */
function baseFetchOptions(body) {
  return {
    method: "POST",
    headers: {
      "Content-Type": "application/json;charset=utf-8"
    },
    body: body
  }
}

/**
 * Преобразовывает дату
 * @param {string} strDate строка с датой ГГГГ-ММ-ДД
 */
function formatDate(strDate) {
  const date = new Date(strDate);
  const formattedDate = date.toLocaleDateString('ru-RU', { weekday:"long", month:"short", day:"numeric"});
  return formattedDate.charAt(0).toUpperCase() + formattedDate.slice(1);
}

function shake(tag) {
  tag.classList.add("shake");
  window.setTimeout(function () {
    tag.classList.remove("shake");
  }, 1000);
  return false;
}
