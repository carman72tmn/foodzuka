

Вот рекомендации по API (Server iiko api Resto)
проведи анализ появления дапнных ошибок,  опиши причины и способы испраления ошибок в системе сайта , сайт на удаленном VPS cервере по ssh foodtech . Просто произведи подробную испекцию возникновения ошибок, дай точные и правильные рекомендации по устранения, либо варианты исправления, либо если не уверен в каких то переменных и коммандах обязательно пометь эти места, чтобы я мог сверить правильность с официальной документацией сам! Произведи только анализ и дай полную рекомендацию с подробным описанием и вариантами а так  же пометками если не уверен в правильности! Ничего сам не исправляй! Все строго на русском языке! Вот логи ошбиок которые нужно исправить! 20.04.2026, 13:22:08	

* [Список активных](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2__2109393174)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_1387997121)
* [Список по подразделению](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2__1547518874)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_1553313209)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_105637038)
* [Сотрудник по ID](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2__2094082183)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_2138875455)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__984807956)
* [Сотрудник по коду](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2__243212989)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_226895131)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__1886227089)
* [Поиск сотрудника](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2_623154327)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_1270857196)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__1577761397)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__237152841)
* [Добавить или заменить сотрудника (по Id)](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2_653670241)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_945285395)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_687002477)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__820067579)
* [Добавить сотрудника (по коду)](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2__1324771003)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3__436508111)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_384736109)
* [Изменить/добавить сотрудника (по id)](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2_439774833)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_179396395)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_1880996741)
* [Удалить сотрудника](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h2_1893260727)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_600101026)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/h3_1310189372)
* [Описание сущностей для представления в формате XML (XSD-схема)](/articles/api-documentations/rabota-s-dannymi-sotrudnikovv/a/v1.APIсотрудников-ОписаниясущностейдляпредставлениявформатеXML%28XSD-схема%29)

## Список активных

Версия API: 1.0

Версия iiko: 4.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees |
| --- | --- |

### Параметры запроса

### 

####  

| **Название** | **Значение** | **Версия** | **Описание** |
| --- | --- | --- | --- |
| includeDeleted | true/false | с 5.0 | Возвращать и действующих, и удаленных сотрудников |
| revisionFrom | число, номер ревизии | с 6.4 | Номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br> <br>По умолчанию (неревизионный запрос) revisionFrom = -1 |

### Что в ответе
Список сотрудников.  Все сотрудники (включая встроенные системные аккаунты), которые активны (не удалены)

###  **Пример запроса**

https://localhost:8080/resto/api/employees?key=284c5690-2b56-b1d6-0c81-e94b5034243d

## Список по подразделению

Версия API: 1.0

Версия iiko: 4.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **** https://host:port/resto/api/employees/byDepartment/{departmentCode} |
| --- | --- |

### Параметры запроса

| **Параметр** | **Описание** |
| --- | --- |
| **includeDeleted** (с 5.0) | Возвращать и действующих, и удаленных сотрудников |

### Что в ответе
 
Список сотрудников указанного подразделения.  Все сотрудники (включая встроенные системные аккаунты), которые активны (не удалены).
 
Для RMS идентично обычному списку, для Chain - только список сотрудников указанного подразделения.
 
**Пример запроса**

https://localhost:8080/resto/api/employees/byDepartment/1?key=284c5690-2b56-b1d6-0c81-e94b5034243d

## Сотрудник по ID

Версия API: 1.0

Версия iiko: 4.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **** https://host:port/resto/api/employees/byId/{employeeUUID} |
| --- | --- |

### 

### Что в ответе

Сотрудник с указанным GUID.

### Пример запроса

https://localhost:8080/resto/api/employees/byId/61b97cfb-6b4e-4668-9a38-c30190f7a109?key=180c8a55-efae-8183-0d6d-015a685f84f1

###  

## Сотрудник по коду

Версия API: 1.0

Версия iiko: 4.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/api/employees/byCode/{employeeCode}** |
| --- | --- |

### Что в ответе

Сотрудник с указанным кодом.

###  **Пример запроса**

https://localhost:8080/resto/api/employees/byCode/2?key=a10b7fdc-9ae5-449f-c6fb-cb5a67e5b2e6

## Поиск сотрудника

Версия API: 1.0

Версия iiko: 4.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**employees/search?firstName={regexp}&middleName={regexp}** |
| --- | --- |

### Параметры запроса
| **Параметры** | **Описание** |
| --- | --- |
| address <br> cardNumber <br> cellPhone <br> client <br> code <br> email <br> employee <br> firstName <br> lastName <br> login <br> mainRoleCode <br> middleName <br> name <br> note <br> phone <br> supplier | Регулярное выражение<br> <br>По любому из текстовых или булевых полей в dto (см. список в 1 столбце)<br> <br>Параметры необязательные. Если отсутствуют, вернет всех активных |
| **includeDeleted** (с 5.0) | Возвращать и действующих, и удаленных сотрудников |

### Что в ответе

Сотрудник с указанными именем и/или отчеством.

###  **Пример запроса**

https://localhost:8080/resto/api/employees/search?key=de7c43fc-b4d7-cf45-51b4-c40cba21265f&firstName=n&middleName=m

## Добавить или заменить сотрудника (по Id)
Версия API: 1.0

Версия iiko: 4.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/api****/employees/byId/{UUID}** |
| --- | --- |

### Параметры запроса

### Что в ответе
 
Если передан новый id, то будет создан новый сотрудник (код возврата 201 Created).
 
Если передан id существующего сотрудника, то произойдет полное замещение всех полей сотрудника (код возврата 200 OK). При этом если не указать какое-либо из необязательных полей, то значение этого поля сбросится.
 
Для обновления частичного набора полей используйте метод POST **/employees/byId/{employeeUUID}**

###  **Пример запроса**

https://localhost:8080/resto/api/employees/byId/4f390698-241d-6ab9-015e-a3d90baa0370


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<employee>
    <code>6</code>
    <name>АPIbyId</name>
    <login/>
    <mainRoleCode>CS1</mainRoleCode>
    <roleCodes>CS1</roleCodes>
    <phone>7979</phone>
    <cellPhone>00000</cellPhone>
    <firstName>Name</firstName>
    <lastName>Name</lastName>
    <birthday>2017-09-14T00:00:00+03:00</birthday>
    <email>email2@mail.ru</email>
    <address>address</address>
    <hireDate>2017-09-04T00:00:00+03:00</hireDate>
    <fireDate>2017-09-21T00:00:00+03:00</fireDate>
    <cardNumber/>
    <taxpayerIdNumber>111111111111111111</taxpayerIdNumber>
    <snils>455555555555555555</snils>
    <preferredDepartmentCode>1</preferredDepartmentCode>
    <departmentCodes>1</departmentCodes>
    <responsibilityDepartmentCodes>1</responsibilityDepartmentCodes>
    <deleted>false</deleted>
    <supplier>false</supplier>
    <employee>true</employee>
    <client>false</client>
    <publicExternalData>
        <entry>
            <key>keyPUT</key>
            <value>valuePUT</value>
        </entry>
    </publicExternalData>
</employee>
```


**Пример результата вызова API**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<employee>
    <id>4f390698-241d-6ab9-015e-a3d90baa0370</id>
    <code>6</code>
    <name>АPIbyId</name>
    <login/>
    <mainRoleCode>CS1</mainRoleCode>
    <roleCodes>CS1</roleCodes>
    <phone>7979</phone>
    <cellPhone>00000</cellPhone>
    <firstName>Name</firstName>
    <lastName>Name</lastName>
    <birthday>2017-09-14T00:00:00+03:00</birthday>
    <email>email2@mail.ru</email>
    <address>address</address>
    <hireDate>2017-09-04T00:00:00+03:00</hireDate>
    <fireDate>2017-09-21T00:00:00+03:00</fireDate>
    <cardNumber/>
    <taxpayerIdNumber>111111111111111111</taxpayerIdNumber>
    <snils>455555555555555555</snils>
    <preferredDepartmentCode>1</preferredDepartmentCode>
    <departmentCodes>1</departmentCodes>
    <responsibilityDepartmentCodes>1</responsibilityDepartmentCodes>
    <deleted>false</deleted>
    <supplier>false</supplier>
    <employee>true</employee>
    <client>false</client>
    <publicExternalData>
        <entry>
            <key>keyPUT</key>
            <value>valuePUT</value>
        </entry>
    </publicExternalData>
</employee>
```


## Добавить сотрудника (по коду)

| ![PUT Request](/resources/Storage/api-documentations/http_request_put.png) | **https://host:port/resto/api/** **employees/byCode/{employeeCode}** |
| --- | --- |

###  Что в ответе

Новый сотрудник (код возврата 201 Created).

учитывается только код, переданный в теле PUT-запроса.

###   **Пример запроса** 
https://localhost:8080/resto/api/employees/byCode/5

employeeCode - введенное значение будет отображаться в поле Табельный номер
 
**Пример результата вызова API**
 

Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<employee>
    <id>4f390698-241d-6ab9-015e-a3d90baa0371</id>
    <code>5</code>
    <name>АPI</name> //имя в системе
    <login/>
    <mainRoleCode>CS1</mainRoleCode>
    <roleCodes>CS1</roleCodes>
    <phone>78787878</phone>
    <cellPhone>56565</cellPhone>
    <firstName>firstName</firstName>
    <lastName>lastName</lastName>
    <birthday>2017-09-14T00:00:00+03:00</birthday>
    <email>email@mail.ru</email>
    <address>address</address>
    <hireDate>2017-09-04T00:00:00+03:00</hireDate>
    <fireDate>2017-09-21T00:00:00+03:00</fireDate>
    <cardNumber/>
    <taxpayerIdNumber>111111111111111111</taxpayerIdNumber>
    <snils>455555555555555555</snils>
    <preferredDepartmentCode>1</preferredDepartmentCode>
    <departmentCodes>1</departmentCodes>
    <responsibilityDepartmentCodes>1</responsibilityDepartmentCodes>
    <deleted>false</deleted>
    <supplier>false</supplier>
    <employee>true</employee>
    <client>false</client>
</employee>
```


## Изменить/добавить сотрудника (по id)

Версия API: 1.0

Версия iiko: 4.0

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/employees/byId/{employeeUUID} |
| --- | --- |

### Что в ответе
 
Если передан новый id, то будет создан новый сотрудник (код возврата 201 Created).
 
Если передан id существующего сотрудника, то произойдет изменение указанных полей (код возврата 200 OK). Поля не указанные в запросе останутся без изменений.
 
Для полного замещения всех полей используйте метод PUT **/employees/byId/{employeeUUID}.**
 
Список пар ключ-значение в поле publicExternalData задается через XML следующим образом:
 
&lt;r&gt;&lt;entry&gt;&lt;key&gt;key\_POST1&lt;/key&gt;&lt;value&gt;value\_POST1&lt;/value&gt;&lt;/entry&gt;&lt;entry&gt;&lt;key&gt;key\_POST2&lt;/key&gt;&lt;value&gt;value\_POST2&lt;/value&gt;&lt;/entry&gt;&lt;/r&gt;.
 
Корневой тег может быть любым, можно задавать &lt;r&gt; для краткости, главное чтобы содержимое соответствовало указанному формату. Сервер "знает", что нужно распарсить это поле в виде XML и положить в виде списка пар ключ-значение в справочник User.
 
Внутри &lt;entry&gt; ключ &lt;key&gt; задавать обязательно, т.е. ключ не может быть null, а вот значение &lt;value&gt; можно не задавать, поскольку оно может быть null, см. employee.xsd ниже.
 ###   **Пример запроса** 
**** https://localhost:8080/resto/api/employees/byId/4f390698-241d-6ab9-015e-a3d90baa0370
 

Код

```
<!--Content-Type: application/x-www-form-urlencoded-->
code=10&name=name&taxpayerIdNumber=000000000000&externalData=<r><entry><key>key_POST1</key><value>value_POST1</value></entry><entry><key>key_POST2</key><value>value_POST2</value></entry></r>
```

 
**Пример результата вызова API**
 

Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<employee>
    <id>4f390698-241d-6ab9-015e-a3d90baa0370</id>
    <code>10</code>
    <name>name</name>
    <login/>
    <mainRoleCode>CS1</mainRoleCode>
    <roleCodes>CS1</roleCodes>
    <phone>7979</phone>
    <cellPhone>00000</cellPhone>
    <firstName>Name</firstName>
    <lastName>Name</lastName>
    <birthday>2017-09-14T00:00:00+03:00</birthday>
    <email>email2@mail.ru</email>
    <address>address</address>
    <hireDate>2017-09-04T00:00:00+03:00</hireDate>
    <fireDate>2017-09-21T00:00:00+03:00</fireDate>
    <cardNumber/>
    <taxpayerIdNumber>000000000000</taxpayerIdNumber>
    <snils>455555555555555555</snils>
    <preferredDepartmentCode>1</preferredDepartmentCode>
    <departmentCodes>1</departmentCodes>
    <responsibilityDepartmentCodes>1</responsibilityDepartmentCodes>
    <deleted>false</deleted>
    <supplier>false</supplier>
    <employee>true</employee>
    <client>false</client>
    <publicExternalData>
        <entry>
            <key>key_POST1</key>
            <value>value_POST1</value>
        </entry>
        <entry>
            <key>key_POST2</key>
            <value>value_POST2</value>
        </entry>
    </publicExternalData>
</employee>
```


## Удалить сотрудника

Версия API: 1.0

Версия iiko: 4.0

| ![DELETE Request](/resources/Storage/api-documentations/http_request_delete.png) | https://host:port/resto/api/employees/byId/{employeeUUID} |
| --- | --- |

### Что в ответе
 
Пустой ответ если сотрудник удален (или уже был удален).
 
Entity of class User not found by id (employeeUUID), если передан несуществующий guid.
 
### **Пример запроса**

https://localhost:8080/resto/api/employees/byId/4f390698-241d-6ab9-015e-a3d90baa0370

## Описание сущностей для представления в формате XML (XSD-схема)
[+] [Сотрудник](javascript:void%280%29)
 [-] [Сотрудник](javascript:void%280%29)
 
```
 %%CH%PRE5%%
```


* [Список должностей](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h2_334405970)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h3_1387997121)
* [Описание сущностей для представления в формате XML (XSD-схема)](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/v1.APIсотрудников-ОписаниясущностейдляпредставлениявформатеXML%28XSD-схема%29)

## Список должностей

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/roles |
| --- | --- |

### 

### Параметры запроса
| **Название** | **Параметр** | **Версия** | **Описание** |
| --- | --- | --- | --- |
| revisionFrom | число, номер ревизии | с 6.4 | Номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |
### Что в ответе

Список должностей (см. описание XSD).

### **Пример запроса**

https://localhost:8080/resto/api/employees/roles

**Результат:**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<employeeRoles>
  <role>
    <id>d9753f67-6e87-4564-9b74-4018c37306d7</id>
    <code>BAR1</code>
    <name>Barista</name>
    <paymentPerHour>2.500000000</paymentPerHour>
    <steadySalary>1860.000000000</steadySalary>
    <scheduleType>SESSION</scheduleType>
    <deleted>false</deleted>
  </role>
  <role>
    <id>01a014eb-6609-c206-dbed-3102179f80be</id>
    <code>SMB</code>
    <name>Somebody</name>
    <paymentPerHour>2.000000000</paymentPerHour>
    <steadySalary>340.000000000</steadySalary>
    <scheduleType>HOURS</scheduleType>
    <deleted>false</deleted>
  </role>
</employeeRoles>
```


## Описание сущностей для представления в формате XML (XSD-схема)
[+] [Должность](javascript:void%280%29)
 [-] [Должность](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```



* [Список должностей](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h2_334405970)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/h3_1387997121)
* [Описание сущностей для представления в формате XML (XSD-схема)](/articles/api-documentations/rabota-s-dannymi-dolzhnostey/a/v1.APIсотрудников-ОписаниясущностейдляпредставлениявформатеXML%28XSD-схема%29)

## Список должностей

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/roles |
| --- | --- |

### 

### Параметры запроса
| **Название** | **Параметр** | **Версия** | **Описание** |
| --- | --- | --- | --- |
| revisionFrom | число, номер ревизии | с 6.4 | Номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |
### Что в ответе

Список должностей (см. описание XSD).

### **Пример запроса**

https://localhost:8080/resto/api/employees/roles

**Результат:**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<employeeRoles>
  <role>
    <id>d9753f67-6e87-4564-9b74-4018c37306d7</id>
    <code>BAR1</code>
    <name>Barista</name>
    <paymentPerHour>2.500000000</paymentPerHour>
    <steadySalary>1860.000000000</steadySalary>
    <scheduleType>SESSION</scheduleType>
    <deleted>false</deleted>
  </role>
  <role>
    <id>01a014eb-6609-c206-dbed-3102179f80be</id>
    <code>SMB</code>
    <name>Somebody</name>
    <paymentPerHour>2.000000000</paymentPerHour>
    <steadySalary>340.000000000</steadySalary>
    <scheduleType>HOURS</scheduleType>
    <deleted>false</deleted>
  </role>
</employeeRoles>
```


## Описание сущностей для представления в формате XML (XSD-схема)
[+] [Должность](javascript:void%280%29)
 [-] [Должность](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```

* [Получение типов явок](/articles/api-documentations/rabota-s-dannymi-yavok/a/h2_1174254487)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_1387997121)
* [Получение явок](/articles/api-documentations/rabota-s-dannymi-yavok/a/h2_375860816)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_199559134)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_765642244)
* [Создание или обновление явки](/articles/api-documentations/rabota-s-dannymi-yavok/a/h2__667173474)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_1461044143)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3__1042337956)
* [Удаление явки](/articles/api-documentations/rabota-s-dannymi-yavok/a/h2_753455492)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_1967588710)
* [Пример вызова](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3__232688264)
* [Доступность сотрудников](/articles/api-documentations/rabota-s-dannymi-yavok/a/v1.APIсотрудников-Доступностьсотрудников)
* [Получить доступность сотрудников](/articles/api-documentations/rabota-s-dannymi-yavok/a/h2__983155982)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3_1914196038)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3__1125635261)
* [Пример вызова](/articles/api-documentations/rabota-s-dannymi-yavok/a/h3__343110906)
* [Описание сущностей для представления в формате XML (XSD-схема)](/articles/api-documentations/rabota-s-dannymi-yavok/a/v1.APIсотрудников-ОписаниясущностейдляпредставлениявформатеXML%28XSD-схема%29)

## Получение типов явок

Версия API: 1.0

Версия iiko: 2.5

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance/types |
| --- | --- |

### Параметры запроса
| **Название** | **Значение** | **Версия** | **Описание** |
| --- | --- | --- | --- |
| includeDeleted | true\false |  | Включать ли удаленные элементы в результат. По умолчанию false. |
| revisionFrom | число, номер ревизии | с 6.4 | Номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |
### **Что в ответе**

Возвращаются все не удаленные типы явок.

### **Пример запроса**

https://localhost:8080/resto/api/employees/attendance/types

## Получение явок

Версия API: 1.0

Версия iiko: 2.5

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance/byDepartment/{departmentCode}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance/byDepartment/{departmentCode}/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance/department/{departmentId}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/attendance/department/{departmentId}/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

### **Параметры запроса**

| Параметр | Описание |
| --- | --- |
| from | дата начала отчета в формате YYYY-MM-DD |
| to | дата окончания отчета (включающая) в формате YYYY-MM-DD |
| employeeUUID | ID сотрудника |
| departmentCode | код подразделения (тот, который используется при регистрации iikoRMS в iikoChain) |
| departmentId | UUID идентификатор подразделения |
| withPaymentDetails | *(начиная с 5.0)* если true, ко сменам добавляется информация об отработанном времени и начисленной по явкам заработной плате.<br>У сотрудников, работающих по расписанию или на окладе, paymentDetails явки будет пуст. |
| revisionFrom | номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |

### **Что в ответе**

Возвращаются все явки, **пересекающие** интервал отчета.

При этом, в отличие от других методов API, здесь дата окончания выборки включающая: `&to=2016-03-21 `вернет явки, пересекающие 2016-03-22 00:00:00.

### **Пример запроса**

https://localhost:8080/resto/api/employees/attendance?from=2017-08-01&to=2017-10-09&withPaymentDetails=true

**Пример результата вызова API**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<attendances>
    <attendance>
        <id>faa6d21e-7193-4c1f-885c-6049ddddd0ce</id>
        <employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
        <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
        <dateFrom>2017-09-21T10:27:00+03:00</dateFrom>
        <attendanceType>W</attendanceType>
        <comment/>
        <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
        <departmentName>ТП1</departmentName>
        <paymentDetails>
            <regularPayedMinutes>0</regularPayedMinutes>
            <regularPaymentSum>0</regularPaymentSum>
            <overtimePayedMinutes>0</overtimePayedMinutes>
            <overtimePayedSum>0</overtimePayedSum>
            <otherPaymentsSum>0</otherPaymentsSum>
        </paymentDetails>
        <personalDateFrom>2017-09-21T10:27:00+03:00</personalDateFrom>
        <created>2017-09-21T10:27:53.987+03:00</created>
    </attendance>
    <attendance>
        <id>72582fa9-172b-4956-9b66-c3b40efff751</id>
        <employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
        <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
        <dateFrom>2017-09-21T09:02:00+03:00</dateFrom>
        <dateTo>2017-09-21T14:02:00+03:00</dateTo>
        <attendanceType>W</attendanceType>
        <comment/>
        <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
        <departmentName>ТП1</departmentName>
        <paymentDetails>
            <regularPayedMinutes>300</regularPayedMinutes>
            <regularPaymentSum>50.000000000</regularPaymentSum>
            <overtimePayedMinutes>0</overtimePayedMinutes>
            <overtimePayedSum>0</overtimePayedSum>
            <otherPaymentsSum>0</otherPaymentsSum>
        </paymentDetails>
        <personalDateFrom>2017-09-21T09:02:00+03:00</personalDateFrom>
        <created>2017-09-21T09:02:40.343+03:00</created>
        <modified>2017-09-21T10:17:06.620+03:00</modified>
        <userModified>c831367e-778f-e80f-18f7-bd0843cd10c6</userModified>
    </attendance>
</attendances>
```


## Создание или обновление явки

Версия API: 1.0

Версия iiko: 2.5

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | **https://host:port/resto/api/employees/attendance/create** |
| --- | --- |

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | **https://host:port/resto/api/employees/attendance/update** |
| --- | --- |

Структура **attendance:** при создании поле id может быть не заполнено. Даты округляются с точностью до минуты. Запрещается создание пересекающихся явок.

### Что в ответе

Структура **attendance** после сохранения, с округленными датами, сгенерированным id.

**Внимание!** При обновлении (update) явки ее id может измениться.

### **Пример запроса**
https://localhost:8080/resto/api/employees/attendance/create

**Пример результата вызова API**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<attendance>
    <id>d9d8aa67-9e10-97ee-015e-f1879f9c5e87</id>
    <employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
    <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
    <dateFrom>2017-10-08T10:00:00+03:00</dateFrom>
    <dateTo>2017-10-08T18:00:00+03:00</dateTo>
    <attendanceType>W</attendanceType>
    <comment/>
    <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
    <departmentName>ТП1</departmentName>
    <personalDateFrom>2017-10-08T18:00:00+03:00</personalDateFrom>
    <created>2017-10-09T09:26:22.731+03:00</created>
    <modified>2017-10-09T09:26:22.731+03:00</modified>
    <userModified>c831367e-778f-e80f-18f7-bd0843cd10c6</userModified>
</attendance>
```


## Удаление явки

Версия API: 1.0

Версия iiko: 5.0

| ![DELETE Request](/resources/Storage/api-documentations/http_request_delete.png) | https://host:port/resto/api/employees/attendance/byId/{attendanceUUID} |
| --- | --- |

### Что в ответе

Удаленная явка **attendance**.

### **Пример вызова**

https://localhost:8080/resto/api/employees/attendance/byId/d9d8aa67-9e10-97ee-015e-f1879f9c5e87

## Доступность сотрудников

## Получить доступность сотрудников

Версия API: 1.0

Версия iiko: 5.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/availability/list?from={YYYY-MM-DD}&to={YYYY-MM-DD}&department={departmentUUID}&role={roleUUID}&user={userUUID} |
| --- | --- |

### **Параметры запроса**

| **Параметр** | **Описание** |
| --- | --- |
| from | Дата начала отчета (включающая). |
| to | Дата окончания отчета (исключающая).<br><br>**Внимание!** Отрезки доступности будут сформированы по расписаниям на весь запрошенный интервал, то есть, следует использовать минимально необходимую дату (неделя/месяц вперед). |
| department | Id подразделения сотрудника для фильтрации. Можно задать параметр несколько раз. Если не задан ни один, отображаются данные по сотрудникам всех подразделений. |
| role | Id должности сотрудника для фильтрации. Можно задать параметр несколько раз. Если не задан ни один, отображаются данные по сотрудникам всех должностей. |
| user | Id сотрудника для фильтрации. Можно задать параметр несколько раз. Если не задан, отображаются данные по всем сотрудникам. |

### Что в ответе

Список отрезков доступности **availability**.

### **Пример вызова**

https://localhost:8080/resto/api/employees/availability/list?from=2017-09-01&to=2017-10-09&department=2b602c10-2045-4f52-b5f9-d00be812d6aa&role=6e3fa11d-3617-c735-bd29-aeac662741ed&user=0a508f8c-4cdb-4126-bd0d-243c4718c22f

**Пример результата вызова API**


Код

```
 <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<availabilities>
    <availability>
        <employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
        <dateFrom>2017-09-01T00:00:00+03:00</dateFrom>
        <dateTo>2017-10-09T00:00:00+03:00</dateTo>
    </availability>
</availabilities>
```


## Описание сущностей для представления в формате XML (XSD-схема)
 [+] [Явки](javascript:void%280%29)
 [-] [Явки](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

 [+] [Тип явки](javascript:void%280%29)
 [-] [Тип явки](javascript:void%280%29)
 
```
 %%CH%PRE4%%
```


* [Получение типов смен](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_1490336783)
* [Получение смен](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_611132094)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3_1387997121)
* [Создание или обновление смены](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_588945765)
* [Тело запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3__1158465537)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3__2104128272)
* [Удаление смены](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_1431404139)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3_1338030860)
* [Описание сущностей для представления в формате XML (XSD-схема)](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/v1.APIсотрудников-ОписаниясущностейдляпредставлениявформатеXML%28XSD-схема%29)

## Получение типов смен

Версия API: 1.0

Версия iiko: 2.5

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/api/employees/schedule/types** |
| --- | --- |

**Что в ответе**

Возвращаются все не удаленные типы смен.

includeDeleted — не реализовано.

**Пример запроса**

https://localhost:8080/resto/api/employees/schedule/types

## Получение смен

Версия API: 1.0

Версия iiko: 2.5

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/byDepartment/{departmentCode}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/byDepartment/{departmentCode}/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/department/{departmentId}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/department/{departmentId}/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

### **Параметры запроса**

| Параметр | Описание |
| --- | --- |
| from | дата начала отчета в формате YYYY-MM-DD |
| to | дата окончания отчета (включающая) в формате YYYY-MM-DD |
| employeeUUID | ID сотрудника |
| departmentCode | код подразделения (тот, который используется при регистрации iikoRMS в iikoChain) |
| departmentId | UUID идентификатор подразделения |
| withPaymentDetails | *(начиная с 5.0)* если true, ко сменам добавляется информация об отработанном времени и начисленной по явкам заработной плате. |
| revisionFrom | номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |

У сотрудников, работающих по свободному графику, смен может не быть; если есть, то paymentDetails у них будет пуст. Если у сотрудника, есть незакрытые явки, начавшиеся раньше, при значении true будет ошибка.

### **Что в ответе**

Возвращаются все смены, **пересекающие** интервал отчета.

При этом, в отличие от других методов API, здесь дата окончания выборки включающая: `&to=2016-03-21` вернет явки, пересекающие 2016-03-22 00:00:00.

### **Пример запроса**

https://localhost:8080/resto/api/employees/schedule/?from=2017-03-21&to=2017-03-22&withPaymentDetails=true

## Создание или обновление смены

Версия API: 1.0

Версия iiko: 5.0

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/employees/schedule/create |
| --- | --- |

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/employees/schedule/update |
| --- | --- |
### Тело запроса

| Переменная | Описание |
| --- | --- |
| employeeId | id сотрудника |
| roleId | id роли сотрудника |
| dateFrom | время начала смены |
| dateTo | время окончания смены |
| scheduleTypeCode | код типа смены |
| nonPaidMinutesdepartmentId | неоплачиваемые минуты |
| departmentId | id подразделения |
| departmentName | наименование подразделения |

### **Что в ответе**
Структура **schedule**. При создании поле id может быть не заполнено. Даты округляются с точностью до минуты.

Структура **schedule** после сохранения, с округленными датами, сгенерированным новым id.

Внимание! При обновлении (update) смены ее id может измениться.

### **Пример запроса**
https://localhost:8080/resto/api/employees/schedule/create


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<schedule>
<employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
    <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
    <dateFrom>2017-10-06T16:00:00+03:00</dateFrom>
    <dateTo>2017-10-06T22:00:00+03:00</dateTo>
    <scheduleTypeCode>DSH</scheduleTypeCode>
    <nonPaidMinutes>0</nonPaidMinutes>
    <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
    <departmentName>ТП1</departmentName>
</schedule>
```


**Пример результата вызова API**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<schedule>
    <id>d9d8aa67-9e10-97ee-015e-f1879f9c0589</id>
    <employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
    <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
    <dateFrom>2017-10-06T16:00:00+03:00</dateFrom>
    <dateTo>2017-10-06T22:00:00+03:00</dateTo>
    <scheduleTypeCode>DSH</scheduleTypeCode>
    <nonPaidMinutes>0</nonPaidMinutes>
    <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
    <departmentName>ТП1</departmentName>
</schedule>
```


## Удаление смены

Версия API: 1.0

Версия iiko: 5.0

| ![DELETE Request](/resources/Storage/api-documentations/http_request_delete.png) | https://host:port/resto/api/employees/schedule/byId/{scheduleUUID} |
| --- | --- |

### Что в ответе

Удаленная смена **schedule**.

## Описание сущностей для представления в формате XML (XSD-схема)

[+] [Тип смены](javascript:void%280%29)
 [-] [Тип смены](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```


[+] [Смена в расписании](javascript:void%280%29)
 [-] [Смена в расписании](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

* [Получение типов смен](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_1490336783)
* [Получение смен](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_611132094)
* [Параметры запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3_1387997121)
* [Создание или обновление смены](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_588945765)
* [Тело запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3__1158465537)
* [Пример запроса](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3__2104128272)
* [Удаление смены](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h2_1431404139)
* [Что в ответе](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/h3_1338030860)
* [Описание сущностей для представления в формате XML (XSD-схема)](/articles/api-documentations/rabota-s-dannymi-smeny-i-raspisaniy/a/v1.APIсотрудников-ОписаниясущностейдляпредставлениявформатеXML%28XSD-схема%29)

## Получение типов смен

Версия API: 1.0

Версия iiko: 2.5

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/api/employees/schedule/types** |
| --- | --- |

**Что в ответе**

Возвращаются все не удаленные типы смен.

includeDeleted — не реализовано.

**Пример запроса**

https://localhost:8080/resto/api/employees/schedule/types

## Получение смен

Версия API: 1.0

Версия iiko: 2.5

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/byDepartment/{departmentCode}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/byDepartment/{departmentCode}/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/department/{departmentId}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/employees/schedule/department/{departmentId}/byEmployee/{employeeUUID}/?from={YYYY-MM-DD}&to={YYYY-MM-DD}&withPaymentDetails={true/false}&revisionFrom=-1 |
| --- | --- |

### **Параметры запроса**

| Параметр | Описание |
| --- | --- |
| from | дата начала отчета в формате YYYY-MM-DD |
| to | дата окончания отчета (включающая) в формате YYYY-MM-DD |
| employeeUUID | ID сотрудника |
| departmentCode | код подразделения (тот, который используется при регистрации iikoRMS в iikoChain) |
| departmentId | UUID идентификатор подразделения |
| withPaymentDetails | *(начиная с 5.0)* если true, ко сменам добавляется информация об отработанном времени и начисленной по явкам заработной плате. |
| revisionFrom | номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |

У сотрудников, работающих по свободному графику, смен может не быть; если есть, то paymentDetails у них будет пуст. Если у сотрудника, есть незакрытые явки, начавшиеся раньше, при значении true будет ошибка.

### **Что в ответе**

Возвращаются все смены, **пересекающие** интервал отчета.

При этом, в отличие от других методов API, здесь дата окончания выборки включающая: `&to=2016-03-21` вернет явки, пересекающие 2016-03-22 00:00:00.

### **Пример запроса**

https://localhost:8080/resto/api/employees/schedule/?from=2017-03-21&to=2017-03-22&withPaymentDetails=true

## Создание или обновление смены

Версия API: 1.0

Версия iiko: 5.0

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/employees/schedule/create |
| --- | --- |

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/employees/schedule/update |
| --- | --- |
### Тело запроса

| Переменная | Описание |
| --- | --- |
| employeeId | id сотрудника |
| roleId | id роли сотрудника |
| dateFrom | время начала смены |
| dateTo | время окончания смены |
| scheduleTypeCode | код типа смены |
| nonPaidMinutesdepartmentId | неоплачиваемые минуты |
| departmentId | id подразделения |
| departmentName | наименование подразделения |

### **Что в ответе**
Структура **schedule**. При создании поле id может быть не заполнено. Даты округляются с точностью до минуты.

Структура **schedule** после сохранения, с округленными датами, сгенерированным новым id.

Внимание! При обновлении (update) смены ее id может измениться.

### **Пример запроса**
https://localhost:8080/resto/api/employees/schedule/create


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<schedule>
<employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
    <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
    <dateFrom>2017-10-06T16:00:00+03:00</dateFrom>
    <dateTo>2017-10-06T22:00:00+03:00</dateTo>
    <scheduleTypeCode>DSH</scheduleTypeCode>
    <nonPaidMinutes>0</nonPaidMinutes>
    <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
    <departmentName>ТП1</departmentName>
</schedule>
```


**Пример результата вызова API**


Код

```
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<schedule>
    <id>d9d8aa67-9e10-97ee-015e-f1879f9c0589</id>
    <employeeId>0a508f8c-4cdb-4126-bd0d-243c4718c22f</employeeId>
    <roleId>6e3fa11d-3617-c735-bd29-aeac662741ed</roleId>
    <dateFrom>2017-10-06T16:00:00+03:00</dateFrom>
    <dateTo>2017-10-06T22:00:00+03:00</dateTo>
    <scheduleTypeCode>DSH</scheduleTypeCode>
    <nonPaidMinutes>0</nonPaidMinutes>
    <departmentId>2b602c10-2045-4f52-b5f9-d00be812d6aa</departmentId>
    <departmentName>ТП1</departmentName>
</schedule>
```


## Удаление смены

Версия API: 1.0

Версия iiko: 5.0

| ![DELETE Request](/resources/Storage/api-documentations/http_request_delete.png) | https://host:port/resto/api/employees/schedule/byId/{scheduleUUID} |
| --- | --- |

### Что в ответе

Удаленная смена **schedule**.

## Описание сущностей для представления в формате XML (XSD-схема)

[+] [Тип смены](javascript:void%280%29)
 [-] [Тип смены](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```


[+] [Смена в расписании](javascript:void%280%29)
 [-] [Смена в расписании](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

* [Список смен](/articles/api-documentations/kassovye-smeny-v2/a/h2__1634510164)
* [Параметры запроса](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Параметры.1)
* [Что в ответе](/articles/api-documentations/kassovye-smeny-v2/a/h3_501454233)
* [Пример запроса и результат](/articles/api-documentations/kassovye-smeny-v2/a/h3_1561844723)
* [Выгрузка платежей, внесений, изъятий за смену](/articles/api-documentations/kassovye-smeny-v2/a/h2_1746421875)
* [Параметры запроса](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Параметры)
* [Что в ответе](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Результат)
* [Выгрузка кассовой смены по id](/articles/api-documentations/kassovye-smeny-v2/a/h2_775061847)
* [Что в ответе](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Результат.1)
* [Пример запроса и результат](/articles/api-documentations/kassovye-smeny-v2/a/h3__2016272752)
* [Выгрузка документы принятия кассовой смены по id смены](/articles/api-documentations/kassovye-smeny-v2/a/h2_1113421559)
* [Что в ответе](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Результат.2)
* [Пример запроса и результата](/articles/api-documentations/kassovye-smeny-v2/a/h3_316519999)
* [Принятие кассовой смены](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Принятиекассовойсмены)
* [Примерный алгоритм принятия кассовой смены](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-Примерныйалгоритмпринятиякассовойсмены)
* [Тело запроса](/articles/api-documentations/kassovye-smeny-v2/a/h3_1150399349)
* [Что в ответе](/articles/api-documentations/kassovye-smeny-v2/a/h3_1772527967)
* [Ошибка](/articles/api-documentations/kassovye-smeny-v2/a/v2.APIкассовыесмены-ОшибкаОшибка)
* [Пример запроса и результат](/articles/api-documentations/kassovye-smeny-v2/a/h3_1387997121)

## Список смен

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/cashshifts/list |
| --- | --- |

### Параметры запроса
| Название | Значение | Описание |
| --- | --- | --- |
| openDateFrom | YYYY-MM-DD | Период открытия смены ''с'' (входит в интервал). |
| openDateTo | YYYY-MM-DD | Период открытия смены ''по'' (входит в интервал). |
| departmentId | UUID | Список ТП, если пуст, то фильтра нет. |
| groupId | UUID | Список групп секций, если пуст, то фильтра нет. |
| status | String<br>| Значение | Описание |<br>| --- | --- |<br>| ANY | Любая. |<br>| OPEN | Открытая. |<br>| CLOSED | Закрытая. |<br>| ACCEPTED | Принята. |<br>| UNACCEPTED | Не принята. |<br>| HASWARNINGS | Подозрительная. | | Фильтр по статусу. Не может быть пустым. |
| --- | --- | --- |
| revisionFrom | число, -1 | Номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 (**с версии iiko 6.4**) |
### Что в ответе

Json структура. Возвращает списки смен
| Поле | Значение |
| --- | --- |
| id | Id смены |
| sessionNumber | Номер кассовый смены (в нумерации фронта). |
| fiscalNumber | Фискальный номер смены (с ФРа). |
| cashRegNumber | Номер ФРа (в нумерации iiko). |
| cashRegSerial | Серийный номер ФРа. |
| openDate | Дата открытия смены. |
| closeDate | Дата закрытия смены. |
| acceptDate | Дата принятия смены. null --- смена не принята. |
| managerId | Ответственный менеджер. |
| responsibleUser | Ответственный кассир. |
| sessionStartCash | Остаток в кассе на начало дня. |
| payOrders | Сумма всех заказов с учётом скидки |
| sumWriteoffOrders | Сумма заказов, закрытых за счет заведения. |
| salesCash | Сумма продаж за наличные. |
| salesCerdit | Сумма продаж в кредит. |
| salesCard | Сумма продаж по картам. |
| payIn | Сумма всех внесений. |
| payOut | Сумма всех изъятий, без учета изъятий в конце смены. |
| payIncome | Сумма изъятия в конце смены. |
| cashRemain | Остаток в кассе после закрытия смены. |
| cashDiff | Общее расхождение сумм книжных и фактических. |
| sessionStaus | Статус смены. |
| conception | Концепция, которой принадлежит данная кассовая смена. |
| pointOfSale | Точка продаж данной кассовой смены. |
###  **Пример запроса и результат**

```
%%CH%PRE0%%


```

## Выгрузка платежей, внесений, изъятий за смену

Версия iiko: 5.4

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/**cashshifts/payments/list/{sessionId}** |
| --- | --- |

### Параметры запроса
| **Название** | **Значение** | **Описание** |
| --- | --- | --- |
| hideAccepted | true, false | скрыть принятые |
### Что в ответе

Json структура. Возвращает списки внесений, изъятий, безналичных платежей за смену
| Поле | Описание |
| --- | --- |
| sessionId | UUID запрошенной смены |
| cashlessRecords | Список записей, относящихся к безналичным платежам. |
| payInRecords | Список записей, относящихся к внесениям. |
| payOutRecords | Список записей, относящихся к изъятиям. || Запись в документе<br>| Поле | Описание |<br>| --- | --- |<br>| info | Описание проводки<br><br><br>| Поле | Описание |<br>| --- | --- |<br>| id | UUID проводки. |<br>| date | Дата создания в формате "yyyy-MM-dd'T'HH:MM:SS"<br><br>Проводки оплат заказов содержат в этом поле учетный день, округленный до суток. |<br>| creationDate | Дата создания в формате "yyyy-MM-dd'T'HH:MM:SS"<br>с привязкой ко времени, может быть меньше, чем date,<br>если используется настройка "конец учетного дня" &lt;&gt; 00:00. |<br>| group | группа проводок:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">CARD (безнал)</span></span></span></span></li><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">CREDIT (кредит)</span></span></span></span></li><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">PAYOUT (изъятия)</span></span></span></span></li><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">PAYIN (внесения)</span></span></span></span></li></ul> |<br>| accountId | Редактируемый счет. Чаще принимается конечный счет проводки. |<br>| counteragentId | Контрагент. |<br>| paymentTypeId | Тип оплаты. |<br>| type | Тип проводки. |<br>| sum | Сумма. |<br>| comment | Комментарий. |<br>| auth | Авторизационные данные транзакции<br>| Поле | Описание |<br>| --- | --- |<br>| user | UUID пользователя. |<br>| card | Номер карты. | |<br>| --- | --- |<br>| causeEvenId | UUID события оплаты заказа. |<br>| cashierId | UUID кассира, совершившего проводку. |<br>| departmentId | UUID торгового предприятия. |<br>| cashFlowCategory | Статья движения денежных средств (ДДС).<br>| Поле | Описание |<br>| --- | --- |<br>| code | Код. |<br>| parentCategory | Родительская статья ДДС. |<br>| type | Тип деятельности:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">OPERATIONAL (операционная)</span></span></span></span></span></li><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">INVESTMENT (инвестиционная)</span></span></span></span></span></li><li><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">FINANCE (финансовая)</span></span></span></span></span></li></ul> | |<br>| --- | --- | |<br>| --- | --- |<br>| actualSum | Сумма из элемента документа закрытия кассовой смены соответствующего данным проводки<br><br>или сумма из проводки, если такового не нашлось. |<br>| originalSum | Сумма проводки. |<br>| editedPayAccountId | Счет из элемента документа закрытия кассовой смены соответствующего данным проводки<br><br>или сумма из проводки, если такового не нашлось. Редактируемый счет. |<br>| originalPayAccountId | Счет, значение которого совпадает с editedPayAccountId. |<br>| payAgentId | Контрагент из элемента документа закрытия смены соответствующего данным проводки или<br><br>из транзакции, если такого элемента не нашлось. |<br>| paymentTypeId | Тип оплаты. |<br>| editableComment | Комментарий. | |
| --- |
**Пример запроса и результата**

**Запрос**

https://localhost:8080/resto/api/v2/cashshifts/payments/list/f67fea0a-90d4-427c-ac3d-b82c1582f7f9?hideAccepted=false
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```

 
```


```

## Выгрузка кассовой смены по id

Версия iiko: 5.4

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/cashshifts/byId/{sessionId} |
| --- | --- |

### Что в ответе

Json структура кассовой смены.

| Поле | Значение |
| --- | --- |
| id | Id смены |
| sessionNumber | Номер кассовый смены (в нумерации фронта). |
| fiscalNumber | Фискальный номер смены (с ФРа). |
| cashRegNumber | Номер ФРа (в нумерации iiko). |
| cashRegSerial | Серийный номер ФРа. |
| openDate | Дата открытия смены. |
| closeDate | Дата закрытия смены. |
| acceptDate | Дата принятия смены. null --- смена не принята. |
| managerId | Ответственный менеджер. |
| responsibleUser | Ответственный кассир. |
| sessionStartCash | Остаток в кассе на начало дня. |
| payOrders | Сумма всех заказов с учётом скидки |
| sumWriteoffOrders | Сумма заказов, закрытых за счет заведения. |
| salesCash | Сумма продаж за наличные. |
| salesCerdit | Сумма продаж в кредит. |
| salesCard | Сумма продаж по картам. |
| payIn | Сумма всех внесений. |
| payOut | Сумма всех изъятий, без учета изъятий в конце смены. |
| payIncome | Сумма изъятия в конце смены. |
| cashRemain | Остаток в кассе после закрытия смены. |
| cashDiff | Общее расхождение сумм книжных и фактических. |
| sessionStaus | Статус смены. |
| conception | Концепция, которой принадлежит данная кассовая смена. |
| pointOfSale | Точка продаж данной кассовой смены. |

### **Пример запроса и результат**

**Запрос**

https://localhost:8080/resto/api/v2/cashshifts/byId/1c81b65a-1b8a-428f-8a74-2c994a928a86


```

  [+] Результат
  [-] Результат

  
  
     %%CH%PRE2%%
  

```

## Выгрузка документы принятия кассовой смены по id смены

Версия iiko: 5.4

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/**cashshifts/closedSessionDocument/{id}** |
| --- | --- |

### Что в ответе

Json структура документа принятия кассовой смены. Возвращает существующий документ, либо создает новый.
| Поле | Значение |
| --- | --- |
| id | id документа. |
| session | Кассовая смена<br>| Поле | Значение |<br>| --- | --- |<br>| sessionId | id смены. |<br>| groupId | id группы секций работающих в одной кассовой смене. |<br>| number | Номер смены. | |
| --- | --- |
| accountShortageId | Счет, на который записывается недостача. |
| counteragentShortageId | Контрагент, на которого записывается недостача. |
| accountSurplusId | Счет, на который записывается излишек. |
| counteragentSurplusId | Контрагент, на которого записывается излишек. |
| departmentId | Торговое предприятие кассовой смены. |
| items | Элементы/строки документа<br>| Поле | Значение |<br>| --- | --- |<br>| num | Номер элемента. |<br>| transactionId | UUID проводки. |<br>| sumReal | Отредактированная сумма. |<br>| accountOverrideId | Отредактированный счет. |<br>| counteragentOverrideId | Отредактированный контрагент. |<br>| status | Статус.<br>| Значение | Описание |<br>| --- | --- |<br>| ACCEPTED | принята |<br>| UNACCEPTED | не принята |<br>| HASWARNINGS | подозрительная | |<br>| --- | --- |<br>| comment | Комментарий. | |
| --- | --- |
### **Пример запроса и результата**

https://localhost:8080/resto/api/v2/cashshifts/closedSessionDocument/f67fea0a-90d4-427c-ac3d-b82c1582f7f9


```json
{ 
   "id":"1a94e9e8-56cf-3a14-015b-ce1629e5006b",
   "session":{ 
      "sessionId":"f67fea0a-90d4-427c-ac3d-b82c1582f7f9",
      "groupId":"94a6f400-2f9b-4a5a-be7f-19b7b62c55a7",
      "number":1
   },
   "accountShortageId":null,
   "counteragentShortageId":null,
   "accountSurplusId":null,
   "counteragentSurplusId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
   "departmentId":"cb90393a-8299-4af1-9fab-5ec308726266",
   "items":[ 
      { 
         "num":0,
         "transactionId":"e08a16b6-931c-4068-9aa5-b740d5ce726b",
         "sumReal":2660,
         "accountOverrideId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
         "counteragentOverrideId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
         "status":"ACCEPTED",
         "comment":"test"
      }
   ]
}
```


## Принятие кассовой смены

### Примерный алгоритм принятия кассовой смены

1. Получить список кассовых смен. Выбрать id смены, которую нужно принять.
2. Получить документ принятия кассовой смены по id смены.
3. Получить список безналичных платежей, внесений, изъятий по выбранной из п.1 кассовой смене.
4. Дополнить список элементов документа недостающими.

Список из п.3 содержит все проводки смены. Документ принятия смены из п.2 состоит из элементов, редактирующих
такие проводок. Если есть проводки, для которых нет элементов в документе (например, когда смена закрывается впервые),
то нужно добавить новые элементы. Другими словами документ принятия смены должен содержать все проводки из п.3.

Добавление нового элемента происходит на основании записи из списка, полученного в п.3., следующим образом:

* В поле num устанавливается следующий порядковый номер.
* В поле transactionId устанавливается UUID добавляемой проводки.
* В поле sumReal указывается результат редактирования суммы проводки: поле sum. sumReal заполняется только для
изъятий. т.е. для записей из payOutRecords. Для других записей сумма не редактируется.

* В поле accountOverride устанавливаете результат редактирования счета из поля accountId. В counteragentOverride
результат редактирования counteragentId с некоторыми правилами.

* Указывается нужный статус и комментарий.

5. Отредактировать документ.

6. Отправить на сервер.

Версия iiko: 5.4

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/**cashshifts/save** |
| --- | --- |

Content-Type: application/json

### Тело запроса
| Поле | Значение |
| --- | --- |
| id | id документа. |
| session | Кассовая смена<br>| Поле | Значение |<br>| --- | --- |<br>| sessionId | id смены. |<br>| group | id группы секций работающих в одной кассовой смене. |<br>| number | Номер смены. | |
| --- | --- |
| accountShortageId | Счет, на который записывается недостача. |
| counteragentShortageId | Контрагент, на которого записывается недостача. |
| accountSurplusId | Счет, на который записывается излишек. |
| counteragentSurplusId | Контрагент, на которого записывается излишек.[1] |
| departmentId | Торговое предприятие кассовой смены. |
| items | Элементы/строки документа.<br><br>Элемент - продажа за безнал, внесение, изъятие.<br>| Поле | Значение |<br>| --- | --- |<br>| num | Номер элемента. |<br>| transactionId | UUID проводки кассовой смены. |<br>| sumReal | Отредактированная сумма. |<br>| accountOverrideId | Отредактированный счет. |<br>| counteragentOverrideId | Отредактированный контрагент.[2] |<br>| status | Статус.<br>| Значение | Описание |<br>| --- | --- |<br>| ACCEPTED | принята |<br>| UNACCEPTED | непринята |<br>| HASWARNINGS | подозрительная | |<br>| --- | --- |<br>| comment | Комментарий. | |
| --- | --- |
[1].Счета/контрагенты для недостачи/излишка должны быть заполнены независимо от выбранного счета.

Так сделано для обратной совместимости.

[2]. Контрагент в элементе документа должен быть указан только для счетов :
| Тип счета | Название |
| --- | --- |
| 
```
ACCOUNTS_RECEIVABLE
```
 | Задолженность покупателей |
| 
```
DEBTS_OF_EMPLOYEES
```
 | Задолженность сотрудников |
| 
```
EMPLOYEES_LIABILITY
```
 | Расчеты с сотрудниками |
| 
```
ACCOUNTS_PAYABLE
```
 | Расчеты с поставщиками |
| 
```
CLIENTS_LIABILITY
```
 | Расчеты с гостями |
Список доступных счетов можно получить через API счетов.


```json
{ 
   "id":"1a94e9e8-56cf-3a14-015b-ce1629e5006b",
   "session":{ 
      "sessionId":"f67fea0a-90d4-427c-ac3d-b82c1582f7f9",
      "groupId":"94a6f400-2f9b-4a5a-be7f-19b7b62c55a7",
      "number":1
   },
   "accountShortageId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
   "counteragentShortageId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
   "accountSurplusId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
   "counteragentSurplusId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
   "departmentId":"cb90393a-8299-4af1-9fab-5ec308726266",
   "items":[ 
      { 
         "num":0,
         "transactionId":"e08a16b6-931c-4068-9aa5-b740d5ce726b",
         "sumReal":2650,
         "accountOverrideId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
         "counteragentOverrideId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
         "status":"ACCEPTED",
         "comment":"test"
      }
   ]
}
```


### Что в ответе

Содержит результат импорта, который состоит из результата валидации импортируемого документа и самого документа. Результат валидации состоит из ошибок, общих для всего документа, и ошибок по каждому отдельному элементу документа. Ошибка состоит из кода ошибки и текста ошибки.

| Поле | Значение |
| --- | --- |
| importResult | Статус результата принятия смены<br><br>SUCCESS, ERROR |
| status | Статус принятой смены. Вычисляется из совокупности статусов элементов документа.<br><br>Статус элемента задает пользователь. Если хотя бы один элемент имеет статус HASWARNINGS,<br><br>то весь документ будет в статусе HASWARNINGS, если хотя бы один элемент в статусе UNACCEPTED,<br><br>то весь документ будет в таком же статусе, ACCEPTED - все элементы приняты.<br><br>У HASWARNINGS самый высокий приоритет.<br>| Значение | Описание |<br>| --- | --- |<br>| UNACCEPTED | не принята |<br>| ACCEPTED | принята |<br>| HASWARNINGS | подозрительна | |
| --- | --- |
| errors | Список ошибок, не позволивших сделать успешный импорт документа.<br>| Поле | Значение |<br>| --- | --- |<br>| documentError | Ошибки в полях документа. |<br>| itemError | Ошибки в полях документа.<br>| Поле | Значение |<br>| --- | --- |<br>| identifier | UUID элемента. |<br>| error | Ошибка. | |<br>| --- | --- | |
| --- | --- |
| document | Импортируемый документ. |
### Ошибка
| Поле | Значение |
| --- | --- |
| value | Неверное значение, либо название пустого поля. |
| code | Код ошибки. |
### 
 [+] [Коды ошибок](javascript:void%280%29)
 [-] [Коды ошибок](javascript:void%280%29)
 | Код | Описание |
| --- | --- |
| ACCOUNT\_DELETED | Указанный счет удален. |
| COUNTERAGENT\_DELETED | Указанный контрагент удален. |
| INVENTORY\_ASSETS\_TYPE\_NOT\_ALLOWED | Счета категории "складские запасы" не допускаются. |
| COUNTERAGENT\_MISSED\_FOR\_ACCOUNT | Для указанного счета должен быть указан контрагент. |
| COUNTERAGENT\_NOT\_ALLOWED\_FOR\_ACCOUNT | Для указанного счета контрагент не указывается. |
| ACCOUNT\_NOT\_SPECIFIED | Счет не указан. |
| COUNTERAGENT\_NOT\_SPECIFIED | Контрагент не указан. |
| COUNTERAGENT\_NOT\_ALLOWED | Контрагент НЕ указывается. |
| COUNTERAGENT\_TYPE\_WRONG | Указан неверный тип для выбранного контрагента. |
| CONCEPTION\_NOT\_SPECIFIED | Концепция не указана. |
| CONCEPTION\_DELETED | Концепция удалена. |
| PAYROLL\_MISSED\_FOR\_ACCOUNT | Для указанного счета должен быть указана платежная ведомость. |
| PAYROLL\_DELETED | Платежная ведомость удалена. |
| ONLY\_POSITIVE\_VALUES\_ALLOWED | Допускаются только положительные значения. |
| DEPARTMENT\_DELETED | ТП удалено. |
| RESTAURANT\_SECTION\_DELETED | Отделение удалено. |
| MEASURE\_UNIT\_DELETED | Единица измерения удалена. |
| COOKING\_PLACE\_DELETED | Место приготовления удалено. |
| TAX\_CATEGORY\_DELETED | Налоговая категория удалена. |
| PRODUCT\_CATEGORY\_DELETED | Пользовательская категория удалена. |
| PRODUCT\_GROUP\_DELETED | Номенклатурная группа удалена. |
| PRODUCT\_DELETED | Товар удален. |
| PRODUCT\_MISSED | Товар не указан. |
| COOKING\_PLACE\_EMPTY\_FOR\_SALE\_DISH | Товар продается. Тип места приготовления не может быть пустым. |
| WRONG\_NOMENCLATURE\_TYPE | Указан недопустимый тип номенклатуры. |
| NOT\_INCLUDED\_IN\_MENU\_WITH\_EXCLUDED\_SECTIONS | У блюда указаны отделения, в которых его нельзя продавать, в то время, как <br>само блюдо не включено в меню по умолчанию. |
| CHILD\_MODIFIERS\_NOT\_ALLOWED | Вложенные модификаторы не допускаются. |
| MODIFIER\_NOT\_BELONGS\_TO\_GROUP | Модификатор не принадлежит группе. |
| NOT\_MODIFIER | Не является модификатором. |
| WRONG\_MIN\_MAX\_AMOUNT | Не правильно указаны минимальное, максимальное значение. |
| HAS\_RESTRICTION\_AND\_DEFAULT\_AMOUNT\_OUT\_OF\_RANGE | У родительского модификатора **ВКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов",<br>но дефолтное значение у дочернего модификатора выходит за рамки мин. макс. значений. |
| DEFAULT\_AMOUNT\_OUT\_OF\_RANGE | Дефолтное значение выходит за рамки мин. макс. значений. |
| NO\_RESTRICTION\_AND\_MIN\_MAX\_NOT\_ZERO | У родительского модификатора **ВЫКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов",<br>у дочернего мин. макс. количество не равно 0 (а должно). |
| REQUIRED\_AND\_WRONG\_MIN\_AMOUNT | Модификатор является обязательным, но мин. количество = 0, <br>либо НЕ является обязательным и мин. количество != 0.<br><br>Начиная с версии iiko 6.2.3 ошибка с таким кодом прилететь не может, т.к. поле **required** было убрано из ChoiceBindingDto |
| FREE\_OF\_CHARGE\_AMOUNT\_MORE\_THAN\_MAX | У группового или одиночного модификатора количество бесплатных больше чем максимальное. |
| HAS\_RESTRICTION\_AND\_FREE\_OF\_CHARGE\_MORE\_THAN\_MAX | У родительского модификатора **ВКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов", но <br>бесплатное количество у дочернего модификатора больше максимального. |
| HAS\_RESTRICTION\_AND\_FREE\_OF\_CHARGE\_MORE\_THAN\_PARENT | У родительского модификатора **ВКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов", но <br>бесплатное количество у дочернего модификатора больше чем у родительского. |
| NO\_RESTRICTION\_AND\_FREE\_OF\_CHARGE\_AMOUNT\_NOT\_EQUAL\_VALUE\_IN\_PARENT | У родительского модификатора **ВЫКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов", но<br>бесплатное количество у дочернего модификатора не равно бесплатному количеству в родительском. |
| NO\_RESTRICTION\_AND\_REQUIRED\_SHOULD\_BE\_FALSE | У родительского модификатора **ВЫКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов",<br>но дочерний модификатор является обязательным. |
| NOT\_GROUP\_MODIFIER\_HAS\_CHILD\_RESTRICTION | У **НЕ** группового (одиночного, дочернего) модификатора **ВКЛЮЧЕНО** "Ограничение на минимум и максимум у дочерних модификаторов". |
| SINGLE\_MODIFIER\_HIDE\_DEFAULT\_AMOUNT | У одиночного модификатора<br><br>"Скрывать, если кол-во по умолчанию". |
| PARENT\_AMOUNT\_BY\_DEFAULT\_NOT\_EQUAL\_SUM\_OF\_CHILDREN | У родительского модификатора кол-во по умолчанию не равно сумме дефолтный значений дочерних элементов. |
| IMAGE\_NOT\_FOUND | Изображение не найдено. | 
```


```


### **Пример запроса и результат**

**Запрос**


```
https://localhost:8080/resto/api/v2/cashshifts/save 

```

#### Результат

```
%%CH%PRE5%%
​
```


#### Пример успешного импорта - **SUCCESS**

**
```json
{ 
   "importResult":"SUCCESS",
   "status":"ACCEPTED",
   "errors":null,
   "document":{ 
      "id":"1a94e9e8-56cf-3a14-015b-ce1629e5006b",
      "session":{ 
         "sessionId":"f67fea0a-90d4-427c-ac3d-b82c1582f7f9",
         "groupId":"94a6f400-2f9b-4a5a-be7f-19b7b62c55a7",
         "number":1
      },
      "accountShortageId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
      "counteragentShortageId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
      "accountSurplusId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
      "counteragentSurplusId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
      "departmentId":"cb90393a-8299-4af1-9fab-5ec308726266",
      "items":[ 
         { 
            "num":0,
            "transactionId":"e08a16b6-931c-4068-9aa5-b740d5ce726b",
            "sumReal":2650,
            "accountOverrideId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
            "counteragentOverrideId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
            "status":"ACCEPTED",
            "comment":"test"
         }
      ]
   }
}
```
**

#### `Пример не успешного импорта - ``ERROR`

`
```json
{ 
   "importResult":"ERROR",
   "status":null,
   "errors":{ 
      "documentError":[ 
         { 
            "value":"ad3cc1aa-a60c-c85c-e66d-3904490de4b9",
            "code":"ACCOUNT_SHORTAGE_NOT_FOUND"
         },
         { 
            "value":"counteragentShortage",
            "code":"EMPTY_FIELD"
         }
      ],
      "itemError":[ 
         { 
            "identifier":0,
            "error":[ 
               { 
                  "value":"bd3cc1aa-a60e-c85c-e66d-3904490de4b9",
                  "code":"INVENTORY_ASSETS_TYPE_NOT_ALLOWED"
               },
               { 
                  "value":"6c6f7e76-2fee-473e-879e-4c4c2faaa032",
                  "code":"COUNTERAGENT_DELETED"
               }
            ]
         }
      ]
   },
   "document":{ 
      "id":"1a94e9e8-56cf-3a14-015b-ce1629e5006b",
      "session":{ 
         "sessionId":"f67fea0a-90d4-427c-ac3d-b82c1582f7f9",
         "group":"94a6f400-2f9b-4a5a-be7f-19b7b62c55a7",
         "number":1
      },
      "accountShortageId":"ad3cc1aa-a60c-c85c-e66d-3904490de4b9",
      "counteragentShortageId":null,
      "accountSurplusId":"ad3cc1aa-a60e-c85c-e66d-3904490de4b9",
      "counteragentSurplusId":"2c6f7e76-2fee-473e-879e-4c4c2faaa032",
      "departmentId":"cb90393a-8299-4af1-9fab-5ec308726266",
      "items":[ 
         { 
            "num":0,
            "transactionId":"e08a16b6-931c-4068-9aa5-b740d5ce726b",
            "sumReal":2650,
            "accountOverrideId":"bd3cc1aa-a60e-c85c-e66d-3904490de4b9",
            "counteragentOverrideId":"6c6f7e76-2fee-473e-879e-4c4c2faaa032",
            "status":"HASWARNINGS",
            "comment":"test"
         }
      ]
   }
}
```
​`

* [Доступ](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Доступ)
* [Получение типов внесений и изъятий](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Получениетиповвнесенийиизъятий)
* [Параметры запроса](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Параметры)
* [Что в ответе](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Результат)
* [Пример запроса и результата](/articles/api-documentations/rabota-s-izyatiyami/a/h3__232688264)
* [Совершить изъятие](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Совершитьизъятие.)
* [Тело запроса](/articles/api-documentations/rabota-s-izyatiyami/a/h3_1150399349)
* [Что в ответе](/articles/api-documentations/rabota-s-izyatiyami/a/h3_501454233)
* [Пример вызова](/articles/api-documentations/rabota-s-izyatiyami/a/h3_2017789044)
* [Получение платежных ведомостей](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Получениеплатежныхведомостей)
* [Параметры запроса](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIкассовыесмены-Параметры)
* [Что в ответе](/articles/api-documentations/rabota-s-izyatiyami/a/v2.APIизъятия-Результат.2)
* [Пример запроса и результата](/articles/api-documentations/rabota-s-izyatiyami/a/h3_41887754)
* [Примеры изъятий](/articles/api-documentations/rabota-s-izyatiyami/a/h2_1154554098)
* [Изъятие. Платёжная ведомость](/articles/api-documentations/rabota-s-izyatiyami/a/h3__469280520)
* [Изъятие. Аванс поставщику](/articles/api-documentations/rabota-s-izyatiyami/a/h3__474185203)

## Доступ

Чтобы пользоваться API:

* Получения типов внесений и изъятий: право B\_APIO "Просматривать типы внесений/изъятий".
* Выполнения изъятий: право F\_APIO "Авторизовывать кассовые внесения и изъятия".

## Получение типов внесений и изъятий

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/entities/payInOutTypes/list |
| --- | --- |

### Параметры запроса
| **Название** | **Тип данных** | **Версия** | **Описание** |
| --- | --- | --- | --- |
| includeDeleted | Boolean |  | включая удаленные (по умолчанию false) |
| revisionFrom | -1, число | с 6.4 | Номер ревизии, начиная с которой необходимо отфильтровать сущности. Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom.<br><br>По умолчанию (неревизионный запрос) revisionFrom = -1 |
### Что в ответе

Json структура. Возвращает список типов внесений и изъятий.

### 

| **Поле** | **Тип данных** | **Описание** |
| id | UUID | Guid внесения/изъятия в базе iiko. |
| chiefAccount | UUID | Guid шеф-счёта. При изъятии перемещаются на корр. счёт, а при внесении наоборот. |
| account | UUID | Guid корр-счёта. При изъятии перемещаются на корр. счёт, а при внесении наоборот. |
| counteragentType | Enum | Тип контрагента:<br><ul><li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">NONE (нет)</span></span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">COUNTERAGENT (все)</span></span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">EMPLOYEE (сотрудник)</span></span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">SUPPLIER (поставщик)</span></span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">CLIENT (гость)</span></span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;"><span style="">INTERNAL_SUPPLIER (внутренний поставщик)</span></span></span></li></ul> |
| transactionType | Enum | Тип проводки. |
| cashFlowCategory | DTO | Статья движения денежных средств (ДДС). |
| conception | DTO | Концепция<br> <br><br>| Параметр | Тип, формат | Описание |<br>| --- | --- | --- |<br>| id | String | Guid концепции в базе iiko. |<br>| code | String | Код. |<br>| name | String | Название. | |
| --- | --- | --- |
| limit | BigDecimal | Предельная сумма для внесений/изъятий на iikoFront. |
| comment | String | Комментарий |
| mandatoryFrontComment | Boolean | Требовать ввода комментария к операции в iikoFront. |
| isDeleted | Boolean | Удален |

### **Пример запроса и результата**

**Запрос**

https://localhost:8080/resto/api/v2/entities/payInOutTypes/list?includeDeleted=true

[+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE0%%
```


## Совершить изъятие

Версия iiko: 6.0

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/payInOuts/addPayOut |
| --- | --- |

Content-Type: application/json

### Тело запроса

| Поле | Тип данных | Описание |
| --- | --- | --- |
| payOutTypeId | UUID | Guid типа изъятия в базе iiko. |
| payOutDate | String | Дата в формате yyyy-MM-dd. Время проставляется текущее. |
| counteragent | UUID | Guid контрагента в базе iiko. В зависимости от типа изъятия. |
| departmentSumMap | UUID -&gt; BigDecimal | Торговое предприятие -&gt; сумма изъятия. |
| payrollId | UUID | Guid платежной ведомости в базе iiko. Указывается если изъятие происходит на счет<br>(т.е. корр.счет) "Текущие расчеты с сотрудниками". |
| comment | String | Комментарий. |

### Что в ответе

Содержит результат изъятия, который состоит из результата валидации параметров изъятия и самого изъятия. Результат валидации состоит из ошибок. Ошибка состоит из кода ошибки и текста ошибки.

### 

| Поле | Тип данных | Значение |
| --- | --- | --- |
| result | Enum | SUCCESS, ERROR |
| payOutSettings | DTO | Параметры изъятия. |
| errors | DTO | Список ошибок, не позволивших сделать изъятие. |

### **Пример вызова**

**** https://localhost:8080/resto/api/v2/payInOuts/addPayOut

#### **Пример результата - SUCCESS**

**
```json
 { 
   "result":"SUCCESS",
   "errors":null,
   "payOutSettings":{ 
      "payOutTypeId":"37d410d1-c524-4a76-b28c-8b733e313d7a",
      "payOutDate":"2017-10-18",
      "counteragent":null,
      "departmentSumMap":{ 
         "06d7ec0c-8fee-f341-015f-b58127ff000d":1500
      },
      "payrollId":null,
      "comment":null
   }
}
```
**

#### **Пример результата - ERROR**

**
```json
{ 
   "result":"ERROR",
   "errors":[ 
      { 
         "value":"chiefAccount",
         "code":"ACCOUNT_NOT_SPECIFIED"
      }
   ],
   "payOutSettings":{ 
      "payOutTypeId":"32e01087-ded3-b5bb-4b82-6a3f0348af84",
      "payOutDate":"2017-10-18",
      "counteragent":null,
      "departmentSumMap":{ 
         "06d7ec0c-8fee-f341-015f-b58127ff000d":-100
      },
      "payrollId":null,
      "comment":null
   }
}
```
**

## Получение платежных ведомостей

Версия iiko: 6.0

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/payrolls/list |
| --- | --- |

### Параметры запроса

| Поле | Тип данных | Описание |
| --- | --- | --- |
| dateFrom | String | Начало периода в формате yyyy-MM-dd, включительно. |
| dateTo | String | Окончание периода в формате yyyy-MM-dd, включительно. |
| department | UUID | Guid торгового предприятия. в базе iiko. |
| includeDeleted | Boolean | Включая удаленные (по умолчанию false). |

### Что в ответе

Возвращает список платежных ведомостей.
| Поле | Тип данных | Описание |
| --- | --- | --- |
| payrollId | UUID | UUID ведомости. |
| dateFrom | Date | Дата начала действия. |
| dateTo | Date | Дата окончания действия. |
| department | UUID | Guid торгового предприятия. |
| documentNumber | String | Номер документа. |
| status | Enum | Статус документа (NEW, PROCESSED, DELETED). |
| comment | String | Комментарий. |

### **Пример запроса и результата**

**Запрос**
https://localhost:8080/resto/api/v2/payrolls/list?dateFrom=2017-08-01&dateTo=2017-10-01&department=372f68b4-8e7a-bae1-015f-0f9c638f000d

#### Результат


```json
[
    {
        "id": "d4b29bd7-076f-48ba-9f93-6f21b78f47bf",
        "dateFrom": "2017-10-01T00:00:00",
        "dateTo": "2017-10-31T23:59:59",
        "department": "372f68b4-8e7a-bae1-015f-0f9c638f000d",
        "documentNumber": "0001",
        "status": "PROCESSED",
        "comment": null
   }
]

```


| ![Warning](/resources/Storage/api-documentations/api-documentations/warning.png) | Для использования кириллицы в комментарии (параметр comment) при совершении изъятия в headers запроса должен быть параметр: *content-type: application/json;charset=UTF-8* |
| --- | --- |

## Примеры изъятий

### **Изъятие. Платёжная ведомость**

**Запрос**

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/payInOuts/addPayOut |
| --- | --- |


Код

```

{
"payOutTypeId":"114c757f-bac4-422c-a184-0935923b60b8",
"payOutDate":"2017-12-13",
"counteragent":"d244cb85-9115-4b4d-8e02-a4f7fdd8ec15",
"departmentSumMap":{
"2b9c2770-f146-43b8-9ac1-ad717d9c7996":90.0
},
"payrollId":"c1349656-8401-4476-9541-7f0325c65f98",
"comment":"Comment"
}
```


**Результат**


Код

```
{
"result": "SUCCESS",
"errors": null,
"payOutSettingsDto": {
"payOutTypeId": "114c757f-bac4-422c-a184-0935923b60b8",
"payOutDate": "2017-12-13",
"counteragent": "d244cb85-9115-4b4d-8e02-a4f7fdd8ec15",
"departmentSumMap": {"2b9c2770-f146-43b8-9ac1-ad717d9c7996": 90},
"payrollId": "c1349656-8401-4476-9541-7f0325c65f98",
"comment": "Comment "
}
}
```


### **Изъятие. Аванс поставщику**

**Запрос**

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/payInOuts/addPayOut |
| --- | --- |


Код

```

{
"payOutTypeId":"0cacd214-c280-4f58-afb3-28d25de90c21",
"payOutDate":"2017-12-13",
"counteragent":"ac716010-c95c-4705-a4bf-d202816c406e",
"departmentSumMap":{
"2b9c2770-f146-43b8-9ac1-ad717d9c7996":1000.0
},
"comment":"test1"
}
```


**Результат**


Код

```
{
"result": "SUCCESS",
"errors": null,
"payOutSettingsDto": {
"payOutTypeId": "0cacd214-c280-4f58-afb3-28d25de90c21",
"payOutDate": "2017-12-13",
"counteragent": "ac716010-c95c-4705-a4bf-d202816c406e",
"departmentSumMap": {"2b9c2770-f146-43b8-9ac1-ad717d9c7996": 1000},
"payrollId": null,
"comment": "test1"
}
}
```

* [OLAP-отчет](/articles/api-documentations/olap-otchety-v1/a/h2_1993590971)
* [Параметры запроса](/articles/api-documentations/olap-otchety-v1/a/h3_1827755295)
* [Что в ответе](/articles/api-documentations/olap-otchety-v1/a/h3__232688264)
* [Описание полей OLAP-отчетов](/articles/api-documentations/olap-otchety-v1/a/h3_1457076905)

## OLAP-отчет
 
Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/****api/** **reports/olap** |
| --- | --- |

### Параметры запроса

| Название | Значение | **Описание** |
| --- | --- | --- |
| *report* | SALES - По продажам<br> <br>TRANSACTIONS - По транзакциям<br> <br>DELIVERIES - По доставкам<br> <br>STOCK - Контроль хранения | Тип отчета |
| *summary* | true - вычислять итоговые значения<br><br>false - не вычислять итоговые значения | Вычислять ли итоговые значения.<br>По умолчанию выстален true. При значении false отчет строится намного быстрее.<br><br>с **Version (iiko) 5.3**<br><br>**С версии 9.1.2 значение по умолчанию false.** |
| *groupRow* | Поля группировки, например: groupRow=WaiterName& groupRow=OpenTime | Для определения списка доступных полей см.:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по продажам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по проводкам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по доставкам </span></span></li> </ul> <br>По полю можно проводить группировку, если значение в колонке Grouping для поля равно true |
| *groupCol* | Поля для выделения значений по колонкам | Для определения списка доступных полей см.:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по продажам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по проводкам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по доставкам </span></span></li> </ul> <br>По полю можно проводить группировку, если значение в колонке Grouping для поля равно true |
| *agr* | Поля агрегации, например: agr=DishDiscountSum&agr=VoucherNum | <ul style="margin: 0px; padding-left: 22px;"> <li> <p style="margin: 0px;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Для определения списка доступных полей см.: </span></span></p><ul style="list-style-type: disc; padding-left: 22px;"> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по продажам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по проводкам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по доставкам </span></span></li> </ul> </li> </ul> <br>По полю можно проводить агрегацию, если значение в колонке Aggregation для поля равно true |
| *from* | DD.MM.YYYY | Начальная дата |
| *to* | DD.MM.YYYY | Конечная дата |

### Что в ответе

Структура *report.*

### Пример запроса

| https://localhost:8080/resto/api/reports/olap?key=ec621550-afae-133e-80c8-76155db2b268&report=SALES&from=01.12.2014&to=18.12.2014&groupRow=WaiterName&groupRow=OpenTime&agr=fullSum&agr=OrderNum |
| --- |

### Описание полей OLAP-отчетов
 [+] [Описание полей OLAP-отчета по доставкам](javascript:void%280%29)
 [-] [Описание полей OLAP-отчета по доставкам](javascript:void%280%29)
 # 

| **Name** | **Description** | **Aggreation** | **Grouping** | **Filtering** | **Type** | **Value** |
| --- | --- | --- | --- | --- | --- | --- |
| CloseTime | Время закрытия | false | true | true | DATETIME |  |
| Delivery.ActualTime | Фактическое время доставки | false | true | true | DATETIME |  |
| Delivery.Address | Адрес | false | true | true | STRING |  |
| Delivery.BillTime | Время печати накладной | false | true | true | DATETIME |  |
| Delivery.CancelCause | Причина отмены доставки | false | true | true | STRING |  |
| Delivery.City | Город | false | true | true | STRING |  |
| Delivery.CloseTime | Время закрытия доставки | false | true | true | DATETIME |  |
| Delivery.CookingToSendDuration | Длит: посл.серв.печать-отправка | true | false | false | INTEGER |  |
| Delivery.Courier | Курьер | false | true | true | STRING |  |
| Delivery.CustomerCardNumber | Номер карты клиента доставки | false | true | true | STRING |  |
| Delivery.CustomerCardType | Тип карты клиента доставки | false | true | true | STRING |  |
| Delivery.CustomerComment | Комментарий к клиенту | false | true | true | STRING |  |
| Delivery.CustomerCreatedDate<br><br>(до версии 4.2; в 4.2+ deprecated, заменено на Delivery.CustomerCreatedDateTyped) | Дата создания клиента | false | true | true | STRING |  |
| Delivery.CustomerCreatedDateTyped (4.2+) | Дата создания клиента | false | true | true | DATE |  |
| Delivery.CustomerMarketingSource | Реклама клиента | false | true | true | STRING |  |
| Delivery.CustomerName | ФИО клиента доставки | false | true | true | STRING |  |
| Delivery.Delay | Опоздание доставки(мин) | false | true | true | INTEGER |  |
| Delivery.DelayAvg | Ср.опоздание доставки(мин) | true | false | false | AMOUNT |  |
| Delivery.DeliveryComment | Комментарий к доставке | false | true | true | STRING |  |
| Delivery.DeliveryOperator | Оператор доставки | false | true | true | STRING |  |
| Delivery.Email | e-mail доставки | false | true | true | STRING |  |
| Delivery.ExpectedTime | Планируемое время доставки | false | true | true | DATETIME |  |
| Delivery.MarketingSource | Реклама | false | true | true | STRING |  |
| Delivery.Number | Номер доставки | false | true | true | INTEGER |  |
| Delivery.Phone | Телефон доставки | false | true | true | STRING |  |
| Delivery.PrintTime | Время печати доставки | false | true | true | DATETIME |  |
| Delivery.Region | Район | false | true | true | STRING |  |
| Delivery.SendTime | Время отправки доставки | false | true | true | DATETIME |  |
| Delivery.ServiceType | Тип доставки | false | true | true | ENUM | PICKUP<br>COURIER |
| Delivery.SourceKey | Источник доставки | false | true | true | STRING |  |
| Delivery.Street | Улица | false | true | true | STRING |  |
| Delivery.WayDuration | Время в пути(мин) | false | true | true | INTEGER |  |
| Delivery.WayDurationAvg | Ср.время в пути(мин) | true | false | false | AMOUNT |  |
| Delivery.WayDurationSum | Сумм.время в пути(мин) | true | false | false | INTEGER |  |
| DishServicePrintTime.Max | Сервисная печать последнего блюда | true | false | false | DATETIME |  |
 [+] [Описание полей OLAP отчета по проводкам](javascript:void%280%29)
 [-] [Описание полей OLAP отчета по проводкам](javascript:void%280%29)
 | ![Information](/resources/Storage/api-documentations/info.png) | Поля агрегации, учитывающие **начальный остаток товара и денежный остаток** (StartBalance.Amount, StartBalance.Money, FinalBalance.Amount, FinalBalance.Money) вычисляются суммированием всей таблицы проводок **за все время** работы системы (всей базы данных) без каких-либо оптимизаций. То есть, такой запрос может выполняться очень долго и замедлять работу сервера.<br><br>Если начальный остаток необходим, оставляйте в этом OLAP-запросе только те поля группировки, по которым он действительно необходим (как правило, это Account.Name и Product.Name), и вызывайте такой запрос **как можно реже** и в **не рабочее** время.<br><br>В 5.2 добавлено API для быстрого получения остатков: Отчеты по балансам. Во всех случаях рекомендуется пользоваться им вместо OLAP.<br><br>В 5.5 OLAP-отчеты с остатками оптимизированы с использованием балансовых таблиц ATransactionSum, ATransactionBalance, при условии, что применяются группировки и фильтры по полям из этих таблиц, см. признак StartBalanceOptimizable в описании полей.<br><br>То есть, правильно составленный запрос приведет к суммированию не всей таблицы проводок, а только лишь открытого периода. Обратите особое внимание на то, что оптимизировано только поле Account.Name (счет "текущей" стороны проводки, в том числе склад), а не Store (первый попавшийся "склад" проводки, взятый из: левой, правой части проводки, строки документа или самого документа).<br>**Склад** всегда, когда только возможно, следует брать из поля Account.Name ("Счет"), а **не** Store ("Склад"), оно вычисляется гораздо быстрее. |
| --- | --- |

| **Name** | **Description** | **Aggreation** | **Grouping** | **Filterig** | **StartBakanceOptimizable** | **Type** | **Value** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Account.AccountHierarchyFull | Иерархия счета | false | true | true | true | STRING |  |
| Account.AccountHierarchySecond | Счет 2-го уровня | false | true | true | true | STRING |  |
| Account.AccountHierarchyThird | Счет 3-го уровня | false | true | true | true | STRING |  |
| Account.AccountHierarchyTop | Счет 1-го уровня | false | true | true | true | STRING |  |
| Account.Code | Код счета | false | true | true | true | STRING |  |
| Account.CounteragentType | Тип контрагента | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип Контрагента |
| Account.Group | Группа счета | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Группа счета |
| Account.IsCashFlowAccount | Участвует ли счет в ДДС | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Участвует ли счет в ДДС |
| Account.Name | Счет | false | true | true | true | STRING | Счет (в том числе склад) |
| Account.StoreOrAccount | Склад/счет | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Счет/Склад |
| Account.Type | Тип счета | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип счета |
| Amount | Количество | true | false | false | - | AMOUNT |  |
| Amount.In | Приход (кол-во) | true | false | false | - | AMOUNT |  |
| Amount.Out | Расход (кол-во) | true | false | false | - | AMOUNT |  |
| Amount.StoreInOut (до версии 4.3; в 4.3+ deprecated, заменено на Amount.StoreInOutTyped) | Оборот эл.номенклатуры | true | false | false | - | STRING |  |
| Amount.StoreInOutTyped (4.3+, взамен Amount.StoreInOut) | Оборот эл.номенклатуры | true | false | false | - | AMOUNT |  |
| CashFlowCategory | Статья ДДС | false | true | true | true | STRING |  |
| CashFlowCategory.Hierarchy | Иерархия статей ДДС | false | true | true | true | STRING |  |
| CashFlowCategory.HierarchyLevel1 | Статья ДДС 1-го уровня | false | true | true | true | STRING |  |
| CashFlowCategory.HierarchyLevel2 | Статья ДДС 2-го уровня | false | true | true | true | STRING |  |
| CashFlowCategory.HierarchyLevel3 | Статья ДДС 3-го уровня | false | true | true | true | STRING |  |
| CashFlowCategory.Type | Тип статьи ДДС | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип статьи ДДС |
| Comment | Комментарий | false | true | true | false | STRING |  |
| Conception | Концепция | false | true | true | true | STRING |  |
| Conception.Code | Код концепции | false | true | true | true | STRING |  |
| Contr-Account.Code | Код корр.счета | false | true | true | false | STRING |  |
| Contr-Account.Group | Группа корр.счета | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Группа счета |
| Contr-Account.Name | Корр.Счет/Склад | false | true | true | false | STRING |  |
| Contr-Account.Type | Тип корр.счета | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Тип счета |
| Contr-Amount | Корр.количество | true | false | false | false | AMOUNT |  |
| Contr-Product.AccountingCategory | Корр.Бухгалтерская категория | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass | Класс алкогольной продукции | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass.Code | Код класса алкогольной продукции | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass.Group | Группа алкогольной продукции | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass.Type | Тип алкогольной продукции | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Тип алкогольной продукции |
| Contr-Product.Category | Корр.Категория номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.CookingPlaceType | Корр.Тип места приготовления | false | true | true | false | STRING |  |
| Contr-Product.Hierarchy | Корр.Иерархия номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.MeasureUnit | Корр.Единица измерения | false | true | true | false | STRING |  |
| Contr-Product.Name | Корр.Элемент номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.Num | Корр.Артикул элемента номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.SecondParent | Корр.Группа номенклатуры 2-го уровня | false | true | true | false | STRING |  |
| Contr-Product.ThirdParent | Корр.Группа номенклатуры 3-го уровня | false | true | true | false | STRING |  |
| Contr-Product.TopParent | Корр.Группа номенклатуры 1-го уровня | false | true | true | false | STRING |  |
| Contr-Product.Type | Корр.Тип элемента номенклатуры | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Тип элемента номенклатуры |
| Counteragent.Name | Контрагент | false | true | true | true | STRING |  |
| DateTime (до версии 4.2; в 4.2+ deprecated, заменено на DateTime.Typed) | Дата и время | false | true | true | true\* | STRING |  |
| DateTime.Typed (4.2+) | Дата и время | false | true | true | true\* | DATETIME |  |
| DateTime.Date (до версии 4.2; в 4.2+ deprecated, заменено на DateTime.DateTyped) | Учетный день | false | true | true | true\* | STRING |  |
| DateTime.DateTyped (4.2+) | Учетный день | false | true | true | true\* | DATE |  |
| DateTime.DayOfWeak | День недели | false | true | true | true\* | STRING |  |
| DateTime.Hour | Час | false | true | true | true\* | STRING |  |
| DateTime.Month | Месяц | false | true | true | true\* | STRING |  |
| DateTime.Year | Год | false | true | true | true\* | STRING |  |
| DateSecondary.DateTyped (добавлено в 6.0) | Дата проводки | false | true | true |  | DATE |  |
| DateSecondary.DateTimeTyped (добавлено в 6.0) | Дата и время проводки | false | true | true |  | DATETIME |  |
| Department | Торговое предприятие | false | true | true | true | STRING |  |
| Department.Category1 | Категория 1 | false | true | true | true | STRING |  |
| Department.Category2 | Категория 2 | false | true | true | true | STRING |  |
| Department.Category3 | Категория 3 | false | true | true | true | STRING |  |
| Department.Category4 | Категория 4 | false | true | true | true | STRING |  |
| Department.Category5 | Категория 5 | false | true | true | true | STRING |  |
| Department.Code | Код подразделения | false | true | true | true | STRING |  |
| Department.JurPerson | Юридическое лицо | false | true | true | true | STRING |  |
| Document | Номер документа | false | true | true | false | STRING |  |
| FinalBalance.Amount | Конечный остаток товара | true | false | false | - | AMOUNT | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| FinalBalance.Money | Конечный денежный остаток | true | false | false | - | MONEY | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| PercentOfSummary.ByCol | % по столбцу | true | false | false | false | PERCENT |  |
| PercentOfSummary.ByRow | % по строке | true | false | false | false | PERCENT |  |
| Product.AccountingCategory | Бухгалтерская категория | false | true | true | true | STRING |  |
| Product.AlcoholClass | Класс алкогольной продукции | false | true | true | true | STRING |  |
| Product.AlcoholClass.Code | Код класса алкогольной продукции | false | true | true | true | STRING |  |
| Product.AlcoholClass.Group | Группа алкогольной продукции | false | true | true | true | STRING |  |
| Product.AlcoholClass.Type | Тип алкогольной продукции | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип алкогольной продукции |
| Product.AvgSum | Средняя цена | true | false | false | - | MONEY |  |
| Product.Category | Категория номенклатуры | false | true | true | true | STRING |  |
| Product.CookingPlaceType | Тип места приготовления | false | true | true | true | STRING |  |
| Product.Hierarchy | Иерархия номенклатуры | false | true | true | true | STRING |  |
| Product.MeasureUnit | Единица измерения | false | true | true | true | STRING |  |
| Product.Name | Элемент номенклатуры | false | true | true | true | STRING |  |
| Product.Num | Артикул элемента номенклатуры | false | true | true | true | STRING |  |
| Product.SecondParent | Группа номенклатуры 2-го уровня | false | true | true | true | STRING |  |
| Product.ThirdParent | Группа номенклатуры 3-го уровня | false | true | true | true | STRING |  |
| Product.TopParent | Группа номенклатуры 1-го уровня | false | true | true | true | STRING |  |
| Product.Type | Тип элемента номенклатуры | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип элемента номенклатуры |
| Session.CashRegister | Касса | false | true | true | false | STRING |  |
| Session.Group | Группа | false | true | true | false | STRING |  |
| Session.RestaurantSection | Отделение | false | true | true | false | STRING |  |
| StartBalance.Amount | Начальный остаток товара | true | false | false | - | AMOUNT | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| StartBalance.Money | Начальный денежный остаток | true | false | false | - | MONEY | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| Store | Склад | false | true | true | false | STRING | Склад: первый попавшийся склад проводки, взятый из: левой, правой части проводки, строки документа или самого документа. |
| Sum.Incoming | Сумма прихода | true | false | false | - | MONEY |  |
| Sum.Outgoing | Сумма расхода | true | false | false | - | MONEY |  |
| Sum.PartOfIncome | % от выручки | true | false | false | - | PERCENT |  |
| Sum.PartOfSummaryByCol | % суммы от итога по столбцам | true | false | false | - | PERCENT |  |
| Sum.PartOfSummaryByRow | % суммы от итога по строкам | true | false | false | - | PERCENT |  |
| Sum.PartOfTotalIncome | % от общей выручки | true | false | false | - | PERCENT |  |
| Sum.ResignedSum | Сумма | true | false | false | - | MONEY |  |
| TransactionSide | Дебет/Кредит | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Дебит/Кредит |
| TransactionType | Тип транзакции | false | true | true | false | ENUM |  |
| TransactionType.Code | Код транзакции | false | true | true | false | OBJECT |  |

\* группировки по дате отбрасываются при вычислении начальных остатков
 [+] [Описание полей OLAP отчета по продажам](javascript:void%280%29)
 [-] [Описание полей OLAP отчета по продажам](javascript:void%280%29)

# 

| **Name** | **Description** | **Description Eng** | **Aggreation** | **Grouping** | **Filterig** | **Type** | **Value** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AuthUser | Авторизовал | Authorised by | false | true | true | STRING |  |
| Banquet | Банкет | Banquet | false | true | true | ENUM | TRUE<br>FALSE |
| Bonus.CardNumber | Номер бонусной карты | Bonus card number | false | true | true | STRING |  |
| Bonus.Sum | Сумма бонуса | Bonus amount | true | false | false | MONEY |  |
| Bonus.Type | Тип бонуса | Bonus type | false | true | true | STRING |  |
| Card | Карта авторизации | Authorisation card | false | true | true | STRING |  |
| CardNumber | Номер карты оплаты | Pay card type | false | true | true | STRING |  |
| CardOwner | Владелец карты гостя | Guest cardholder | false | true | true | STRING |  |
| CardType | Кредитная карта | Credit card | false | true | true | STRING |  |
| Cashier | Кассир | Cashier | false | true | true | STRING |  |
| CashLocation | Расположение кассы | Cash register location | false | true | true | STRING |  |
| CashRegisterName | Касса | Cash register | false | true | true | STRING |  |
| CloseTime | Время закрытия | Closing time | false | true | true | DATETIME |  |
| Comment | Комментарий к блюду | Item comment | false | true | true | STRING |  |
| Conception | Концепция | Concept | false | true | true | STRING |  |
| CookingPlace | Место приготовления | Production place | false | true | true | STRING |  |
| CreditUser | В кредит на... | Credited to... | false | true | true | STRING |  |
| DayOfWeekOpen | День недели | Day of week | false | true | true | STRING |  |
| DeletedWithWriteoff | Блюдо удалено | Item deleted | false | true | true | ENUM | Расшифровки кодов базовых типов#Типы удаления блюд |
| DeletionComment | Комментарий к удалению блюда | Item deletion comment | false | true | true | STRING |  |
| Delivery.IsDelivery | Доставка | Delivery | false | true | true | ENUM | Расшифровки кодов базовых типов#Признак доставки |
| Department | Торговое предприятие | Outlet | false | true | true | STRING |  |
| DiscountPercent | Процент скидки | Discount rate | true | true | true | PERCENT |  |
| DiscountSum | Сумма скидки | Discount amount | true | false | true | MONEY |  |
| discountWithoutVAT | Сумма скидки без НДС не включенного в стоимость | Discount amount excl. VAT not included in the cost | true | false | true | MONEY |  |
| DishAmountInt | Количество блюд | Number of items | true | true | true | AMOUNT |  |
| DishCategory | Категория блюда | Item category | false | true | true | STRING |  |
| DishCode | Код блюда | Item code | false | true | true | STRING |  |
| DishCode.Quick | Код быстрого набора блюда | Item quick code | false | true | true | STRING |  |
| DishDiscountSumInt | Сумма со скидкой | Amount with discount | true | false | false | MONEY |  |
| DishDiscountSumInt.average | Средняя сумма заказа | Average bill amount | true | false | false | MONEY |  |
| DishDiscountSumInt.averageByGuest | Средняя выручка с гостя | Average revenue per guest | true | false | false | MONEY |  |
| DishDiscountSumInt.averagePrice | Средняя цена без НДС | Average price (VAT exclusive) | true | false | false | MONEY |  |
| DishDiscountSumInt.withoutVAT | Сумма со скидкой без НДС | Amount with discount VAT exclusive | true | false | false | MONEY |  |
| DishForeignName | Наименование блюда на иностранном языке | Item name in a foreign language | false | true | true | STRING |  |
| DishFullName | Полное наименование блюда | Full name of the item | false | true | true | STRING |  |
| DishGroup | Группа блюда | Item group | false | true | true | STRING |  |
| DishGroup.Hierarchy | Иерархия блюда | Item hierarchy | false | true | true | STRING |  |
| DishGroup.Num | Код группы блюда | Item group code | false | true | true | STRING |  |
| DishGroup.SecondParent | Группа блюда 2-го уровня | Level 2 item group | false | true | true | STRING |  |
| DishGroup.ThirdParent | Группа блюда 3-го уровня | Level 3 item group | false | true | true | STRING |  |
| DishGroup.TopParent | Группа блюда 1-го уровня | Level 1 item group | false | true | true | STRING |  |
| DishMeasureUnit | Единица измерения | Measurement unit | false | true | true | STRING |  |
| DishName | Блюдо | Item | false | true | true | STRING |  |
| DishReturnSum | Сумма возврата | Void amount | true | true | true | MONEY |  |
| DishServicePrintTime | Сервисная печать блюда | Service printing item | false | true | true | DATETIME |  |
| DishServicePrintTime.Max | Сервисная печать последнего блюда | Service printing latest item | true | false | false | DATETIME |  |
| DishServicePrintTime.OpenToLastPrintDuration | Длит: откр.-посл.серв.печать | Duration: open latest serv. print. | true | false | false | INTEGER |  |
| DishSumInt | Сумма без скидки | Amount without discount | true | false | false | MONEY |  |
| DishType | Тип товара | Stock list type | false | true | true | ENUM | Расшифровки кодов базовых типов#Тип товара |
| fullSum | Сумма без НДС не включенного в стоимость | Amount excl. VAT not included in the cost | true | false | true | MONEY |  |
| GuestNum | Количество гостей | Number of guests | true | true | true | AMOUNT |  |
| GuestNum.Avg | Ср.кол-во гостей на чек | AvgNumber of guests per receipt | true | false | false | AMOUNT |  |
| HourClose | Час закрытия | Closing hour | false | true | true | STRING |  |
| HourOpen | Час открытия | Opening hour | false | true | true | STRING |  |
| IncentiveSumBase.Sum | Мотивационный бонус | Incentive payment | true | false | false | MONEY |  |
| IncreasePercent | Процент надбавки | Surcharge rate | true | true | true | PERCENT |  |
| IncreaseSum | Сумма надбавки | Surcharge amount | true | true | true | MONEY |  |
| JurName | Юридическое лицо | Legal entity | false | true | true | STRING |  |
| Mounth | Месяц | Month | false | true | true | STRING |  |
| NonCashPaymentType | Безналичный тип оплаты | Non-cash payment type | false | true | true | STRING |  |
| NonCashPaymentType.DocumentType | Тип документа | Document type | false | true | true | ENUM | Расшифровки кодов базовых типов#Тип документа |
| OpenDate (до версии 4.2; в 4.2+ deprecated, заменено на OpenDate.Typed) | Учетный день |  | false | true | true | STRING |  |
| OpenDate.Typed (4.2+) | Учетный день |  | false | true | true | DATE |  |
| OpenTime | Время открытия | Opening time | false | true | true | DATETIME |  |
| OperationType | Операция | Operation | false | true | true | ENUM | Расшифровки кодов базовых типов#Тип операции |
| OrderDeleted | Заказ удален | Order deleted | false | true | true | ENUM | Расшифровки кодов базовых типов#Признак удаления заказа |
| OrderDiscount.GuestCard | Гостевая карта | Guest card | false | true | true | STRING |  |
| OrderDiscount.Type | Тип скидки | Discount type | false | true | true | STRING |  |
| OrderIncrease.Type | Тип надбавки | Type of surcharge | false | true | true | STRING |  |
| OrderItems | Позиций чека | Order items | true | false | false | INTEGER |  |
| OrderNum | Номер чека | Receipt number | true | true | true | INTEGER |  |
| OrderTime.AverageOrderTime | Ср.время обсл.(мин) | AvgServing time (min) | true | false | false | AMOUNT |  |
| OrderTime.AveragePrechequeTime | Ср.время в пречеке (мин) | Avg time in guest bill (min) | true | false | false | AMOUNT |  |
| OrderTime.OrderLength | Время обслуживания (мин) | Serving time (min) | false | true | true | INTEGER |  |
| OrderTime.OrderLengthSum | Время обсл.сумм.(мин) | Serving time (min) | true | false | false | INTEGER |  |
| OrderTime.PrechequeLength | Время в пречеке (мин) | Time in guest bill (min) | false | true | true | INTEGER |  |
| OrderType | Тип заказа | Order type | false | true | true | STRING |  |
| OrderWaiter.Name | Официант заказа | Waiter for the order | false | true | true | STRING |  |
| OriginName | Источник заказа | Order origin | false | true | true | STRING |  |
| PayTypes | Тип оплаты | Payment type | false | true | true | STRING |  |
| PayTypes.Combo | Тип оплаты (комб.) | Payment type (comb.) | false | true | true | STRING |  |
| PayTypes.Group | Группа оплаты | Payment group | false | true | true | ENUM | Расшифровки кодов базовых типов#Группа оплаты |
| PayTypes.IsPrintCheque | Фиск. тип оплаты | Fisc. payment type | false | true | true | ENUM | Расшифровки кодов базовых типов#Признак фискальности оплаты |
| PayTypes.VoucherNum | Количество ваучеров | Number of vouchers | true | false | false | INTEGER |  |
| PercentOfSummary.ByCol | % по столбцу | % by column | true | false | false | PERCENT |  |
| PercentOfSummary.ByRow | % по строке | % by row | true | false | false | PERCENT |  |
| PrechequeTime | Время пречека | Guest bill time | false | true | true | DATETIME |  |
| PriceCategory | Ценовая категория клиента | Customer price category | false | true | true | STRING |  |
| PriceCategoryCard | ЦК номер карты | Price Category Card Number | false | true | true | STRING |  |
| PriceCategoryDiscountCardOwner | ЦК владелец карты | Price Category Cardholder | false | true | true | STRING |  |
| PriceCategoryUserCardOwner | ЦК контрагент | Price Category Card Owner | false | true | true | STRING |  |
| ProductCostBase.MarkUp | Наценка(%) | Markup (%) | true | false | false | PERCENT |  |
| ProductCostBase.OneItem | Себестоимость единицы | Cost per unit | true | false | false | MONEY |  |
| ProductCostBase.Percent | Себестоимость(%) | Cost(%) | true | false | false | PERCENT |  |
| ProductCostBase.ProductCost | Себестоимость | Cost | true | false | false | MONEY |  |
| ProductCostBase.Profit | Наценка | Markup | true | false | false | MONEY |  |
| RemovalType | Причина удаления блюда | Reason for item deletion | false | true | true | STRING |  |
| RestaurantSection | Отделение | Room | false | true | true | STRING |  |
| RestorauntGroup | Группа | Group | false | true | true | STRING |  |
| SessionNum | Номер смены | Shift number | false | true | true | INTEGER |  |
| SoldWithDish | Продано с блюдом | Sold with item | false | true | true | STRING |  |
| Store.Name | Со склада | From storage | false | true | true | STRING |  |
| StoreTo | На склад | To storage | false | true | true | STRING |  |
| Storned | Возврат чека | Void receipt | false | true | true | ENUM | TRUE<br>FALSE |
| sumAfterDiscountWithoutVAT | Сумма со скидкой без НДС не включенного в стоимость | Amount with discount excl. VAT not included in the cost | true | false | true | MONEY |  |
| TableNumInt (до 5.1; в 5.1+ заменено на TableNum) | Номер стола |  | false | true | true | STRING |  |
| TableNum (5.1+) | Номер стола |  | false | true | true | INTEGER |  |
| UniqOrderId | Чеков | Orders | true | false | false | INTEGER |  |
| UniqOrderId.OrdersCount | Заказов | Orders | true | false | false | AMOUNT |  |
| VAT.Percent | НДС(%) | VAT(%) | true | true | true | PERCENT |  |
| VAT.Sum | НДС по чекам(Сумма) | VAT by bill (Amount) | true | true | true | MONEY |  |
| WaiterName | Официант блюда | Item waiter | false | true | true | STRING |  |
| WriteoffReason | Причина списания | Write-off reason | false | true | true | STRING |  |
| WriteoffUser | Списано на сотрудника | Written off to employee | false | true | true | STRING |  |
| YearOpen | Год | Year | false | true | true | STRING |  |
 [+] [Описание полей OLAP отчета по контролю хранения](javascript:void%280%29)
 [-] [Описание полей OLAP отчета по контролю хранения](javascript:void%280%29)
 | Name | Description | Aggreation | Grouping | Type | Value |
| --- | --- | --- | --- | --- | --- |
| ProductNum | Артикул | false | true | STRING |  |
| ProductName | Блюдо | false | true | STRING |  |
| ProductAccountingCategory | Бухгалтерская категория блюда | false | true | STRING |  |
| EventDate | Дата | false | true | DATETIME |  |
| EventCookingDate | Дата и время приготовления | false | true | DATETIME |  |
| ProductMeasureUnit | Единицы измерения | false | true | STRING |  |
| ProductCategory | Категория блюда | false | true | STRING |  |
| Department.Code | Код подразделения | false | true | STRING |  |
| Amount | Количество | false | true | AMOUNT |  |
| ProductExpirationDuration | Просрочка на момент продажи | true | false | DATETIME |  |
| ProductCostBase.OneItem | Себестоимость единицы, р. | true | false | MONEY |  |
| ProductCostBase.ProductCost | Себестоимость, р. | true | false | MONEY |  |
| StoreFrom | Склад | false | true | STRING |  |
| User | Сотрудник | false | true | STRING |  |
| AccountTo | Счет | false | true | STRING |  |
| Event.Type | Тип события | false | true | STRING |  |
| Department | Торговое предприятие | false | true | STRING |  |


А вот подсказки по настройке получения данных о заказах через CLOUD API (IIKO Transport API)
* [Создание доставочного заказа](/articles/api-documentations/sozdanie-dostavochnogo-zakaza/a/h2_1050193778)
* [Немного про SourceKey](/articles/api-documentations/sozdanie-dostavochnogo-zakaza/a/h3_1741386113)
* [Работа со статусами](/articles/api-documentations/sozdanie-dostavochnogo-zakaza/a/h3__1706479435)
* [Схема работы](/articles/api-documentations/sozdanie-dostavochnogo-zakaza/a/h2__991776161)
* [Схема работы с отправкой заказа С автораспределением](/articles/api-documentations/sozdanie-dostavochnogo-zakaza/a/h3__1865005608)
* [Схема работы с отправкой заказа БЕЗ автораспределения](/articles/api-documentations/sozdanie-dostavochnogo-zakaza/a/h3__541222395)

Данная статья описывает API для создания доставочного заказа в системе iiko. С помощью этого инструмента пользователи могут автоматизировать процесс оформления заказов на доставку, интегрируя его с внешними системами и улучшая управление заказами в ресторане.

В документации методы для работы с доставочными заказами разделены на два блока [Deliveries: Create and update](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update) и [Deliveries: Retrieve](https://api-ru.iiko.services/docs#tag/Deliveries:-Retrieve)

## Создание доставочного заказа
Шаги для создания доставочного заказа:

1. [Авторизуйтесь](https://api-ru.iiko.services/docs#tag/Authorization), используя апи-логин, созданный при [подключении](/smart/project-api-documentation/connect-to-iiko-cloud).
2. Получите список [организаций](https://api-ru.iiko.services/docs#tag/Organizations/paths/~1api~11~1organizations/post) **/api/1/organizations** для заданного апи-логина. При *returnAdditionalInfo: true* в ответе также вернется актуальная версия вашего РМС.
3. Получите список [терминалов](https://api-ru.iiko.services/docs#tag/Terminal-groups/paths/~1api~11~1terminal_groups/post) доставки в организации **/api/1/terminal\_groups**. Так как iikoCloud API работает напрямую с фронтом, передача терминала обязательна при отключенной функции автораспределения заказов.
4. Получите [список](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~12~1menu/post)внешних меню и введенных в него [позиций](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~12~1menu~1by_id/post).
5. Вы также можете проверить актуальный список позиций, находящихся в[стоп листе](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~11~1stop_lists/post) **/api/1/stop\_lists**.
6. Получите [типы оплат](https://api-ru.iiko.services/docs#tag/Dictionaries/paths/~1api~11~1payment_types/post) **/api/1/payment\_types**. Типы оплат должны быть заранее [настроены](/smart/project-iikooffice/topic-103) в iikoOffice.
7. Настройте и выгрузите в API [города и улицы](/smart/project-api-documentation/cities-streets).
8. Выполните [запрос](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) **/api/1/deliveries/create.**

### Немного про SourceKey
Источник заказа работает в 2 стороны. Если его задать у апи-логина, то заказы, созданные через данный апи-логин будут получать именно данный источник.
С другой стороны, если он задан, то он работает и как фильтр (заказы, имеющие другое значение в поле источник) не будут доступны в API для данного апи-логина.
Другими словами, поле "источник" нужно, чтобы ограничить видимость заказов для внешней интеграции (например для DC, который должен видеть только свои заказы).
В остальных случаях источник **указывать не надо**.

### Работа со статусами

После отправки заказа в iikoCloud API ему может присвоиться один из следующих статусов:
* **Success** - приходит, когда фронт ответил успехом на создание;
* **Error** - когда фронт ответил ошибкой на создание;
* **InProgress** - во всех остальных случаях, то есть когда мы не получили ответ от фронта. Другими словами - мы "ожидаем" от фронта ответы всегда.

**TransportToFrontTimeOut** - это время, в течение которого, iikoCloud API должен попробовать создать заказ, т.е. достучаться до фронта. Им можно регулировать время, которое заказ будет находиться в очереди на создание заказа, и когда таск будет сниматься из нее.
**Front,** или касса, с определенной периодичностью отстукивается в iikoCloud API, давая знать, что точка активна и может принимать заказы.
Статус создания заказа, как и успешность любого другого запроса рекомендуется проверять методом /api/1/commands/status (с версии 7.7.6) и /api/1/deliveries/by\_id (для более ранних версий).

##  Схема работы

###  Схема работы с отправкой заказа С автораспределением

1. Проверка доступных и подходящих под ГРиК точек методом **/api/1/delivery\_restrictions/allowed**
2. Возврат списка подходящих точек и условий. Если подходящей точки нет, заказ создавать нельзя. Если подходящая точка есть - начало создания заказа методом **/api/1/deliveries/create**
3. Если фронт доступен все время:
    * За отведенное в **TransportToFrontTimeOut**время, iikoCloud API пытается достичь фронта и создать заказ. В это время заказ находится в статусе **inProgress**
    * Фронт принимает заказ, т.е. отвечает успехом - статус в iikoCloud APIе сменяется на **Success,**либо фронт отклоняет заказ, тогда статус в трн сменяется на **Error**
4. Если фронт работал штатно, но ко времени создания заказа стал недоступен и так и не вышел на связь:
    * За отведенное в **TransportToFrontTimeOut**время, iikoCloud API пытается достичь фронта и создать заказ. В это время заказ находится в статусе **inProgress**
    * Отведенное время завершилось, к отведенному времени прибавляется еще 1 минуты, и после этого статус переходит в **Error.**Необходимо отменить заказ или создать заказ через альтернативный канал.

    5. Если фронт был на связи во время создания заказа, успел его принять, но затем ушел в оффлайн (нет связи с фронтом какое-то время), а затем снова вернулся к сети:

    * За отведенное в **TransportToFrontTimeOut**время, iikoCloud API пытается достичь фронта и создать заказ. В это время заказ находится в статусе **inProgress**
    * Отведенное время завершилось, к отведенному времени прибавляется еще 1 минуты, и после этого статус переходит в **Error.**Необходимо отменить заказ или создать заказ через альтернативный канал.
    * Фронт в итоге выходит на связь и принимает заказ, т.е. отвечает успехом - статус в iikoCloud APIе сменяется на **Success,**либо фронт отклоняет заказ, тогда статус в трн сменяется на **Error**
    * iikoCloud API отсылает вебхук об изменении статуса заказа с **inProgress**на **Success.**Вебхук должен быть заранее настроен согласно [документации](https://api-ru.iiko.services/docs#tag/WebHooks/paths/~1api~11~1webhooks~1settings/post)
    * Ресторан получает заказ, который был отменен гостю в п.2.
    * Необходимо отменить заказ методом **/api/1/deliveries/cancel**
    * При успешной отмене заказ удаляется с фронта.

### Схема работы с отправкой заказа БЕЗ автораспределения

Это срочные заказы, отправляются на конкретную точку с указанием в теле **terminalGroupId**

1. Проверка доступности точки. Происходит ДО создания заказа методом **/api/1/terminal\_groups/is\_alive**
2. Если точка недоступна - заказ создавать нельзя. Если точка доступна - начало создания заказа **/api/1/deliveries/create**
3. Если фронт доступен все время:
    * За отведенное в **TransportToFrontTimeOut**время, iikoCloud API пытается достичь фронта и создать заказ. В это время заказ находится в статусе **inProgress**
    * Фронт принимает заказ, т.е. отвечает успехом - статус в iikoCloud APIе сменяется на **Success,**либо фронт отклоняет заказ, тогда статус в трн сменяется на **Error**
4. Если фронт работал штатно, но ко времени создания заказа стал недоступен и так и не вышел на связь:
    * За отведенное в **TransportToFrontTimeOut**время, iikoCloud API пытается достичь фронта и создать заказ. В это время заказ находится в статусе **inProgress**
    * Отведенное время завершилось, к отведенному времени прибавляется еще 1 минуты, и после этого статус переходит в **Error.**Необходимо отменить заказ или создать заказ через альтернативный канал.

    5. Если фронт был на связи во время создания заказа, успел его принять, но затем ушел в оффлайн (нет связи с фронтом какое-то время), а затем снова вернулся к сети:

    * За отведенное в **TransportToFrontTimeOut**время, iikoCloud API пытается достичь фронта и создать заказ. В это время заказ находится в статусе **inProgress**
    * Отведенное время завершилось, к отведенному времени прибавляется еще 1 минуты, и после этого статус переходит в **Error.**Необходимо отменить заказ или создать заказ через альтернативный канал.
    * Фронт в итоге выходит на связь и принимает заказ, т.е. отвечает успехом - статус в iikoCloud APIе сменяется на **Success,**либо фронт отклоняет заказ, тогда статус в трн сменяется на **Error**
    * iikoCloud API отсылает вебхук об изменении статуса заказа с **Error**на **Success.** Вебхук должен быть заранее настроен согласно [документации](https://api-ru.iiko.services/docs#tag/WebHooks/paths/~1api~11~1webhooks~1settings/post)
    * Ресторан получает заказ, который был отменен гостю в п.2.
    * Необходимо отменить заказ методом **/api/1/deliveries/cancel**
    * При успешной отмене заказ удаляется с фронта.
	
	* [Методы для работы с заказами на стол](/articles/api-documentations/rabota-s-zakazom-na-stol/a/h2_1962164077)
* [Работа с QR кодами на столе](/articles/api-documentations/rabota-s-zakazom-na-stol/a/h2__991776161)
* [Что необходимо](/articles/api-documentations/rabota-s-zakazom-na-stol/a/h3__1865005608)
* [Описание процесса работы с QR-кодами и действий гостя в ресторане](/articles/api-documentations/rabota-s-zakazom-na-stol/a/h3__541222395)
* [Примечание](/articles/api-documentations/rabota-s-zakazom-na-stol/a/h3__81553844)

В iikoCloud API существует блок методов, позволяющих работать с заказами в стол (создание заказа по QR-коду со стола в заведении). Методы для заказов в стол отличны от методов для работы с доставками, и находятся в блоке [Orders](https://api-ru.iiko.services/docs#tag/Orders).

##  Методы для работы с заказами на стол

1. [Метод](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1create/post) создания ресторанного заказа в стол.
2. [Метод](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1by_id/post) поиска заказа по его идентификатору. Возможно только для заказов, созданных через API, или заказов, попавших в API после вызова метода из пункта 7.
3. [Метод](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1by_table/post) поиска заказа по номеру стола. Возможно только для заказов, созданных через API, или заказов, попавших в API после вызова метода из пункта 7.
4. [Добавление](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1add_items/post) позиции в заказ.
5. [Закрытие](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1close/post) заказа. Возможно только, если заказ оплачен. Платеж можно передать как сразу в создании заказа, так и добавить позже через вызов метода в пункте 6.
6. [Изменение](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1change_payments/post) платежа заказа. На данный момент нельзя добавить в заказ более одного платежа.
7. [Метод](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1init_by_table/post), позволяющий протолкнуть заказы в стол, созданные на фронте, в API. Если заказы были созданы не через API iikoCloud, а через кассу или другим путем, то автоматически такие заказы не отображаются в API. Чтобы они там отобразились, нужно вызвать данный метод. Данный метод будет работать только в том случае, если заказ не закрыт в iikoFront.

В данной статье описан основной сценарий использования методов АПИ для реализации пользовательских приложений об оплате и создание заказов внутри ресторана.

## Работа с QR кодами на столе

###  Что необходимо 

Необходимые лицензии для работы: iikoCloud API-входит в состав тарифов iikoCloud, для LT необходимо приобретать [iikoCloud API](/smart/project-iikoweb/iikocloudapi).

###  Описание процесса работы с QR-кодами и действий гостя в ресторане 

* QR код наклеивается на каждый стол в ресторане,

* В QR код может содержаться следующая информация: id ресторана, id зала, id стола - эти данные могут потребоваться приложению для четкого позиционированию в ресторане.

* Гость приходит в ресторан, считывает QR и попадает в приложение, где он может просмотреть меню и сделать заказ или так же после просмотра меню позвать официанта и сделать заказ через него.
* После оформления заказа (гость может в любой момент произвести полную оплату заказа) в приложения заказа уходит на фронт и сразу начинает готовиться. Также гость может просмотреть статус своего заказа в приложении.

![](/resources/Storage/api-documentations/rabota-s-zakazom-na-stol/rabota-s-zakazom-na-stol-2025-03-21.png)

**Ссылка на схему в [Miro](https://miro.com/app/board/uXjVOJM3MU8=/?invite_link_id=116382572391)**

Шаги при работе с заказом на стол по QR-коду:
1. Получить [список организаций](https://api-ru.iiko.services/docs#tag/Organizations),

2. Получить [список терминалов](https://api-ru.iiko.services/docs#tag/Terminal-groups),

3. Получить [список внешних меню](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~12~1menu/post) и [доступных позиций](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~12~1menu~1by_id/post),

4. Создать [заказ на стол](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1create/post),

5. Получить [список типов оплат](https://api-ru.iiko.services/docs#tag/Dictionaries/paths/~1api~11~1payment_types/post),

6. [Найти заказ для оплаты](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1by_id/post),

7. [Оплата заказа](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1close/post).

###  Примечание 

Заказы в стол, оформленные в iikoFront, можно получить только через API.Front. Для этого необходимо реализовать плагин на C#.

Ниже вы найдете ссылки на документацию и примеры

[https://iiko.github.io/front.api.doc/](https://iiko.github.io/front.api.doc/)

[https://github.com/iiko/front.api.sdk/tree/master/sample](https://github.com/iiko/front.api.sdk/tree/master/sample)

Ближайшее время данный функционал будет реализован и в iikoCloud API.

* [Схема модификаторов](/articles/api-documentations/rabota-s-modifikatorami-v-cloud-api/a/h2_255748801)
* [Пример настройки схемы модификаторов и работа по API](/articles/api-documentations/rabota-s-modifikatorami-v-cloud-api/a/h3__1794990131)
* [Пример 1 - блюдо не делится](/articles/api-documentations/rabota-s-modifikatorami-v-cloud-api/a/h3__840635112)
* [Вариант 2 - блюдо делится и содержит разный набор модификаторов в каждой половинке](/articles/api-documentations/rabota-s-modifikatorami-v-cloud-api/a/h3__1076123057)

В данной статье описывается работа с модификаторами в API iikoCloud. Этот функционал позволяет гибко управлять настройками модификаций товаров в заказах, таких как добавление ингредиентов или выбор опций, обеспечивая удобное и эффективное взаимодействие с внешними приложениями и улучшая процесс обслуживания клиентов в ресторане.

# Работа с модификаторами

#### Работа с одиночным модификатором 
![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-iikocloud-api/rabota-s-modifikatorami-v-iikocloud-api-2024-07-22.png)

Модификатор может иметь следующие параметры:

* **Максимальное и минимальное количество**. По умолчанию для каждого из модификаторов определено, что минимальное их количество – 0 (то есть он является необязательным), максимальное – 1. Чтобы изменить эти границы введите нужное значение в колонки **Мин**и **Макс**.
* **Признак «По умолчанию»**. Вы можете указать модификаторы, которые всегда будут добавляться в заказ вместе с блюдом. Для этого напротив нужной позиции в колонке **По умолчанию**введите количество таких модификаторов. У простых модификаторов эта величина должна быть больше или равна значению в поле **Мин**, и меньше или равно значению в поле **Макс**. Для групповых модификаторов количество по умолчанию задается для каждого элемента группы отдельно, а минимальное количество – для всей группы. Поэтому значение по умолчанию для отдельной позиции может быть меньше минимума и даже нулевым.
* **Признак «Обязательный»**. Поле **Обязательный**взаимосвязано с полем **Мин**. Если в поле **Мин**задать значение больше нуля, то он становится обязательным, в поле **Обязательный**напротив него появится галочка. И наоборот: если установить галочку **Обязательный**, то поле **Мин**примет значение по умолчанию – 1, но вы можете его изменить. Обязательный модификатор добавляется в заказ вместе с блюдом автоматически в количестве, указанном в колонке **По умолчанию**.
* Признак **Скрывать, если кол-во по умолчанию**. При включении параметра модификатор, если он был добавлен в заказ в количестве, указанном по умолчанию, не будет печататься на сервисном чеке и отображаться на Кухонном экране. Иными словами, повар всегда будет готовить блюдо с этим модификатором в количестве по умолчанию, если в заказе не указано иное. Если же в заказе указано, что к блюду не нужно добавлять этот модификатор, то он будет отпечатан в сервисном чеке и на Кухонном экране и его количество будет равно 0, чтобы повар знал, что блюдо нужно готовить без данного модификатора.
* В блоке **Дополнительно** в **Общих настройках** торгового предприятия можно включить параметр **Отображать относительное количество модификаторов**. Данный режим отображения может быть полезен сотрудникам, которые хорошо знают технологическую карту и помнят количество порций модификаторов по ней — тогда им достаточно будет знать лишь то количество модификаторов, которое гость попросил добавить или убрать — относительное количество. Если настройка включена, модификаторы сопровождаются знаком «плюс» (+) или «минус» (-) кроме платных модификаторов, количество которых всегда отображается со знаком умножения (х).
* **Ограничения на минимум у дочерних модификаторов**. По умолчанию для группового модификатора минимальные и максимальные значения, а также признак «Бесплатные», должны указываться для всей группы. Чтобы была возможность устанавливать такие ограничения отдельно для каждого модификатора внутри группы, установите галочку **Ограничения на минимум у дочерних модификаторов**. При этом максимальные значения и количество бесплатных модификаторов в каждой строке будут установлены такие же, какие были у группы, но вы можете их отредактировать.
* **Бесплатный**. В колонке **Бесплатные**вы можете указать количество модификаторов, которые не будут увеличивать стоимость блюда при добавлении его в заказ.. Эта величина должна быть меньше или равна значению, указанному в поле **Макс**. У группового модификатора значение указывается для всей группы, т. е. суммарное количество модификаторов группы при формировании заказа не должно превышать это значение. Если в заказ добавляется несколько модификаторов из группы, то бесплатным будет самый дорогой из них.

 [+] [Пример запроса №1](javascript:void%280%29)
 [-] [Пример запроса №1](javascript:void%280%29)
 
```
 меню по запросу /api/2/menu/by_id
%%CH%PRE0%% 
```

 [+] [Пример запроса №2](javascript:void%280%29)
 [-] [Пример запроса №2](javascript:void%280%29)
 
```
 Используется одиночный модификатор со следующими настройками в iiko: 
%%CH%PRE1%% 
```

 [+] [Пример запроса №3](javascript:void%280%29)
 [-] [Пример запроса №3](javascript:void%280%29)
 
```
 В данном примере показано как передавать модификатор со следующими настройками 
Мин=1 - это означает, что необходимо передать как минимум один модификатор, 
По умолчанию - указывает, что данный модификатор всегда необходимо добавлять в заказ вместе с блюдом. 
В данном случае необходимо добавить один модификатор. 
Макс - это означает максимальное количество модификаторов, которое можно передать в запросе. 


%%CH%PRE2%% 
```

 
Подробное описание модификаторов можно прочитать в статье [Модификаторы](/articles/iikooffice-9-1/topic-3100).

## Схема модификаторов

Основная статья по работе со [схемой модификаторов](/articles/iikooffice-9-0/topic-224)

Для работы со схемой модификаторов имеется три переменные primaryComponent, secondaryComponent, commonModifiers и тип "Compound".

* primaryComponent - "главный" компонент в структуре, заполняется id самого блюда и модификаторов (если блюдо делится, то выводится блюдо и половинка модификатора);
* secondaryComponent - также передает id блюда и половинку модификаторов. Если блюдо не делится, параметр не заполняется.
* commonModifiers - передает неделимые части заказа.

Данные схемы модификаторов можно получить, пользуясь методом для работы с внешним меню [/api/2/menu/by_id](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~12~1menu~1by_id/post).
Признак разделения блюда и модификатора называется одинаково, разница только в уровне вывода информации: на уровне блюда и модификатора. Переменная, отвечающая за признак разделения блюда и модификатора, называется **canBeDivided**.

Сейчас у переменной canBeDivided есть особенности:
- поддерживается работа на уровне групповых модификаторов, то есть, если в схеме указан признак разделения группового модификатора, то в ответе на запрос выйдет canBeDivided: true на уровне вывода информации группового модификатора.
- если в схеме установлен одиночный модификатор, то выведется false.

| ![Warning](/resources/Storage/api-documentations/api-documentations/warning.png) | Разделение одиночных модификаторов в схеме модификаторов не поддерживается. |
| --- | --- |

Ниже приведен пример ответа на вызов метода получения внешнего меню со схемой модификаторов [/api/2/menu/by_id](https://api-ru.iiko.services/docs#tag/Menu/paths/~1api~12~1menu~1by_id/post) (пример "Пицца половинки", описанного ниже). Добавлены комментарии к переменной canBeDivided:
 [+] [Пример ответа](javascript:void%280%29)
 [-] [Пример ответа](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

 
### Пример настройки схемы модификаторов и работа по API

Рассмотрим пример настройки схемы модификаторов для блюда "Пицца половинки". Данное блюдо можно разделить на части и дополнить каждую часть своим набором модификаторов.

Группы модификаторов "Овощи" и "Соус" могут быть разделены. Группа "Тип теста" - неделимый модификатор.

Общий вид схемы для данной пиццы:

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-1.png)

В разделе "Шкала размеров" приведены размеры пиццы:

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-2.png)

Если открыть данное блюдо на iikoFront, то получим следующий вид:

слева размещаются неделимые модификаторы и шкала размеров: размеры пиццы и типы теста,

в центральной части делимые: овощи и соус.

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-3.png)

### Пример 1 - блюдо не делится

Выбраны **неделимые параметры**размер пиццы S (30 см), тонкое тесто, а также **без деления** томатный соус и начинки шпинат и помидоры.

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-4.png)

После подтверждения состава пиццы можно увидеть как выглядит данный вариант в списке заказа:

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-5.png)

Ниже приведен пример заполнения items для передачи такого же результата как на iikoFront выше (рассматриваем метод создания доставки api/1/deliveries/create).

В данном случае primaryComponent работает как главное звено и содержит id блюда и модификаторы,

secondaryComponent не заполняется, так как блюдо не делится, commonModifiers - заполняется неделимым модификатором.


```json
        "items": [
            {
                "primaryComponent": {
                    "productId": "5bb9a8ce-114e-4617-b8d4-1eac73a0b2f7", //id Пицца половинки
                    "modifiers": [
                        {
                            "productId": "7d0b238b-6e88-47d1-98d8-21254425497d", // помидоры
                            "productGroupId": "6728e164-81a3-47de-a3cf-5a258ef9efe9", // группа Овощи
                            "price": 50,
                            "amount": 1
                        },
                        {
                            "productId": "dec5927b-64bf-481b-8008-c25c5235ac1d", // соус шпинат
                            "productGroupId": "6728e164-81a3-47de-a3cf-5a258ef9efe9", //группа Овощи
                            "price": 50,
                            "amount": 1
                        },
                        {
                            "productId": "c14d73f3-7f65-465a-885f-446999032694", // томатный соус
                            "productGroupId": "5f129433-de0a-46f8-a239-30a6d1169a2f", // группа Соус
                            "price": 50,
                            "amount": 1
                        }
                    ],
                    "price": 1500.0, // цена пиццы
                    "positionId": null
                },
                "secondaryComponent": null, // блюдо не делится, этот параметр пропускается
                "commonModifiers": [
                    {
                        "productId": "c9319e1e-ba6b-4970-b392-c0c667508dc7", // тонкое тесто
                        "productGroupId": "48179386-a8fa-453f-b69a-3031db329af6", // группа Тип теста
                        "price": 0,
                        "amount": 1
                    }
                ],
                "type": "Compound",
                "amount": 1,
                "productSizeId": "2a86b1a8-e093-4e74-b533-ba1f7e2aa14c" // размер пиццы S(30 см)
            }
        ],

```


На iikoFront информация придет в следующем виде. Успех!

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-6.png)

### Вариант 2 - блюдо делится и содержит разный набор модификаторов в каждой половинке

На iikoFront это выглядит следующим образом:

Выбраны **неделимые параметры**размер пиццы S (30 см), тонкое тесто,

а также **разделили** пиццу на половинки и получили два набора модификаторов с каждой стороны: 1) помидоры, шпинат и томатный соус, 2) маслины, шампиньоны и белый соус.

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-7.png)

Список позиций заказа выглядит так:

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-8.png)

Ниже приведен пример заполнения items для передачи такого же результата как на iikoFront выше (рассматриваем метод создания доставки api/1/deliveries/create).

В данном случае primaryComponent и secondaryComponent содержат id блюда и модификаторы, commonModifiers - заполняется неделимым модификатором.


```json
        "items": [
            {
                "primaryComponent": {
                    "productId": "5bb9a8ce-114e-4617-b8d4-1eac73a0b2f7", //id Пицца половинки 
                    "modifiers": [
                        {
                            "productId": "7d0b238b-6e88-47d1-98d8-21254425497d", // помидоры
                            "productGroupId": "6728e164-81a3-47de-a3cf-5a258ef9efe9", // группа Овощи
                            "price": 50,
                            "amount": 1
                        },
                        {
                            "productId": "dec5927b-64bf-481b-8008-c25c5235ac1d", // соус шпинат
                            "productGroupId": "6728e164-81a3-47de-a3cf-5a258ef9efe9", //группа Овощи
                            "price": 50,
                            "amount": 1
                        },
                        {
                            "productId": "c14d73f3-7f65-465a-885f-446999032694", // томатный соус
                            "productGroupId": "5f129433-de0a-46f8-a239-30a6d1169a2f", // группа Соус
                            "price": 50,
                            "amount": 1
                        }
                    ],
                    "price": 1500.0, // цена пиццы
                    "positionId": null
                },
                "secondaryComponent": {
                    "productId": "5bb9a8ce-114e-4617-b8d4-1eac73a0b2f7", //id Пицца половинки
                    "modifiers": [
                        {
                            "productId": "7b889243-ebfd-4e73-910b-f94e087a6fbb", //маслины
                            "productGroupId": "6728e164-81a3-47de-a3cf-5a258ef9efe9", // группа Овощи
                            "price": 50,
                            "amount": 1
                        },
                        {
                            "productId": "daffc06c-8db3-462c-8436-53b53c7a1fed", // шампиньоны
                            "productGroupId": "6728e164-81a3-47de-a3cf-5a258ef9efe9", // группа Овощи
                            "price": 50,
                            "amount": 1
                        },
                        {
                            "productId": "a6e13d5c-74e3-4acc-a894-df6edc71b340", // белый соус
                            "productGroupId": "5f129433-de0a-46f8-a239-30a6d1169a2f", // группа Соус
                            "price": 50,
                            "amount": 1
                        }
                    ],
                    "price": 1500.0,
                    "positionId": null
                },
                "commonModifiers": [
                    {
                        "productId": "c9319e1e-ba6b-4970-b392-c0c667508dc7", // тонкое тесто
                        "productGroupId": "48179386-a8fa-453f-b69a-3031db329af6", // группа Тип теста
                        "price": 0,
                        "amount": 1
                    }
                ],
                "type": "Compound",
                "amount": 1,
                "productSizeId": "2a86b1a8-e093-4e74-b533-ba1f7e2aa14c" // размер пиццы S(30 см)
            }
        ]
    },

```


Результат:

![](/resources/Storage/api-documentations/rabota-s-modifikatorami-v-cloud-api/rabota-s-modifikatorami-v-cloud-api-2025-06-27-9.png)

Статья на сайте iiko описывает API для работы с холдированием (предварительным резервированием) бонусов в системе.
Работа с холдированием через Cloud API

Для того, чтобы начать работать с холдированием, необходимо произвести первоначальные настройки. Для этого нужно в маркетинговых программ поставить галочку "разрешать холдирование" и так же нужно создать дополнительный тип оплат и сопоставить маркетинговые акции. Подробное описание, как создавать маркетинговые программы, описаны в статье/articles/iikocard/topic-10/q/%2525252525252525252525D0%2525252525252525252525A5%2525252525252525252525D0%2525252525252525252525BE%2525252525252525252525D0%2525252525252525252525BB%2525252525252525252525D0%2525252525252525252525B4%2525252525252525252525D0%2525252525252525252525B8%2525252525252525252525D1%252525252525252525252580%2525252525252525252525D0%2525252525252525252525BE%2525252525252525252525D0%2525252525252525252525B2%2525252525252525252525D0%2525252525252525252525B0%2525252525252525252525D0%2525252525252525252525BD%2525252525252525252525D0%2525252525252525252525B8%2525252525252525252525D0%2525252525252525252525B5%252525252525252525252520/qid/2377546/qp/1[Акции](/smart/project-iikocard/topic-10/a/h2_0)

В настройках маркетинговой акции появился чек-бокс "Разрешить холдирование при онлайн оплате", которая позволяет заранее "заморозить" n-ную сумму денег на кошельке гостя через методы api.

1. Создаем программу для работы с холдированием. В программе создаем одну-единственную маркетинговую акцию , включаем у нее холдирование, добавляем действие оплаты.

2. В iikoOffice настраиваем тип оплаты с холдированием: получаем доступные маркетинговые акции , в списке будет маркетинговая акция (холдирование)". Ставим галочку "запрещать вводить вручную" и указываем, что может приниматься извне. Тип оплаты с холдированием в RMS должен содержать только одну маркетинговую акцию

**Для создания заказа через api**

1. Получаем доступные [типы оплат](https://api-ru.iiko.services/docs#tag/Dictionaries/paths/~1api~11~1payment_types/post).

2. Получаем [лояльность]( https://api-ru.iiko.services/docs#tag/Discounts-and-promotions/paths/~1api~11~1loyalty~1iiko~1calculate/post ) для заказа, с учетом нужной нам маркетинговой акции, с указанием маркетинговой акции в availablePaymentMarketingCampaignIds в теле запроса.

![](/resources/Storage/api-documentations/kholdirovanie/kholdirovanie-2024-03-19.png)

3. В ответе calculate\_checkin в availablePayments в id - указывается маркетинговая акция для оплаты (по нему можно сопоставить тип оплаты ), в walletInfos -&gt; id - id кошелька для оплаты (для холдирования средств).

4. Холдируем средства на кошельке гостя и создаем заказ [методом](https://api-ru.iiko.services/docs#tag/Customers/paths/~1api~11~1loyalty~1iiko~1customer~1wallet~1hold/post). 
5. В ответе придет id созданной транзакции холдирования, которую можно будет использовать [для отмены холдирования](https://api-ru.iiko.services/docs#tag/Customers/paths/~1api~11~1loyalty~1iiko~1customer~1wallet~1cancel_hold/post), если заказ будет отменен/возникнет ошибка при создании. После отмены в "журнале транзакций" появится транзакция "Отмена холдирования средств".
6. Создаем заказ, в теле запроса в payments указываем нужный тип оплаты (созданный для холдирования) и сумму, которая была захолдирована

**В iikoFront создается доставка**

Закрываем доставку, при этом с кошелька гостя на Pos-Server сумма холдирования не списывается, т.к. она была списана ранее на сервере iikoCard, при вызове [метода](https://api-ru.iiko.services/docs#tag/Customers/paths/~1api~11~1loyalty~1iiko~1customer~1wallet~1hold/post).

После синхронизации Pos-Server с iikoBiz, если в iikoBiz нашлась свободная транзакция холдирования (Холдирование средств) на ту же сумму, которая была в оплате методом холдирования в заказе (транзакция "Холдирование средств из заказа"), то они сопоставятся и деньги с кошелька на сервере iikoCard не списываются. Если нужной транзакции не нашлось, то будет списание средств из кошелька.

****

* [Общее описание работы метода создания заказа](/articles/api-documentations/obschie-printsipy-sozdaniya-zakaza-na-stol-i-na-dostavku/a/h2__13654055)
* [Порядок действий интеграции при создании заказа](/articles/api-documentations/obschie-printsipy-sozdaniya-zakaza-na-stol-i-na-dostavku/a/h2__371861471)
* [Ограничения перевода статуса оплат](/articles/api-documentations/obschie-printsipy-sozdaniya-zakaza-na-stol-i-na-dostavku/a/h2_458020796)

В статье описывается, как работает метод создания доставочного заказа [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) и как интеграция должна использовать этот метод и обрабатывать получаемые при его работе ошибки. Все написанное также верно для метода создания заказа в стол [/api/1/order/create](https://api-ru.iiko.services/docs#tag/Orders/paths/~1api~11~1order~1create/post).

## Общее описание работы метода создания заказа

При вызове метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) происходит предварительная валидация запроса. Если валидация не была успешной (например, не переданы или переданы неверно какие-то обязательные параметры создания заказа), то метод сразу возвращает ошибку (http 400 или какую-то иную; описание ошибки содержится в body ответа в поле ErrorInfo) и прерывает работу.

Если валидация была успешной, то заказ сохраняется в базу CloudApi и отправляется на кассу. Метод возвращает успешный статус 200 и ответ, в котором содержится id нового заказа, а также поле creationStatus со значением InProgress. После этого метод также завершает работу. Ответ http 200 метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) означает только то, что заказ был сохранён в базе CloudApi и отправлен на кассу. Но пока неизвестно, был ли он успешно доставлен на кассу и фактически создан там или нет.

Возможные проблемы, из-за которых заказ может быть не создан на кассе:

* неверные параметры заказа. Часть параметров валидируется сразу при вызове метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post), а часть - только на самой кассе. Т.е. возможна ситуация, когда заказ успешно доставляется до кассы, но там не создаётся из-за неуспешной валидации.
* проблемы со связью между кассой и CloudApi

Таким образом, интеграция не должна полагаться только на успешность выполнения метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post), т.к. это ещё не гарантирует, что заказ был фактически создан. После вызова метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) заказа интеграция обязана проверять успешность создания заказа одним из нижеописанных способов.

## Порядок действий интеграции при создании заказа

1. Вызвать метод [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post).

2. Проверить результат выполнения метода. Возможные результаты выполнения метода:

* Заказ был успешно сохранён в базе CloudApi и отправлен во фронт. Метод возвращает http-статус 200 и ответ, в котором есть поле id, содержащее идентификатор нового заказа, и поле creationStatus = InProgress, показывающее, что заказ находится в процессе доставки до фронта.
* Были ошибки при предварительной валидации заказа:
    * http-статус 200 в случае некоторых ошибок предварительной валидации, например, в запросе указан идентификатор несуществующей терминальной группы. В этом случае в ответе будет поле creationStatus = Error. То, что статус 200 используется для неуспешных запросов, обусловлено историческими причинами. Исправить это поведение затруднительно, т.к. оно уже является частью публичного API;
    * http-статус 400 и описание ошибки в запросе, из-за которой он не был выполнен (например, в запросе не хватает каких-то обязательных полей);
    * http-статус 401 - в заголовке Authorization указан неверны/истёкший токен, или апи-логин, от которого вызывается запрос, был заблокирован;
    * http-статус 402 - срок действия лицензии CloudApi истёк;
    * http-статус 403 и описание ошибки, из-за которой запрос не был выполнен, например, попытка создать заказ в организацию, которая не привязана к апи-логину или попытка создать заказ с блюдом, которое находится в стоп-листе (только при заданном параметре CheckStopList = true в теле запроса);
* Произошли другие типы ошибок:
    * 500 - внутренняя ошибка CloudApi,
    * 408 - метод выполнялся слишком долго и упал по таймауту,
    * 429 - метод создания заказа вызывается слишком часто.

3. Если вызов метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) завершился ошибкой, интеграция должна её обработать (уведомить пользователя о том, что заказ не был создан, и разработчиков интеграции, чтобы они выяснили и устранили причину ошибки). Интеграция не должна бесконечно пытаться вызывать один и тот же ошибочный запрос, т.к. он будет заканчиваться той же ошибкой, а интеграция при таком поведении будет заблокирована.

4. Если метод [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) выполнился успешно, т.е. вернул http-статус 200 и creationStatus = InProgress, интеграция должна проверять успешность (или неуспешность) фактического создания заказа на кассе, т.е. дождаться момента, когда creationStatus перейдёт из InProgress либо в Success, либо в Error. Для проверки можно использовать один из следующих способов:

* (рекомендуется) Через веб-хуки. При успешном (или неуспешном) создании заказа будет отправлен веб-хук, который должна получить и обработать интеграция. В веб-хуке будет содержаться информация о созданном заказе и поле creationStatus = Success (в случае успешного создания заказа на кассе), или информация об ошибке и поле creationStatus = Error (в случае неуспешного создания заказа на кассе).
* (рекомендуется) Периодический вызов метода [/api/1/commands/status](https://api-ru.iiko.services/docs#tag/Operations/paths/~1api~11~1commands~1status/post). Не следует вызывать метод слишком часто (раз в 2-5 секунд; чаще не стоит). Этот метод получает на вход correlationId, который вернул метод [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post), и возвращает поле state, которое содержит значение InProgress, пока заказ создаётся во фронте. В какой-то момент в поле state окажется значение Success или Error (соответственно при успешном и неуспешном создании заказа во фронте). При получении одного из статусов Success или Error интеграция должна прекратить вызывать метод [/api/1/commands/status](https://api-ru.iiko.services/docs#tag/Operations/paths/~1api~11~1commands~1status/post). Можно однократно вызывать метод [/api/1/deliveries/by_id](https://api-ru.iiko.services/docs#tag/Deliveries:-Retrieve/paths/~1api~11~1deliveries~1by_id/post) для получения информации об успешно созданном заказе или о причинах ошибки при неуспешном создании
* (рекомендуется) Периодический вызов метода [/api/1/deliveries/by_revision](https://api-ru.iiko.services/docs#tag/Deliveries:-Retrieve/paths/~1api~11~1deliveries~1by_revision/post). Этот метод получает все заказы, изменившиеся с момента предыдущего вызова; в том числе он получит и изменение статуса creationStatus из InProgress в Success или Error. Плюсы этого метода: может возвращать сразу несколько заказов. Минусы: не получится вызывать метод слишком часто, из-за чего информация об успешном создании заказа будет поступать в интеграцию с определённой задержкой, что может быть неудобно для отслеживания успешности создания заказа (на более поздних этапах жизни заказа такие задержки менее критичны)
* (не рекомендуется) Периодический вызов метода [/api/1/deliveries/by_id](https://api-ru.iiko.services/docs#tag/Deliveries:-Retrieve/paths/~1api~11~1deliveries~1by_id/post). Алгоритм примерно тот же, что с методом [/api/1/commands/status](https://api-ru.iiko.services/docs#tag/Operations/paths/~1api~11~1commands~1status/post). Метод [/api/1/deliveries/by_id](https://api-ru.iiko.services/docs#tag/Deliveries:-Retrieve/paths/~1api~11~1deliveries~1by_id/post) будет возвращать значение creationStatus = InProgress, пока заказ создаётся во фронте; далее в какой-то момент вернёт creationStatus = Success или creationStatus = Error. Минус этого подхода по сравнению с использованием [/api/1/commands/status](https://api-ru.iiko.services/docs#tag/Operations/paths/~1api~11~1commands~1status/post) заключается в том, что метод [/api/1/deliveries/by_id](https://api-ru.iiko.services/docs#tag/Deliveries:-Retrieve/paths/~1api~11~1deliveries~1by_id/post) гораздо более тяжёлый, создаёт лишнюю нагрузку на CloudApi, поэтому для него настроены рейт-лимиты, которые не позволят вызывать его слишком часто.

5. При переходе заказа в статус Success интеграция должна обработать успешность создания заказа (уведомить пользователя о том, что заказ был создан).

6. При переходе заказа в статус Error интеграция обязана обработать ошибку (уведомить пользователя о том, что заказ не был создан, и разработчиков интеграции, чтобы они выяснили и устранили причину ошибки). Возможные причины ошибок:

* Валидация заказа на стороне кассы была неуспешной. Например, в одной из позиций заказа был передан id блюда, который неизвестен кассе. Информация об ошибке содержится в поле ErrorInfo.
* Заказ не был доставлен до кассы. Это бывает в случаях, когда касса потеряла связь с CloudApi из-за проблем с сетью (или просто выключена). В этом случае по истечении определённого таймаута (1-2 минуты) заказ автоматически переводится в статус Error; в поле ErrorInfo будет содержаться сообщение "Creation timeout expired, order automatically transited to error creation status".

7. В случае получения массовых ошибок (см. ниже) как при вызове метода [/api/1/deliveries/create](https://api-ru.iiko.services/docs#tag/Deliveries:-Create-and-update/paths/~1api~11~1deliveries~1create/post) так и в дальнейшем при проверке статуса созданных заказов интеграция не должна бесконечно пытаться повторять неуспешные запросы. Интеграция должна прервать работу и сообщить разработчикам о проблеме, чтобы они могли выяснить и устранить её причину.

Также следует с осторожностью относиться к логике работы интеграции, когда она запоминает заказы, которые не удалось доставить до кассы во время отсутствия связи, и пытается повторно их отправить после восстановления связи. Зависит от целей интеграции, но в большинстве случаев создание заказа со второй или третьей попытки только усугубит ситуацию, т.к. с первой попытки заказ не был создан, и гостю сообщили о его отмене, поэтому он не ждёт, что через 10-15 этот отменённый заказ всё-таки начнёт готовиться и доставляться.

Даже однократная ситуация, когда заказ не был успешно создан, является достаточно серьёзной проблемой, поэтому массовыми ошибками можно считать уже 2-3 подряд потерянных заказа - вероятность, что следующие заказы успешно дойдут до кассы в этом случае достаточно мала.

## Ограничения перевода статуса оплат
Требуются промежуточные статусы (в зависимости от того в какой момент происходит оплата):
**Оплата при закрытии**

1. Если переводить в статус **Delivered**, минуя **OnWay**, возникает ошибка: *«Can not update order, order status was changed at the restaurant checkout»*.
2. Перевод в статус **Waiting** возможен.

**Оплата при отправке**

1. Нельзя перевести заказ в статус **Waiting**, так как метод `PrepareDeliveryForSending` работает только при «Оплате при закрытии». Перевод в **OnWay** возможен.
2. В статус **Delivered** можно перейти только из **OnWay**. В противном случае возникает ошибка: *«Can not update order, order status was changed at the restaurant checkout»*.


* [Диагностика ошибки создания заказа](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h2__1863382226)
* [1. Создание доставки на выключенный iikoFront/либо при проблемах с доступом](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h3__52802670)
* [2. Не задана шкала размеров](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h3_1003885137)
* [3. Некорректные настройки модификаторов и их количественных ограничений для блюда](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h3_194301965)
* [4. Не задан тип места приготовления для блюда или некорректно выбрано блюдо](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h3__1922137823)
* [5. Блюдо исключено из меню](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h3__1494550100)
* [6. Товар не включен в продажу](/articles/api-documentations/poryadok-razbora-problem-s-dostavochnymi-zakazami/a/h3__1917161268)

Заказы, полученные по API, могут не создаться на терминале iikoFront по ряду причин. В данной статье рассмотрим наиболее часто встречающиеся случаи и наиболее популярные причины проблем с созданием заказов через iikoTransport.

## Диагностика ошибки создания заказа

Все ошибки, связанные с созданием заказов через iikoTransport, можно найти в логе транспортного плагина **plugin-Resto.Front.Api.iikoTransport.VXPreviewX** в iikoFront.
Получив ошибку, её легко можно найти по correlation id от внешних сервисов (например, от Delivery Club). Для поиска в логе фронтового плагина транспорта также пригодится время и дата направления запроса на создание доставочного заказа от внешнего сервиса в CloudApi и ключевые слова **save order**, **create order**.

### 1. Создание доставки на выключенный iikoFront/либо при проблемах с доступом

В ответе будет (обычно **Creation timeout expired, order automatically transited to error creation status**)


Code

```
{
    "correlationId": "ba101f44-e166-4b0a-b052-2ccc815b79d8",
    "orders": [
        {
            "id": "2b370a38-7b1f-4a0b-90c4-a2d7c45570e3",
            "organizationId": "******-****-****-****-***********",
            "timestamp": 1650895228234,
            "creationStatus": "Error",
```


В ответе есть время (в таком виде "timestamp": 1650895228234)
Переводим в привычный нам вид (любым доступным online [конвертером](https://www.unixtimestamp.com/))![](/resources/Storage/api-documentations/project-knowlege-base/getting-started-2022-04-25.png)

**GMT**: Monday, 25 April 2022 г., 14:00:28.234
**Your time zone**: понедельник, 25 апреля 2022 г., 17:00:28.234 [GMT+03:00](https://www.epochconverter.com/timezones?q=1650895228234)

В **cash-server.log** проверяем таймзону на фронте с главным терминалом:

Current time zone is (**UTC+03:00**) Kuwait, Riyadh (Arab Standard Time) with effective UTC offset 03:00

Далее проверяем plugin-Resto.Front.Api.iikoTransport.VXPreviewX.log - время из ответа.

**Решение**

1) при выполнении любого метода Cloud API iikoFront должен быть включен, так как в противном случае будет отсутствовать связь транспорта и терминальной группы, и заказы не будут доставлены на кассу.

Перед выполнением запроса на создание заказа выполните вызов метода проверки доступности терминала - [/api/1/terminal_groups/is_alive](https://api-ru.iiko.services/docs#tag/Terminal-groups/paths/~1api~11~1terminal_groups~1is_alive/post). Если в ответе метода "isAlive": true, то можно переходить к методу выполнения запроса на создание заказа.

2) после выполнения метода создания заказа можно уточнить, действительно ли заказ дошел до кассы. Для этого используйте метод [/api/1/commands/status](https://api-ru.iiko.services/docs#tag/Operations/paths/~1api~11~1commands~1status/post).

Если в ответе метода

"state": "InProgress" - заказ ещё не дошел до кассы,

если "state": "Success" - заказ дошел до кассы и можно выполнять следующие действия заказом,

если "state": "Error" и добавлено описание ошибки - в теле запроса создания заказа есть ошибка, требуется её устранение и повторное выполнение.

| ![Warning](/resources/Storage/api-documentations/api-documentations/warning.png) | Многократное выполнение любого метода с ошибочным телом запроса может привести к  API ключа. |
| --- | --- |

Ознакомьтесь с [общими принципами создания заказа](/articles/api-documentations/~obschie-printsipy-sozdaniya-zakaza-na-stol-i-na-dostavku) и по работе с [терминальными группами](/articles/iikoweb/iikocloudapi/a/h3_129714767).

### 2. Не задана шкала размеров

В таких случаях в логах**plugin-Resto.Front.Api.iikoTransport.VXPreviewX** можно найти сообщения вида:


Code

```
2021-10-29 17:37:22,466]  INFO [64] - [CorrelationId: a5148df3-e6ac-4bf6-87d4-98ec05f15588, Route: Orders/CreateOrder] 
Can not create delivery order 3b8e218f-d743-4eb9-acc4-1c0c25bf3114 / 5d34325c-a480-4a03-8411-c0ee56effaa5: 
Resto.Front.Api.Exceptions.ConstraintViolationException: 
Product “Маргарита” (28828c4a-728e-4a13-94da-ce6237cf8bde) has scale “Пицца” (73b7cd7c-1c8a-4623-958f-008be41662d7), 
therefore product size must be specified.
```


**Решением** будет проверить настройки блюда и задать шкалу размеров. Дополнительно проверить все блюда и их модификаторы на включенность в прейскурант в iikoOffice.

### 3. Некорректные настройки модификаторов и их количественных ограничений для блюда

Также находим по **correlationId** или по **Orders/SetOrderError**, **Start converting delivery order**, **Start order save**, **Can not create delivery order**


Code

```
[2021-09-02 11:59:13,559]  INFO [Event Loop 1] - Schedule new message: Id: 730c60fb-b7be-4d04-aa24-cc0171e3b609, 
CorrelationId: 57cf8884-94d7-4d9e-be6e-e3a9da497883, Route: Orders/SetOrderError.

```


Чуть выше запись в логе:
Code

```
[2021-09-02 11:59:13,559]  INFO [AMQP Connection amqp://rbmq-ru.iiko.services:5671] - 
Can not create delivery order f6f46419-6402-40f7-a11e-01b5d8acd48f: Resto.Front.Api.Exceptions.ConstraintViolationException: 
Order item modifier “гарнир” (2fe947ca-306a-43c2-9917-2714485d839a) has invalid group amount: min = 1, max = 1, actual = 0. 
Ensure that interconnected product and modifier changes are in the same edit session.

```


**Решением** будет проверить настройки блюда и модификаторов, скорректировав настройки в iikoOffice.

### 4. Не задан тип места приготовления для блюда или некорректно выбрано блюдо

В логе имеется запись:
Code

```
[2021-08-16 13:51:34,059]  INFO [12] - Finish order convert.
Start order save.
[2021-08-16 13:51:35,387]  INFO [47] - [CorrelationId: 4b26cb05-2f24-4c22-9a45-aa61bc451ec6, Route: Orders/CreateOrder] 
Can not create delivery order 0e021256-a74f-4a0b-bb2d-417bf027f2a3: Resto.Front.Api.Exceptions.ConstraintViolationException: 
Product “Округление в пользу гостя” (5b08a4c4-2453-a7f6-4275-4db8016a2e1f) doesn't have cooking place type.

```


**Решением** будет проверить настройки блюда и типа места приготовления, скорректировав настройки в iikoOffice. Проверить настройки сайта конструктора (блок "доставка" - поле "услуга доставки") или другого внешнего сервиса на предмет необходимости добавления того или иного блюда в заказ.

### 5. Блюдо исключено из меню

Частый сценарий, когда заказ создается на блюдо запрещенное к продаже. В логах фронтового транспортного плагина также будет присутствовать запись **excluded from menu**.

**Решением** будет включить блюдо в меню и проверить выгрузку меню и действующий прейскурант.

### 6. Товар не включен в продажу

Если поискать по id из ответа в логе транспортного плагина на фронте, то станет понятно в чем была ошибка.
В логе имеется запись:
Code

```
[2022-02-25 12:05:01,303]  INFO [48] - Finish order convert.
Start order save.
[2022-02-25 12:05:01,443]  INFO [ 8] - [CorrelationId: 896e8821-5e2f-44c3-93fe-5efedd168e43, 
Route: Orders/CreateOrder] Can not create delivery order c62db178-3561-4600-a098-8a8664e011d1 / 13088676-1311-8060-8769-745828518553: 
Resto.Front.Api.Exceptions.CannotAddInactiveProductException: 
Product “Молоко отдельно” (d131d813-c586-0cd0-0158-a8b4c8135c96) is inactive. Only active products can be added to order.

```


**Решением** будет проверить включенность товара в продажу и при необходимости внести правки в прейскурант и карточку товара/блюда.






* [API приказов](/articles/api-documentations/prikazy/a/v2.APIприказов-Описаниеполей)
* [MenuChangeDocumentDto](/articles/api-documentations/prikazy/a/v2.APIприказов-MenuChangeDocumentDto)
* [MenuChangeDocumentItemDto](/articles/api-documentations/prikazy/a/v2.APIприказов-MenuChangeDocumentItemDto)
* [IncludeForCategoryDto](/articles/api-documentations/prikazy/a/v2.APIприказов-IncludeForCategoryDto)
* [PriceForCategoryDto](/articles/api-documentations/prikazy/a/v2.APIприказов-PriceForCategoryDto)
* [Выгрузка приказов](/articles/api-documentations/prikazy/a/h2_1894775106)
* [Параметры запроса](/articles/api-documentations/prikazy/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/prikazy/a/h3_501454233)
* [Пример запроса и результата](/articles/api-documentations/prikazy/a/h3_1561844723)
* [Выгрузка приказа по идентификатору](/articles/api-documentations/prikazy/a/h2_362568358)
* [Параметры запроса](/articles/api-documentations/prikazy/a/h3__1718461175)
* [Пример запроса и результата](/articles/api-documentations/prikazy/a/h3_1214224988)
* [Выгрузка приказов по номеру](/articles/api-documentations/prikazy/a/h2_1748209904)
* [Параметры запроса](/articles/api-documentations/prikazy/a/h3_1693881420)
* [Пример запроса и результат](/articles/api-documentations/prikazy/a/h3__2087356861)
* [Создание/редактирование приказа](/articles/api-documentations/prikazy/a/h2_2107861861)
* [Тело запроса](/articles/api-documentations/prikazy/a/h3_1150399349)
* [Пример](/articles/api-documentations/prikazy/a/h3_1250036116)

* [Цены, заданные приказами](/articles/api-documentations/tseny-zadannye-prikazami)

##  API приказов

##  Версия iiko: 7.8

##  Описание полей

###  MenuChangeDocumentDto

| Поле | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | Идентификатор. |
| **dateIncoming** | String | Дата проведения документа (учетная) в формате "yyyy-MM-dd". |
| **documentNumber** | String | Учетный номер документа. |
| **status** | Enum | Статус документа.<br> | Значение | Описание |<br>| --- | --- |<br>| **NEW** | Новый. |<br>| **PROCESSED** | Проведенный. |<br>| **DELETED** | Удаленный. | |
| --- | --- | --- |
| **comment** | String | Комментарий к документу. |
| **shortName** | String | Короткое название приказа для отображения на кнопках фронта. |
| **deletePreviousMenu** | Boolean | Если true, то те блюда, которые не присутствуют в документе, будут исключены из меню. |
| **scheduleId** | UUID | Идентификатор расписания. Задается пользователем при создании/редактировании приказа по времени. |
| **schedule** | PeriodScheduleDto | Расписание действия приказа по времени. Только чтение. |
| **dateTo** | String | Дата окончания действия (отмены) приказа в формате "yyyy-MM-dd". |
| **items** | List&lt;MenuChangeDocumentItemDto&gt; | Позиции приказа. |

###  MenuChangeDocumentItemDto

| Поле | Тип | Описание |
| --- | --- | --- |
| **num** | Integer | Позиция строки в документе. При создании/редактировании приказа не учитывается. |
| **departmentId** | UUID | Идентификатор департамента, в котором осуществляется продажа данного продукта. |
| **productId** | UUID | Идентификатор продукта. |
| **productSizeId** | UUID | Идентификатор размера продукта. |
| **including** | Boolean | Включен ли продукт в прайс-лист. |
| **price** | BigDecimal | Цена. |
| **dishOfDay** | Boolean | Является ли блюдо хитом. |
| **flyerProgram** | Boolean | Участвует ли блюдо во флаерной программе. |
| **includeForCategories** | List&lt;IncludeForCategoryDto&gt; | Если в этом списке присутствует идентификатор категории, то для данной ценовой категории есть своя специфика ценообразования. |
| **pricesForCategories** | List&lt;PriceForCategoryDto&gt; | Цены для категорий. |

###  IncludeForCategoryDto

| Поле | Тип | Описание |
| --- | --- | --- |
| **categoryId** | UUID | Идентификатор ценовой категории. |
| **include** | Boolean | Если true, то цену берем из PriceForCategoryDto, если false, то для данной ценовой категории данный продукт исключен из прайс-листа. |

###  PriceForCategoryDto

| Поле | Тип | Описание |
| --- | --- | --- |
| **categoryId** | UUID | Идентификатор ценовой категории. |
| **price** | BigDecimal | Цена. |

## Выгрузка приказов

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/documents/menuChange |
| --- | --- |

### Параметры запроса

| Параметр | Тип | Описание |
| --- | --- | --- |
| dateFrom | String | Начало временного интервала в формате "yyyy-MM-dd". Обязательный. |
| dateTo | String | Конец временного интервала в формате "yyyy-MM-dd". Обязательный. |
| status | Enum | Статус документа. Если не задан, то все. |
| revisionFrom | Integer | В ответе будут сущности с ревизией выше данной. По умолчанию '-1'. |

### Что в ответе
 
Список приказов.
 
Поле revision - максимальная ревизия, доступная для выгрузки во внешние системы на момент запроса (это значит, что в базе присутствуют записи с такой ревизией, а записей с ревизией выше этой в базе нет).
 
Эту ревизию можно использовать в качестве параметра **revisionFrom** в следующем запросе на получение списка расписаний.
 
### Пример запроса и результата

#### Запрос

https://localhost:8080/resto/api/v2/documents/menuChange?dateFrom=2021-08-01&dateTo=2021-09-31
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE0%%
```


##  Выгрузка приказа по идентификатору

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/documents/menuChange/byId |
| --- | --- |

### Параметры запроса
 | Параметр | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | Идентификатор приказа. |
 
### Пример запроса и результата

#### Запрос

https://localhost:8080/resto/api/v2/documents/menuChange/byId?id=d776601c-3184-40d0-8d90-e0cd2164801a
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```

 
##  Выгрузка приказов по номеру

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/documents/menuChange/byNumber |
| --- | --- |

### Параметры запроса
 | Параметр | Тип | Описание |
| --- | --- | --- |
| **documentNumber** | String | Номер документа. |
 
### Пример запроса и результат

#### Запрос 

https://localhost:8080/resto/api/v2/documents/menuChange/byNumber?documentNumber=0006
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```


## Создание/редактирование приказа

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/documents/menuChange |
| --- | --- |

### Тело запроса
 
См. MenuChangeDocumentDto.
 
Если идентификатор документа не задан, то это создание нового приказа.
 
Если идентификатор документа задан, то это редактирование приказа.
 
Редактировать приказ можно, если

1. он находится в статусе 'NEW'
2. он находится в статуе 'PROCESSED' и дата проведения (начала действия) приказа сегодня или позже

У приказа в статусе 'PROCESSED', дата проведения которого вчера или ранее, можно изменить только дату окончания, если дата окончания завтра или позже.
 
Редактировать НК в приказе (поля taxCategoryId и taxCategoryEnabled) можно только при наличии лицензионного модуля 'Возможность задавать налоговую категорию в приказах на изменение меню' (ModuleId = 21052802).
 
Если явно задать taxCategoryEnabled при отключенной лицензии, то значения полей taxCategoryId и taxCategoryEnabled будут проигнорированы,  в БД значения этих полей не изменятся, в серверный лог будет выведено предупреждение вида:
 
The licensing module TAXCATEGORY\_IN\_PRICECHANGEORDER is not present or expired. Failed to establish tax category TaxCategory[ade0e464-0651-459b-ab14-12bab1570983]@80623417,r124 '20' for product товар\_2 (GOODS), produceSize null, department Department[0226a08b-b08d-428d-a505-f9a0de024373]@1330525574,r27 {code: 1, 'Новое торг. предприятие'}, date Wed Jul 12 00:00:00 MSK 2023
 Если не задавать явно taxCategoryEnabled, как это делают старые интеграции, которые ничего не знают про поля НК/Включить НК,
 то в БД значения этих полей не изменятся. Наличие лицензии в этом случае не проверяется.
 
###  Пример 

https://localhost:8080/resto/api/v2/documents/menuChange
 [+] [Запрос](javascript:void%280%29)
 [-] [Запрос](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE4%%
```



* [Стратегия расчета](/articles/api-documentations/tsenovye-kategorii/a/h3__812471)
* [Получение ценовых категорий](/articles/api-documentations/tsenovye-kategorii/a/v2.APIценовыхкатегорий-Получениеценовыхкатегорий)
* [Параметры запроса](/articles/api-documentations/tsenovye-kategorii/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/tsenovye-kategorii/a/h3_501454233)
* [Примеры запроса и результата](/articles/api-documentations/tsenovye-kategorii/a/h3_289737302)
* [Получение ценовой категории по идентификатору](/articles/api-documentations/tsenovye-kategorii/a/v2.APIценовыхкатегорий-Получениеценовойкатегориипоидентификатору)
* [Параметры запроса](/articles/api-documentations/tsenovye-kategorii/a/h3__974892588)
* [Пример запроса и результата](/articles/api-documentations/tsenovye-kategorii/a/h3_1561844723)

# API ценовых категорий

Версия iiko: 7.8

Описание полей

Ценовая категория

#### ClientPriceCategoryDto
| Поле | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | Идентификатор. |
| **name** | String | Название. |
| **deleted** | boolean | Удалена или нет. |
| **code** | String | Пользовательский код элемента справочника. |
| **assignableManually** | boolean | Может быть назначена вручную в iikoFront. |
| **pricingStrategy** | PricingStrategyDto | Стратегия расчёта новой цены. |
### 

### Стратегия расчета

#### **PricingStrategyDto**
| Поле | Тип | Описание |
| --- | --- | --- |
| **type** | Enum | Тип стратегии.<br>| Значение | Описание |<br>| --- | --- |<br>| ABSOLUTE\_VALUE | Стратегия, где скидка/наценка задаётся как абсолютное число, которое будет прибавляться к базовой цене. |<br>| PERCENT | Стратегия вычисления, когда скидка/надбавка задаётся в % от базовой цены. | |
| --- | --- | --- |
| **delta** | BigDecimal | Абсолютное значение скидки/надбавки. Если знак '-', то скидка, если '+', то надбавка. Актуально ABSOLUTE\_VALUE. |
| **percent** | BigDecimal | Значение скидки/надбавки в процентах. Если знак '-', то скидка, если '+', то надбавка. Диапазон значений: [-100, +inf). Актуально для PERCENT. |
## 

## Получение ценовых категорий

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/entities/priceCategories |
| --- | --- |

### Параметры запроса
| Параметр | Тип | Описание |
| --- | --- | --- |
| **includeDeleted** | Boolean | Включать ли в ответ удаленные элементы. По умолчанию false. |
| **id** | List&lt;UUID&gt; | Список идентификаторов ценовых категорий, которые требуется получить. Если не задано, то фильтрации по идентификаторам нет. |
| **revisionFrom** | Integer | В ответе будут сущности с ревизией выше данной. По умолчанию '-1'. |
### Что в ответе

Список ценовых категорий.

Поле revision - максимальная ревизия, доступная для выгрузки во внешние системы на момент запроса (это значит, что в базе присутствуют записи с такой ревизией, а записей с ревизией выше этой в базе нет).

Эту ревизию можно использовать в качестве параметра **revisionFrom** в следующем запросе на получение списка ценовых категорий.

### Примеры запроса и результата

#### Запрос

https://localhost:8080/resto/api/v2/entities/priceCategories/?includeDeleted=true
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE0%%
```

 
#### Запрос

https://localhost:8080/resto/api/v2/entities/priceCategories?id=95035a38-cd23-4b3b-92d8-1db673b6848f&id=67a54111-99ff-40cc-9f34-f2feddd0ff2b
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```


## Получение ценовой категории по идентификатору

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/**entities/priceCategories/byId** |
| --- | --- |

### Параметры запроса
| Параметр | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | Идентификатор ценовой категории. |
### Пример запроса и результата

#### Запрос

https://localhost:8080/resto/api/v2/entities/priceCategories/byId/?id=95035a38-cd23-4b3b-92d8-1db673b6848f
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```



* [Расписание](/articles/api-documentations/periody-deystviya/a/h3__1728986205)
* [Период действия (интервал) по дням недели](/articles/api-documentations/periody-deystviya/a/v2.APIпериодовдействий-Периоддействия%28интервал%29поднямнедели)
* [Получение расписаний](/articles/api-documentations/periody-deystviya/a/v2.APIпериодовдействий-Получениерасписаний)
* [Параметры запроса](/articles/api-documentations/periody-deystviya/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/periody-deystviya/a/h3_501454233)
* [Пример запроса и результата](/articles/api-documentations/periody-deystviya/a/v2.APIпериодовдействий-Пример)
* [Получение расписания по идентификатору](/articles/api-documentations/periody-deystviya/a/v2.APIпериодовдействий-Получениерасписанияпоидентификатору)
* [Параметры запроса](/articles/api-documentations/periody-deystviya/a/h3_1832657069)
* [Пример запроса и результата](/articles/api-documentations/periody-deystviya/a/v2.APIпериодовдействий-Пример.1)

# API периодов действий

Версия iiko: 7.8

Описание полей

### Расписание

#### PeriodScheduleDto
| Поле | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | Идентификатор. |
| **name** | String | Название. |
| **deleted** | Boolean | Удалена или нет. |
| **periods** | List&lt;PeriodScheduleItemDto&gt; | Список интервалов. |
### **Период действия (интервал) по дням недели**

#### **PeriodScheduleItemDto**
| Поле | Тип | Описание |
| --- | --- | --- |
| **begin** | String | Начало полуинтервала в виде "HH:mm". |
| **end** | String | Конец полуинтервала в виде "HH:mm". |
| **daysOfWeek** | List&lt;DayOfWeek&gt; | Дни недели, в которых действует интервал.<br>| DayOfWeek | DayOfWeek |<br>| --- | --- |<br>| Значение | Описание |<br>| --- | --- |<br>| 1 | понедельник |<br>| 2 | вторник |<br>| 3 | среда |<br>| 4 | четверг |<br>| 5 | пятница |<br>| 6 | суббота |<br>| 7 | воскресенье | |
| --- | --- | --- |
## 

## Получение расписаний

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/entities/periodSchedules |
| --- | --- |

### Параметры запроса
| Параметр | Тип | Описание |
| --- | --- | --- |
| **includeDeleted** | Boolean | Включать ли в ответ удаленные элементы. По умолчанию false. |
| **id** | List&lt;UUID&gt; | Список идентификаторов расписаний, которые требуется получить. Если не задано, то фильтрации по идентификаторам нет. |
| **revisionFrom** | Integer | В ответе будут сущности с ревизией выше данной. По умолчанию '-1'. |
### Что в ответе

Список расписаний.

Поле revision - максимальная ревизия, доступная для выгрузки во внешние системы на момент запроса (это значит, что в базе присутствуют записи с такой ревизией, а записей с ревизией выше этой в базе нет).

Эту ревизию можно использовать в качестве параметра **revisionFrom** в следующем запросе на получение списка расписаний.

### Пример запроса и результата

#### Запрос

https://localhost:8080/resto/api/v2/entities/periodSchedules
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE0%%
```

 
## Получение расписания по идентификатору

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/entities/periodSchedules |
| --- | --- |

### Параметры запроса

| Параметр | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | Идентификатор расписания. |

### Пример запроса и результата

#### Запрос

https://localhost:8080/resto/api/v2/entities/periodSchedules/byId?id=598ce53a-c49c-4cd5-8248-1e2b4f0994cf
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```



* [Доступ](/articles/api-documentations/rabota-s-bystrym-menyu/a/v2.APIбыстрогоменю-Доступ)
* [Описание быстрого меню](/articles/api-documentations/rabota-s-bystrym-menyu/a/v2.APIбыстрогоменю-Описаниебыстрогоменю)
* [Получение списка быстрых меню (GET)](/articles/api-documentations/rabota-s-bystrym-menyu/a/v2.APIбыстрогоменю-Получениеспискабыстрыхменю%28GET%29)
* [Параметры запроса](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_501454233)
* [Пример](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_1250036116)
* [Получение списка быстрых меню (POST)](/articles/api-documentations/rabota-s-bystrym-menyu/a/v2.APIбыстрогоменю-Получениеспискабыстрыхменю%28POST%29)
* [Параметры запроса](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3__130600020)
* [Что в ответе](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_345904457)
* [Создание быстрого меню](/articles/api-documentations/rabota-s-bystrym-menyu/a/v2.APIбыстрогоменю-Созданиебыстрогоменю)
* [Тело запроса](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_1150399349)
* [Что в ответе](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_2010954337)
* [Пример запроса и результата](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_1561844723)
* [Тело запроса](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_235180921)
* [Что в ответе](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_301772306)
* [Пример запроса и результата](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_1418450275)
* [Удаление быстрого меню](/articles/api-documentations/rabota-s-bystrym-menyu/a/v2.APIбыстрогоменю-Удалениебыстрогоменю)
* [Тело запроса](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_1215231645)
* [Что в ответе](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3__44805358)
* [Пример запроса и результата](/articles/api-documentations/rabota-s-bystrym-menyu/a/h3_2060852943)

## Доступ 

Чтобы пользоваться данным API:

* У пользователя, под чьим именем осуществляется вход, должно быть право B\_QMENU "Просматривать быстрое меню".

## Описание быстрого меню

Быстрое меню состоит из трех страниц. Каждая страница из 3 х 8 ячеек. В ячейке может содержаться либо элемент номенклатуры, либо группа элементов номенклатуры.

| Поле | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | UUID быстрого меню. |
| **deleted** | boolean | Удалено или нет. |
| **dependsOnWeekDay** | boolean | Зависит ли меню от дня недели. |
| **departmentId** | UUID | Подразделение, для которого действует данное быстрое меню. |
| **sectionId** | UUID | Отделение, для которого действует данное быстрое меню. Если null, то быстрое меню для всего подразделения. |
| **pageNames** | List&lt;String&gt; | Названия страниц (3 штуки). |
| **labels** | List&lt;QuickLabelDto&gt; | Список ячеек.<br>| Поле | Тип | Описание |<br>| --- | --- | --- |<br>| **day** | Integer | День недели. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, null.<br><br>Понедельник - 0. Воскресение - 6. |<br>| **page** | Integer | Номер страницы. Допустимые значения: 0, 1, 2. |<br>| **x** | Integer | Х-координата ячейки. Допустимые значения: 0, 1, 2. |<br>| **y** | Integer | Y-координата ячейки. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, 7. |<br>| **entityId** | UUID | UUID сущности. |<br>| **entityType** | Enum | Тип сущности.<br>| Поле | Описание |<br>| --- | --- |<br>| PRODUCT | Элемент номенклатуры. |<br>| PRODUCT\_GROUP | Группа элементов номенклатуры. | |<br>| --- | --- | --- | |
| --- | --- | --- |

## Получение списка быстрых меню (GET)

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/entities/quickLabels/list |
| --- | --- |

### Параметры запроса
| Параметр | Тип | Описание |
| --- | --- | --- |
| **includeDeleted** | boolean | Включать ли в ответ удаленные быстрые меню. По умолчанию false. |
| **revisionFrom** | Integer | Номер ревизии, начиная с которой необходимо отфильтровать сущности. |
| **id** | List&lt;UUID&gt; | Возвращаемые быстрые меню должны иметь id из этого списка. |
| **departmentId** | List&lt;UUID&gt; | Возвращаемые быстрые меню должны принадлежать подразделению, у которого id из этого списка. |
| **sectionId** | List&lt;UUID&gt; | Возвращаемые быстрые меню должны принадлежать отделению, у которого id из этого списка. Может содержать null. См. примеры. |
### Что в ответе

Список всех быстрых меню для всего подразделения. Содержит "общее" быстрое меню для всего подразделения и быстрое меню для конкретного отделения.

### Пример
https://localhost:9080/resto/api/v2/entities/quickLabels/list?departmentId=6713a472-973e-4215-8e0f-e3142945befd

[+] [Результат](javascript:void%280%29)
 [-] javascript:void%280%29Результат
 
```
 %%CH%PRE0%%
```


"Общее" быстрое меню подразделения. Фильтруем по sectionId = null.
https://localhost:9080/resto/api/v2/entities/quickLabels/list?departmentId=6713a472-973e-4215-8e0f-e3142945befd&sectionId=null
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```

 
## Получение списка быстрых меню (POST)

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/**entities/quickLabels/list** |
| --- | --- |

### Параметры запроса

| Параметр | Тип | Описание |
| --- | --- | --- |
| **includeDeleted** | boolean | Включать ли в ответ удаленные быстрые меню. По умолчанию false. |
| **revisionFrom** | Integer | Номер ревизии, начиная с которой необходимо отфильтровать сущности. |
| **id** | List&lt;UUID&gt; | Возвращаемые быстрые меню должны иметь id из этого списка. |
| **departmentId** | List&lt;UUID&gt; | Возвращаемые быстрые меню должны принадлежать подразделению, у которого id из этого списка. |
| **sectionId** | List&lt;UUID&gt; | Возвращаемые быстрые меню должны принадлежать отделению, у которого id из этого списка. Может содержать null. См. примеры. |

### Что в ответе
Список быстрых меню.

## Создание быстрого меню

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/**entities/quickLabels/save** |
| --- | --- |

### Тело запроса

Список ячеек
| Поле | Тип | Описание |
| --- | --- | --- |
| **dependsOnWeekDay** | boolean | Зависит ли меню от дня недели. |
| **departmentId** | UUID | Подразделение, для которого действует данное быстрое меню. |
| **sectionId** | UUID | Отделение, для которого действует данное быстрое меню. Если null, то быстрое меню для всего подразделения. |
| **pageNames** | List&lt;String&gt; | Названия страниц (3 штуки). |
| **labels** | List&lt;QuickLabelDto&gt; | Список ячеек<br>| Поле | Тип | Описание |<br>| --- | --- | --- |<br>| **day** | Integer | День недели. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, null.<br><br>Понедельник - 0. Воскресение - 6. |<br>| **page** | Integer | Номер страницы. Допустимые значения: 0, 1, 2. |<br>| **x** | Integer | Х-координата ячейки. Допустимые значения: 0, 1, 2. |<br>| **y** | Integer | Y-координата ячейки. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, 7. |<br>| **entityId** | UUID | UUID сущности. | |
| --- | --- | --- | [+] [Пример тела запроса](javascript:void%280%29)
 [-] [Пример тела запроса](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```

 
### Что в ответе

Созданное быстрое меню.

### Пример запроса и результата

#### Запрос

https://localhost:9080/resto/api/v2/entities/quickLabels/save
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

 
Редактирование быстрого меню

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/entities/quickLabels/update |
| --- | --- |

### Тело запроса

Список ячеек.
| Поле | Тип | Описание |
| --- | --- | --- |
| **id** | Integer | День недели. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, null.<br><br>Понедельник - 0. Воскресение - 6. |
| **dependsOnWeekDay** | Integer | Номер страницы. Допустимые значения: 0, 1, 2. |
| **departmentId** | Integer | Х-координата ячейки. Допустимые значения: 0, 1, 2. |
| **sectionId** | Integer | Y-координата ячейки. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, 7. |
| **pageNames** | UUID | UUID сущности. |
| **labels** | List&lt;QuickLabelDto&gt; | Список ячеек.<br>| Поле | Тип | Описание |<br>| --- | --- | --- |<br>| **day** | Integer | День недели. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, null.<br><br>Понедельник - 0. Воскресение - 6. |<br>| **page** | Integer | Номер страницы. Допустимые значения: 0, 1, 2. |<br>| **x** | Integer | Х-координата ячейки. Допустимые значения: 0, 1, 2. |<br>| **y** | Integer | Y-координата ячейки. Допустимые значения: 0, 1, 2, 3, 4, 5, 6, 7. |<br>| **entityId** | UUID | UUID сущности. | |
| --- | --- | --- | [+] [Пример тела запроса](javascript:void%280%29)
 [-] [Пример тела запроса](javascript:void%280%29)
 
```
 %%CH%PRE4%%
```

 
### Что в ответе

Отредактированное быстрое меню.

### Пример запроса и результата

#### Запрос
https://localhost:9080/resto/api/v2/entities/quickLabels/update
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE5%%
```


## Удаление быстрого меню

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://host:port/resto/api/v2/ |
| --- | --- |

### Тело запроса
| Поле | Тип | Описание |
| --- | --- | --- |
| **id** | UUID | UUID быстрого меню |
**Пример тела запроса**


Код

```
{
    "id": "345f5b9d-a356-f4e8-016b-080f9c44002a"
}
```


### Что в ответе

Быстрое меню, помеченное как удаленное.

### Пример запроса и результата

#### Запрос

https://localhost:9080/resto/api/v2/entities/quickLabels/delete
 [+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE7%%
```



* [OLAP-отчет](/articles/api-documentations/olap-otchety-v1/a/h2_1993590971)
* [Параметры запроса](/articles/api-documentations/olap-otchety-v1/a/h3_1827755295)
* [Что в ответе](/articles/api-documentations/olap-otchety-v1/a/h3__232688264)
* [Описание полей OLAP-отчетов](/articles/api-documentations/olap-otchety-v1/a/h3_1457076905)

## OLAP-отчет
 
Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/****api/** **reports/olap** |
| --- | --- |

### Параметры запроса

| Название | Значение | **Описание** |
| --- | --- | --- |
| *report* | SALES - По продажам<br> <br>TRANSACTIONS - По транзакциям<br> <br>DELIVERIES - По доставкам<br> <br>STOCK - Контроль хранения | Тип отчета |
| *summary* | true - вычислять итоговые значения<br><br>false - не вычислять итоговые значения | Вычислять ли итоговые значения.<br>По умолчанию выстален true. При значении false отчет строится намного быстрее.<br><br>с **Version (iiko) 5.3**<br><br>**С версии 9.1.2 значение по умолчанию false.** |
| *groupRow* | Поля группировки, например: groupRow=WaiterName& groupRow=OpenTime | Для определения списка доступных полей см.:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по продажам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по проводкам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по доставкам </span></span></li> </ul> <br>По полю можно проводить группировку, если значение в колонке Grouping для поля равно true |
| *groupCol* | Поля для выделения значений по колонкам | Для определения списка доступных полей см.:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по продажам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по проводкам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по доставкам </span></span></li> </ul> <br>По полю можно проводить группировку, если значение в колонке Grouping для поля равно true |
| *agr* | Поля агрегации, например: agr=DishDiscountSum&agr=VoucherNum | <ul style="margin: 0px; padding-left: 22px;"> <li> <p style="margin: 0px;"><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Для определения списка доступных полей см.: </span></span></p><ul style="list-style-type: disc; padding-left: 22px;"> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по продажам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по проводкам </span></span></li> <li><span style="font-size: 10pt;"><span style="font-family: &quot;Open Sans&quot;, Arial, Helvetica, sans-serif;">Описание полей OLAP отчета по доставкам </span></span></li> </ul> </li> </ul> <br>По полю можно проводить агрегацию, если значение в колонке Aggregation для поля равно true |
| *from* | DD.MM.YYYY | Начальная дата |
| *to* | DD.MM.YYYY | Конечная дата |

### Что в ответе

Структура *report.*

### Пример запроса

| https://localhost:8080/resto/api/reports/olap?key=ec621550-afae-133e-80c8-76155db2b268&report=SALES&from=01.12.2014&to=18.12.2014&groupRow=WaiterName&groupRow=OpenTime&agr=fullSum&agr=OrderNum |
| --- |

### Описание полей OLAP-отчетов
 [+] [Описание полей OLAP-отчета по доставкам](javascript:void%280%29)
 [-] [Описание полей OLAP-отчета по доставкам](javascript:void%280%29)
 # 

| **Name** | **Description** | **Aggreation** | **Grouping** | **Filtering** | **Type** | **Value** |
| --- | --- | --- | --- | --- | --- | --- |
| CloseTime | Время закрытия | false | true | true | DATETIME |  |
| Delivery.ActualTime | Фактическое время доставки | false | true | true | DATETIME |  |
| Delivery.Address | Адрес | false | true | true | STRING |  |
| Delivery.BillTime | Время печати накладной | false | true | true | DATETIME |  |
| Delivery.CancelCause | Причина отмены доставки | false | true | true | STRING |  |
| Delivery.City | Город | false | true | true | STRING |  |
| Delivery.CloseTime | Время закрытия доставки | false | true | true | DATETIME |  |
| Delivery.CookingToSendDuration | Длит: посл.серв.печать-отправка | true | false | false | INTEGER |  |
| Delivery.Courier | Курьер | false | true | true | STRING |  |
| Delivery.CustomerCardNumber | Номер карты клиента доставки | false | true | true | STRING |  |
| Delivery.CustomerCardType | Тип карты клиента доставки | false | true | true | STRING |  |
| Delivery.CustomerComment | Комментарий к клиенту | false | true | true | STRING |  |
| Delivery.CustomerCreatedDate<br><br>(до версии 4.2; в 4.2+ deprecated, заменено на Delivery.CustomerCreatedDateTyped) | Дата создания клиента | false | true | true | STRING |  |
| Delivery.CustomerCreatedDateTyped (4.2+) | Дата создания клиента | false | true | true | DATE |  |
| Delivery.CustomerMarketingSource | Реклама клиента | false | true | true | STRING |  |
| Delivery.CustomerName | ФИО клиента доставки | false | true | true | STRING |  |
| Delivery.Delay | Опоздание доставки(мин) | false | true | true | INTEGER |  |
| Delivery.DelayAvg | Ср.опоздание доставки(мин) | true | false | false | AMOUNT |  |
| Delivery.DeliveryComment | Комментарий к доставке | false | true | true | STRING |  |
| Delivery.DeliveryOperator | Оператор доставки | false | true | true | STRING |  |
| Delivery.Email | e-mail доставки | false | true | true | STRING |  |
| Delivery.ExpectedTime | Планируемое время доставки | false | true | true | DATETIME |  |
| Delivery.MarketingSource | Реклама | false | true | true | STRING |  |
| Delivery.Number | Номер доставки | false | true | true | INTEGER |  |
| Delivery.Phone | Телефон доставки | false | true | true | STRING |  |
| Delivery.PrintTime | Время печати доставки | false | true | true | DATETIME |  |
| Delivery.Region | Район | false | true | true | STRING |  |
| Delivery.SendTime | Время отправки доставки | false | true | true | DATETIME |  |
| Delivery.ServiceType | Тип доставки | false | true | true | ENUM | PICKUP<br>COURIER |
| Delivery.SourceKey | Источник доставки | false | true | true | STRING |  |
| Delivery.Street | Улица | false | true | true | STRING |  |
| Delivery.WayDuration | Время в пути(мин) | false | true | true | INTEGER |  |
| Delivery.WayDurationAvg | Ср.время в пути(мин) | true | false | false | AMOUNT |  |
| Delivery.WayDurationSum | Сумм.время в пути(мин) | true | false | false | INTEGER |  |
| DishServicePrintTime.Max | Сервисная печать последнего блюда | true | false | false | DATETIME |  |
 [+] [Описание полей OLAP отчета по проводкам](javascript:void%280%29)
 [-] [Описание полей OLAP отчета по проводкам](javascript:void%280%29)
 | ![Information](/resources/Storage/api-documentations/info.png) | Поля агрегации, учитывающие **начальный остаток товара и денежный остаток** (StartBalance.Amount, StartBalance.Money, FinalBalance.Amount, FinalBalance.Money) вычисляются суммированием всей таблицы проводок **за все время** работы системы (всей базы данных) без каких-либо оптимизаций. То есть, такой запрос может выполняться очень долго и замедлять работу сервера.<br><br>Если начальный остаток необходим, оставляйте в этом OLAP-запросе только те поля группировки, по которым он действительно необходим (как правило, это Account.Name и Product.Name), и вызывайте такой запрос **как можно реже** и в **не рабочее** время.<br><br>В 5.2 добавлено API для быстрого получения остатков: Отчеты по балансам. Во всех случаях рекомендуется пользоваться им вместо OLAP.<br><br>В 5.5 OLAP-отчеты с остатками оптимизированы с использованием балансовых таблиц ATransactionSum, ATransactionBalance, при условии, что применяются группировки и фильтры по полям из этих таблиц, см. признак StartBalanceOptimizable в описании полей.<br><br>То есть, правильно составленный запрос приведет к суммированию не всей таблицы проводок, а только лишь открытого периода. Обратите особое внимание на то, что оптимизировано только поле Account.Name (счет "текущей" стороны проводки, в том числе склад), а не Store (первый попавшийся "склад" проводки, взятый из: левой, правой части проводки, строки документа или самого документа).<br>**Склад** всегда, когда только возможно, следует брать из поля Account.Name ("Счет"), а **не** Store ("Склад"), оно вычисляется гораздо быстрее. |
| --- | --- |

| **Name** | **Description** | **Aggreation** | **Grouping** | **Filterig** | **StartBakanceOptimizable** | **Type** | **Value** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Account.AccountHierarchyFull | Иерархия счета | false | true | true | true | STRING |  |
| Account.AccountHierarchySecond | Счет 2-го уровня | false | true | true | true | STRING |  |
| Account.AccountHierarchyThird | Счет 3-го уровня | false | true | true | true | STRING |  |
| Account.AccountHierarchyTop | Счет 1-го уровня | false | true | true | true | STRING |  |
| Account.Code | Код счета | false | true | true | true | STRING |  |
| Account.CounteragentType | Тип контрагента | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип Контрагента |
| Account.Group | Группа счета | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Группа счета |
| Account.IsCashFlowAccount | Участвует ли счет в ДДС | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Участвует ли счет в ДДС |
| Account.Name | Счет | false | true | true | true | STRING | Счет (в том числе склад) |
| Account.StoreOrAccount | Склад/счет | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Счет/Склад |
| Account.Type | Тип счета | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип счета |
| Amount | Количество | true | false | false | - | AMOUNT |  |
| Amount.In | Приход (кол-во) | true | false | false | - | AMOUNT |  |
| Amount.Out | Расход (кол-во) | true | false | false | - | AMOUNT |  |
| Amount.StoreInOut (до версии 4.3; в 4.3+ deprecated, заменено на Amount.StoreInOutTyped) | Оборот эл.номенклатуры | true | false | false | - | STRING |  |
| Amount.StoreInOutTyped (4.3+, взамен Amount.StoreInOut) | Оборот эл.номенклатуры | true | false | false | - | AMOUNT |  |
| CashFlowCategory | Статья ДДС | false | true | true | true | STRING |  |
| CashFlowCategory.Hierarchy | Иерархия статей ДДС | false | true | true | true | STRING |  |
| CashFlowCategory.HierarchyLevel1 | Статья ДДС 1-го уровня | false | true | true | true | STRING |  |
| CashFlowCategory.HierarchyLevel2 | Статья ДДС 2-го уровня | false | true | true | true | STRING |  |
| CashFlowCategory.HierarchyLevel3 | Статья ДДС 3-го уровня | false | true | true | true | STRING |  |
| CashFlowCategory.Type | Тип статьи ДДС | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип статьи ДДС |
| Comment | Комментарий | false | true | true | false | STRING |  |
| Conception | Концепция | false | true | true | true | STRING |  |
| Conception.Code | Код концепции | false | true | true | true | STRING |  |
| Contr-Account.Code | Код корр.счета | false | true | true | false | STRING |  |
| Contr-Account.Group | Группа корр.счета | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Группа счета |
| Contr-Account.Name | Корр.Счет/Склад | false | true | true | false | STRING |  |
| Contr-Account.Type | Тип корр.счета | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Тип счета |
| Contr-Amount | Корр.количество | true | false | false | false | AMOUNT |  |
| Contr-Product.AccountingCategory | Корр.Бухгалтерская категория | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass | Класс алкогольной продукции | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass.Code | Код класса алкогольной продукции | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass.Group | Группа алкогольной продукции | false | true | true | false | STRING |  |
| Contr-Product.AlcoholClass.Type | Тип алкогольной продукции | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Тип алкогольной продукции |
| Contr-Product.Category | Корр.Категория номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.CookingPlaceType | Корр.Тип места приготовления | false | true | true | false | STRING |  |
| Contr-Product.Hierarchy | Корр.Иерархия номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.MeasureUnit | Корр.Единица измерения | false | true | true | false | STRING |  |
| Contr-Product.Name | Корр.Элемент номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.Num | Корр.Артикул элемента номенклатуры | false | true | true | false | STRING |  |
| Contr-Product.SecondParent | Корр.Группа номенклатуры 2-го уровня | false | true | true | false | STRING |  |
| Contr-Product.ThirdParent | Корр.Группа номенклатуры 3-го уровня | false | true | true | false | STRING |  |
| Contr-Product.TopParent | Корр.Группа номенклатуры 1-го уровня | false | true | true | false | STRING |  |
| Contr-Product.Type | Корр.Тип элемента номенклатуры | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Тип элемента номенклатуры |
| Counteragent.Name | Контрагент | false | true | true | true | STRING |  |
| DateTime (до версии 4.2; в 4.2+ deprecated, заменено на DateTime.Typed) | Дата и время | false | true | true | true\* | STRING |  |
| DateTime.Typed (4.2+) | Дата и время | false | true | true | true\* | DATETIME |  |
| DateTime.Date (до версии 4.2; в 4.2+ deprecated, заменено на DateTime.DateTyped) | Учетный день | false | true | true | true\* | STRING |  |
| DateTime.DateTyped (4.2+) | Учетный день | false | true | true | true\* | DATE |  |
| DateTime.DayOfWeak | День недели | false | true | true | true\* | STRING |  |
| DateTime.Hour | Час | false | true | true | true\* | STRING |  |
| DateTime.Month | Месяц | false | true | true | true\* | STRING |  |
| DateTime.Year | Год | false | true | true | true\* | STRING |  |
| DateSecondary.DateTyped (добавлено в 6.0) | Дата проводки | false | true | true |  | DATE |  |
| DateSecondary.DateTimeTyped (добавлено в 6.0) | Дата и время проводки | false | true | true |  | DATETIME |  |
| Department | Торговое предприятие | false | true | true | true | STRING |  |
| Department.Category1 | Категория 1 | false | true | true | true | STRING |  |
| Department.Category2 | Категория 2 | false | true | true | true | STRING |  |
| Department.Category3 | Категория 3 | false | true | true | true | STRING |  |
| Department.Category4 | Категория 4 | false | true | true | true | STRING |  |
| Department.Category5 | Категория 5 | false | true | true | true | STRING |  |
| Department.Code | Код подразделения | false | true | true | true | STRING |  |
| Department.JurPerson | Юридическое лицо | false | true | true | true | STRING |  |
| Document | Номер документа | false | true | true | false | STRING |  |
| FinalBalance.Amount | Конечный остаток товара | true | false | false | - | AMOUNT | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| FinalBalance.Money | Конечный денежный остаток | true | false | false | - | MONEY | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| PercentOfSummary.ByCol | % по столбцу | true | false | false | false | PERCENT |  |
| PercentOfSummary.ByRow | % по строке | true | false | false | false | PERCENT |  |
| Product.AccountingCategory | Бухгалтерская категория | false | true | true | true | STRING |  |
| Product.AlcoholClass | Класс алкогольной продукции | false | true | true | true | STRING |  |
| Product.AlcoholClass.Code | Код класса алкогольной продукции | false | true | true | true | STRING |  |
| Product.AlcoholClass.Group | Группа алкогольной продукции | false | true | true | true | STRING |  |
| Product.AlcoholClass.Type | Тип алкогольной продукции | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип алкогольной продукции |
| Product.AvgSum | Средняя цена | true | false | false | - | MONEY |  |
| Product.Category | Категория номенклатуры | false | true | true | true | STRING |  |
| Product.CookingPlaceType | Тип места приготовления | false | true | true | true | STRING |  |
| Product.Hierarchy | Иерархия номенклатуры | false | true | true | true | STRING |  |
| Product.MeasureUnit | Единица измерения | false | true | true | true | STRING |  |
| Product.Name | Элемент номенклатуры | false | true | true | true | STRING |  |
| Product.Num | Артикул элемента номенклатуры | false | true | true | true | STRING |  |
| Product.SecondParent | Группа номенклатуры 2-го уровня | false | true | true | true | STRING |  |
| Product.ThirdParent | Группа номенклатуры 3-го уровня | false | true | true | true | STRING |  |
| Product.TopParent | Группа номенклатуры 1-го уровня | false | true | true | true | STRING |  |
| Product.Type | Тип элемента номенклатуры | false | true | true | true | ENUM | Расшифровки кодов базовых типов#Тип элемента номенклатуры |
| Session.CashRegister | Касса | false | true | true | false | STRING |  |
| Session.Group | Группа | false | true | true | false | STRING |  |
| Session.RestaurantSection | Отделение | false | true | true | false | STRING |  |
| StartBalance.Amount | Начальный остаток товара | true | false | false | - | AMOUNT | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| StartBalance.Money | Начальный денежный остаток | true | false | false | - | MONEY | Тяжелый запрос, рекомендуется запускать только ночью.<br>См. выше. |
| Store | Склад | false | true | true | false | STRING | Склад: первый попавшийся склад проводки, взятый из: левой, правой части проводки, строки документа или самого документа. |
| Sum.Incoming | Сумма прихода | true | false | false | - | MONEY |  |
| Sum.Outgoing | Сумма расхода | true | false | false | - | MONEY |  |
| Sum.PartOfIncome | % от выручки | true | false | false | - | PERCENT |  |
| Sum.PartOfSummaryByCol | % суммы от итога по столбцам | true | false | false | - | PERCENT |  |
| Sum.PartOfSummaryByRow | % суммы от итога по строкам | true | false | false | - | PERCENT |  |
| Sum.PartOfTotalIncome | % от общей выручки | true | false | false | - | PERCENT |  |
| Sum.ResignedSum | Сумма | true | false | false | - | MONEY |  |
| TransactionSide | Дебет/Кредит | false | true | true | false | ENUM | Расшифровки кодов базовых типов#Дебит/Кредит |
| TransactionType | Тип транзакции | false | true | true | false | ENUM |  |
| TransactionType.Code | Код транзакции | false | true | true | false | OBJECT |  |

\* группировки по дате отбрасываются при вычислении начальных остатков
 [+] [Описание полей OLAP отчета по продажам](javascript:void%280%29)
 [-] [Описание полей OLAP отчета по продажам](javascript:void%280%29)

# 

| **Name** | **Description** | **Description Eng** | **Aggreation** | **Grouping** | **Filterig** | **Type** | **Value** |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AuthUser | Авторизовал | Authorised by | false | true | true | STRING |  |
| Banquet | Банкет | Banquet | false | true | true | ENUM | TRUE<br>FALSE |
| Bonus.CardNumber | Номер бонусной карты | Bonus card number | false | true | true | STRING |  |
| Bonus.Sum | Сумма бонуса | Bonus amount | true | false | false | MONEY |  |
| Bonus.Type | Тип бонуса | Bonus type | false | true | true | STRING |  |
| Card | Карта авторизации | Authorisation card | false | true | true | STRING |  |
| CardNumber | Номер карты оплаты | Pay card type | false | true | true | STRING |  |
| CardOwner | Владелец карты гостя | Guest cardholder | false | true | true | STRING |  |
| CardType | Кредитная карта | Credit card | false | true | true | STRING |  |
| Cashier | Кассир | Cashier | false | true | true | STRING |  |
| CashLocation | Расположение кассы | Cash register location | false | true | true | STRING |  |
| CashRegisterName | Касса | Cash register | false | true | true | STRING |  |
| CloseTime | Время закрытия | Closing time | false | true | true | DATETIME |  |
| Comment | Комментарий к блюду | Item comment | false | true | true | STRING |  |
| Conception | Концепция | Concept | false | true | true | STRING |  |
| CookingPlace | Место приготовления | Production place | false | true | true | STRING |  |
| CreditUser | В кредит на... | Credited to... | false | true | true | STRING |  |
| DayOfWeekOpen | День недели | Day of week | false | true | true | STRING |  |
| DeletedWithWriteoff | Блюдо удалено | Item deleted | false | true | true | ENUM | Расшифровки кодов базовых типов#Типы удаления блюд |
| DeletionComment | Комментарий к удалению блюда | Item deletion comment | false | true | true | STRING |  |
| Delivery.IsDelivery | Доставка | Delivery | false | true | true | ENUM | Расшифровки кодов базовых типов#Признак доставки |
| Department | Торговое предприятие | Outlet | false | true | true | STRING |  |
| DiscountPercent | Процент скидки | Discount rate | true | true | true | PERCENT |  |
| DiscountSum | Сумма скидки | Discount amount | true | false | true | MONEY |  |
| discountWithoutVAT | Сумма скидки без НДС не включенного в стоимость | Discount amount excl. VAT not included in the cost | true | false | true | MONEY |  |
| DishAmountInt | Количество блюд | Number of items | true | true | true | AMOUNT |  |
| DishCategory | Категория блюда | Item category | false | true | true | STRING |  |
| DishCode | Код блюда | Item code | false | true | true | STRING |  |
| DishCode.Quick | Код быстрого набора блюда | Item quick code | false | true | true | STRING |  |
| DishDiscountSumInt | Сумма со скидкой | Amount with discount | true | false | false | MONEY |  |
| DishDiscountSumInt.average | Средняя сумма заказа | Average bill amount | true | false | false | MONEY |  |
| DishDiscountSumInt.averageByGuest | Средняя выручка с гостя | Average revenue per guest | true | false | false | MONEY |  |
| DishDiscountSumInt.averagePrice | Средняя цена без НДС | Average price (VAT exclusive) | true | false | false | MONEY |  |
| DishDiscountSumInt.withoutVAT | Сумма со скидкой без НДС | Amount with discount VAT exclusive | true | false | false | MONEY |  |
| DishForeignName | Наименование блюда на иностранном языке | Item name in a foreign language | false | true | true | STRING |  |
| DishFullName | Полное наименование блюда | Full name of the item | false | true | true | STRING |  |
| DishGroup | Группа блюда | Item group | false | true | true | STRING |  |
| DishGroup.Hierarchy | Иерархия блюда | Item hierarchy | false | true | true | STRING |  |
| DishGroup.Num | Код группы блюда | Item group code | false | true | true | STRING |  |
| DishGroup.SecondParent | Группа блюда 2-го уровня | Level 2 item group | false | true | true | STRING |  |
| DishGroup.ThirdParent | Группа блюда 3-го уровня | Level 3 item group | false | true | true | STRING |  |
| DishGroup.TopParent | Группа блюда 1-го уровня | Level 1 item group | false | true | true | STRING |  |
| DishMeasureUnit | Единица измерения | Measurement unit | false | true | true | STRING |  |
| DishName | Блюдо | Item | false | true | true | STRING |  |
| DishReturnSum | Сумма возврата | Void amount | true | true | true | MONEY |  |
| DishServicePrintTime | Сервисная печать блюда | Service printing item | false | true | true | DATETIME |  |
| DishServicePrintTime.Max | Сервисная печать последнего блюда | Service printing latest item | true | false | false | DATETIME |  |
| DishServicePrintTime.OpenToLastPrintDuration | Длит: откр.-посл.серв.печать | Duration: open latest serv. print. | true | false | false | INTEGER |  |
| DishSumInt | Сумма без скидки | Amount without discount | true | false | false | MONEY |  |
| DishType | Тип товара | Stock list type | false | true | true | ENUM | Расшифровки кодов базовых типов#Тип товара |
| fullSum | Сумма без НДС не включенного в стоимость | Amount excl. VAT not included in the cost | true | false | true | MONEY |  |
| GuestNum | Количество гостей | Number of guests | true | true | true | AMOUNT |  |
| GuestNum.Avg | Ср.кол-во гостей на чек | AvgNumber of guests per receipt | true | false | false | AMOUNT |  |
| HourClose | Час закрытия | Closing hour | false | true | true | STRING |  |
| HourOpen | Час открытия | Opening hour | false | true | true | STRING |  |
| IncentiveSumBase.Sum | Мотивационный бонус | Incentive payment | true | false | false | MONEY |  |
| IncreasePercent | Процент надбавки | Surcharge rate | true | true | true | PERCENT |  |
| IncreaseSum | Сумма надбавки | Surcharge amount | true | true | true | MONEY |  |
| JurName | Юридическое лицо | Legal entity | false | true | true | STRING |  |
| Mounth | Месяц | Month | false | true | true | STRING |  |
| NonCashPaymentType | Безналичный тип оплаты | Non-cash payment type | false | true | true | STRING |  |
| NonCashPaymentType.DocumentType | Тип документа | Document type | false | true | true | ENUM | Расшифровки кодов базовых типов#Тип документа |
| OpenDate (до версии 4.2; в 4.2+ deprecated, заменено на OpenDate.Typed) | Учетный день |  | false | true | true | STRING |  |
| OpenDate.Typed (4.2+) | Учетный день |  | false | true | true | DATE |  |
| OpenTime | Время открытия | Opening time | false | true | true | DATETIME |  |
| OperationType | Операция | Operation | false | true | true | ENUM | Расшифровки кодов базовых типов#Тип операции |
| OrderDeleted | Заказ удален | Order deleted | false | true | true | ENUM | Расшифровки кодов базовых типов#Признак удаления заказа |
| OrderDiscount.GuestCard | Гостевая карта | Guest card | false | true | true | STRING |  |
| OrderDiscount.Type | Тип скидки | Discount type | false | true | true | STRING |  |
| OrderIncrease.Type | Тип надбавки | Type of surcharge | false | true | true | STRING |  |
| OrderItems | Позиций чека | Order items | true | false | false | INTEGER |  |
| OrderNum | Номер чека | Receipt number | true | true | true | INTEGER |  |
| OrderTime.AverageOrderTime | Ср.время обсл.(мин) | AvgServing time (min) | true | false | false | AMOUNT |  |
| OrderTime.AveragePrechequeTime | Ср.время в пречеке (мин) | Avg time in guest bill (min) | true | false | false | AMOUNT |  |
| OrderTime.OrderLength | Время обслуживания (мин) | Serving time (min) | false | true | true | INTEGER |  |
| OrderTime.OrderLengthSum | Время обсл.сумм.(мин) | Serving time (min) | true | false | false | INTEGER |  |
| OrderTime.PrechequeLength | Время в пречеке (мин) | Time in guest bill (min) | false | true | true | INTEGER |  |
| OrderType | Тип заказа | Order type | false | true | true | STRING |  |
| OrderWaiter.Name | Официант заказа | Waiter for the order | false | true | true | STRING |  |
| OriginName | Источник заказа | Order origin | false | true | true | STRING |  |
| PayTypes | Тип оплаты | Payment type | false | true | true | STRING |  |
| PayTypes.Combo | Тип оплаты (комб.) | Payment type (comb.) | false | true | true | STRING |  |
| PayTypes.Group | Группа оплаты | Payment group | false | true | true | ENUM | Расшифровки кодов базовых типов#Группа оплаты |
| PayTypes.IsPrintCheque | Фиск. тип оплаты | Fisc. payment type | false | true | true | ENUM | Расшифровки кодов базовых типов#Признак фискальности оплаты |
| PayTypes.VoucherNum | Количество ваучеров | Number of vouchers | true | false | false | INTEGER |  |
| PercentOfSummary.ByCol | % по столбцу | % by column | true | false | false | PERCENT |  |
| PercentOfSummary.ByRow | % по строке | % by row | true | false | false | PERCENT |  |
| PrechequeTime | Время пречека | Guest bill time | false | true | true | DATETIME |  |
| PriceCategory | Ценовая категория клиента | Customer price category | false | true | true | STRING |  |
| PriceCategoryCard | ЦК номер карты | Price Category Card Number | false | true | true | STRING |  |
| PriceCategoryDiscountCardOwner | ЦК владелец карты | Price Category Cardholder | false | true | true | STRING |  |
| PriceCategoryUserCardOwner | ЦК контрагент | Price Category Card Owner | false | true | true | STRING |  |
| ProductCostBase.MarkUp | Наценка(%) | Markup (%) | true | false | false | PERCENT |  |
| ProductCostBase.OneItem | Себестоимость единицы | Cost per unit | true | false | false | MONEY |  |
| ProductCostBase.Percent | Себестоимость(%) | Cost(%) | true | false | false | PERCENT |  |
| ProductCostBase.ProductCost | Себестоимость | Cost | true | false | false | MONEY |  |
| ProductCostBase.Profit | Наценка | Markup | true | false | false | MONEY |  |
| RemovalType | Причина удаления блюда | Reason for item deletion | false | true | true | STRING |  |
| RestaurantSection | Отделение | Room | false | true | true | STRING |  |
| RestorauntGroup | Группа | Group | false | true | true | STRING |  |
| SessionNum | Номер смены | Shift number | false | true | true | INTEGER |  |
| SoldWithDish | Продано с блюдом | Sold with item | false | true | true | STRING |  |
| Store.Name | Со склада | From storage | false | true | true | STRING |  |
| StoreTo | На склад | To storage | false | true | true | STRING |  |
| Storned | Возврат чека | Void receipt | false | true | true | ENUM | TRUE<br>FALSE |
| sumAfterDiscountWithoutVAT | Сумма со скидкой без НДС не включенного в стоимость | Amount with discount excl. VAT not included in the cost | true | false | true | MONEY |  |
| TableNumInt (до 5.1; в 5.1+ заменено на TableNum) | Номер стола |  | false | true | true | STRING |  |
| TableNum (5.1+) | Номер стола |  | false | true | true | INTEGER |  |
| UniqOrderId | Чеков | Orders | true | false | false | INTEGER |  |
| UniqOrderId.OrdersCount | Заказов | Orders | true | false | false | AMOUNT |  |
| VAT.Percent | НДС(%) | VAT(%) | true | true | true | PERCENT |  |
| VAT.Sum | НДС по чекам(Сумма) | VAT by bill (Amount) | true | true | true | MONEY |  |
| WaiterName | Официант блюда | Item waiter | false | true | true | STRING |  |
| WriteoffReason | Причина списания | Write-off reason | false | true | true | STRING |  |
| WriteoffUser | Списано на сотрудника | Written off to employee | false | true | true | STRING |  |
| YearOpen | Год | Year | false | true | true | STRING |  |
 [+] [Описание полей OLAP отчета по контролю хранения](javascript:void%280%29)
 [-] [Описание полей OLAP отчета по контролю хранения](javascript:void%280%29)
 | Name | Description | Aggreation | Grouping | Type | Value |
| --- | --- | --- | --- | --- | --- |
| ProductNum | Артикул | false | true | STRING |  |
| ProductName | Блюдо | false | true | STRING |  |
| ProductAccountingCategory | Бухгалтерская категория блюда | false | true | STRING |  |
| EventDate | Дата | false | true | DATETIME |  |
| EventCookingDate | Дата и время приготовления | false | true | DATETIME |  |
| ProductMeasureUnit | Единицы измерения | false | true | STRING |  |
| ProductCategory | Категория блюда | false | true | STRING |  |
| Department.Code | Код подразделения | false | true | STRING |  |
| Amount | Количество | false | true | AMOUNT |  |
| ProductExpirationDuration | Просрочка на момент продажи | true | false | DATETIME |  |
| ProductCostBase.OneItem | Себестоимость единицы, р. | true | false | MONEY |  |
| ProductCostBase.ProductCost | Себестоимость, р. | true | false | MONEY |  |
| StoreFrom | Склад | false | true | STRING |  |
| User | Сотрудник | false | true | STRING |  |
| AccountTo | Счет | false | true | STRING |  |
| Event.Type | Тип события | false | true | STRING |  |
| Department | Торговое предприятие | false | true | STRING |  |


* [Отчеты по доставке](/articles/api-documentations/otchety-dostavka-v1/a/h2_1240291600)
* [Сводный отчет](/articles/api-documentations/otchety-dostavka-v1/a/v1.APIотчетов%28доставка%29-Сводныйотчет%28GETreports)
* [Параметры запроса](/articles/api-documentations/otchety-dostavka-v1/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/otchety-dostavka-v1/a/h3_501454233)
* [Пример вызова](/articles/api-documentations/otchety-dostavka-v1/a/h3__232688264)
* [Отчет по курьерам](/articles/api-documentations/otchety-dostavka-v1/a/h2_1037094901)
* [Параметры запроса](/articles/api-documentations/otchety-dostavka-v1/a/h3_1258952149)
* [Что в ответе](/articles/api-documentations/otchety-dostavka-v1/a/h3__819598880)
* [Пример вызова](/articles/api-documentations/otchety-dostavka-v1/a/h3__2027210141)
* [Цикл заказа](/articles/api-documentations/otchety-dostavka-v1/a/v1.APIотчетов%28доставка%29-Циклзаказа%28GETreports)
* [Параметры запроса](/articles/api-documentations/otchety-dostavka-v1/a/h3_1316811548)
* [Что в ответе](/articles/api-documentations/otchety-dostavka-v1/a/h3_1865795195)
* [Пример вызова](/articles/api-documentations/otchety-dostavka-v1/a/h3_1793323402)
* [Получасовой детальный отчет](/articles/api-documentations/otchety-dostavka-v1/a/v1.APIотчетов%28доставка%29-Получасовойдетальныйотчет%28GETreports)
* [Параметры запроса](/articles/api-documentations/otchety-dostavka-v1/a/h3_1726970929)
* [Что в ответе](/articles/api-documentations/otchety-dostavka-v1/a/h3_1577632198)
* [Пример вызова](/articles/api-documentations/otchety-dostavka-v1/a/h3__1708034687)
* [Отчет по регионам](/articles/api-documentations/otchety-dostavka-v1/a/v1.APIотчетов%28доставка%29-Отчетпорегионам%28GETreports)
* [Параметры запроса](/articles/api-documentations/otchety-dostavka-v1/a/h3__1130534387)
* [Что в ответе](/articles/api-documentations/otchety-dostavka-v1/a/h3__614265233)
* [Пример вызова](/articles/api-documentations/otchety-dostavka-v1/a/h3_1486024652)
* [Отчет по регионам](/articles/api-documentations/otchety-dostavka-v1/a/v1.APIотчетов%28доставка%29-Отчетпорегионам%28GETreports)
* [Параметры запроса](/articles/api-documentations/otchety-dostavka-v1/a/h3__764351801)
* [Что в ответе](/articles/api-documentations/otchety-dostavka-v1/a/h3_442885765)
* [Пример вызова](/articles/api-documentations/otchety-dostavka-v1/a/h3_935121650)

## Отчеты по доставке

## Сводный отчет 

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/reports/delivery/consolidated |
| --- | --- |

### Параметры запроса

| **Параметры** | **Описание** |
| --- | --- |
| department | Подразделения (Код или ИД) (department={code="005"}). Если не указан, отчет будет построен для всех подразделений (Чейн) |
| --- | --- |
| dateFrom | Дата начала отчета (DD.MM.YYYY или YYYY-MM-DD) |
| --- | --- |
| dateTo | Дата окончания отчета |
| --- | --- |
| writeoffAccounts | Список счетов списания (код или ИД) |
| --- | --- |

### Что в ответе


```json
<report>
<rows>
<row>
<!--средний чек-->
<avgReceipt>486.25</avgReceipt>
<!--дата-->
<date>01.04.2014</date>
<!--кол-во блюд-->
<dishAmount>468.00</dishAmount>
<!--кол-во блюд в чеке-->
<dishAmountPerOrder>2.23</dishAmountPerOrder>
<!--кол- во заказов-->
<orderCount>210.00</orderCount>
<!--заказов "курьер"-->
<orderCountCourier>65.00</orderCountCourier>
<!--заказов "с собой"-->
<orderCountPickup>145.00</orderCountPickup>
<!--% выполнения бюджета-->
<planExecutionPercent>91.00</planExecutionPercent>
<!--% списания-->
<ratioCostWriteoff>22.10</ratioCostWriteoff>
<!--выручка--><revenue>102113.00</revenue>
</row>
</rows>
</report>
```


### Пример вызова

https://localhost:9080/resto/api/reports/delivery/consolidated?department={code="5"}&dateFrom=01.04.2014&dateTo=30.04.2014&writeoffAccounts={code="5.14"}&writeoffAccounts={code="5.13"}&key=cd8cf2c7-a0a2-8b82-b29a-f4f9bf74e5c2

****

## Отчет по курьерам 

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/reports/delivery/couriers |
| --- | --- |

### Параметры запроса

| **Параметры** | **Описание** |
| --- | --- |
| department | Подразделения (Код или ИД) (department={code="005"}). Если не указан, отчет будет построен для всех подразделений (Чейн) |
| --- | --- |
| dateFrom | Дата начала отчета (DD.MM.YYYY или YYYY-MM-DD) |
| --- | --- |
| dateTo | Дата окончания отчета |
| --- | --- |
| targetCommonTime | Целевое значение общего времени, мин. (по умолчанию - 30 мин.) |
| --- | --- |
| targetOnTheWayTime | Целевое значение времени в пути, мин. (по умолчанию - 0 мин.) |
| --- | --- |
| targetDoubledOrders | Целевое количество сдвоенных заказов за день, шт. (по умолчанию - 0 мин.) |
| --- | --- |
| targetTripledOrders | Целевое количество строенных заказов за день, шт. (по умолчанию - 0 мин.) |
| --- | --- |
| targetTotalOrders | Целевое количество заказов за день, шт (по умолчанию - 0 мин.) |
| --- | --- |

### Что в ответе


```json
<report>
<rows>
<row>
<!--курьер–>
<courier>Елена</courier>
<metrics><metric>
<!--сдвоенные заказы-->
<doubledOrders>0.00</doubledOrders>
<!--тип метрики (AVERAGE - среднее,TARGET - отношение к целевым показателям,MAXIMUM - максимальное значение)-->
<metricType>AVERAGE</metricType>
<!--время в пути-->
<onTheWayTime>0.00</onTheWayTime>
<!--кол-во заказов-->
<orderCount>1.00</orderCount>
<!--общее время-->
<totalTime>34.00</totalTime>
<!--строенные заказы-->
<tripledOrders>0.00</tripledOrders>
</metric>
<metric>
<doubledOrders>100.00</doubledOrders>
<metricType>TARGET</metricType>
<onTheWayTime>100.00</onTheWayTime>
<orderCount>0.00</orderCount>
<totalTime>0.00</totalTime>
<tripledOrders>100.00</tripledOrders>
</metric>
<metric>
<doubledOrders>0.00</doubledOrders>
<metricType>MAXIMUM</metricType>
<onTheWayTime>0.00</onTheWayTime>
<orderCount>1.00</orderCount>
<totalTime>34.00</totalTime>
<tripledOrders>0.00</tripledOrders>
</metric>
</metrics>
</row>
<report>
```


### Пример вызова

| https://localhost:9080/resto/api/reports/delivery/couriers?department={code="5"}&dateFrom=01.04.2014&dateTo=30.04.2014&targetCommonTime=5&targetOnTheWayTime=6&targetDoubledOrders=7&targetTripledOrders=8&targetTotalOrders=9&key=d34ab6bd-1515-f22e-d02d-92d2a682a512 |
| --- |

## Цикл заказа 

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/reports/delivery/orderCycle |
| --- | --- |

### Параметры запроса

| **Параметры** | **Описание** |
| --- | --- |
| department | Подразделения (Код или ИД) (department={code="005"}). Если не указан, отчет будет построен для всех подразделений (Чейн) |
| --- | --- |
| dateFrom | Дата начала отчета (DD.MM.YYYY или YYYY-MM-DD) |
| --- | --- |
| dateTo | Дата окончания отчета |
| --- | --- |
| targetPizzaTime | Целевое значение времени на столе Пицца (по умолчанию - 0 мин.) |
| --- | --- |
| targetCuttingTime | Целевое значение времени на столе нарезки (по умолчанию - 0 мин.) |
| --- | --- |
| targetOnShelfTime | Целевое значение времени на стеллаже оперативности (по умолчанию - 0 мин.) |
| --- | --- |
| targetInRestaurantTime | Целевое значение времени в ресторане (по умолчанию - 0 мин.) |
| --- | --- |
| targetOnTheWayTime | Целевое значение времени в пути (по умолчанию - 0 мин.) |
| --- | --- |
| targetTotalTime | Целевое значение общего времени доставки (по умолчанию - 0 мин.) |
| --- | --- |

### Что в ответе


```json
<report>
<rows>
<row>
<!--время на столе нарезки-->
<cuttingTime>0.00</cuttingTime>
<!--время в ресторане-->
<inRestaurantTime>15.90</inRestaurantTime>
<!--время на стеллаже оперативности-->
<onShelfTime>3.72</onShelfTime>
<!--время в пути-->
<onTheWayTime>8.22</onTheWayTime>
<!--время на столе Пицца-->
<pizzaTime>0.00</pizzaTime>
<!--общее время-->
<totalTime>26.61</totalTime>
<!--тип метрики (AVERAGE - среднее, TARGET - отношение к целевым показателям, MAXIMUM - максимальное значение)-->
<metricType>AVERAGE</metricType>
</row>
</rows>
</report>
```


### Пример вызова

https://localhost:9080/resto/api/reports/delivery/orderCycle?department={code="5"}&dateFrom=01.04.2014&dateTo=30.04.2014&targetPizzaTime=5&targetCuttingTime=6&targetOnShelfTime=7&targetInRestaurantTime=8&targetOnTheWayTime=9&targetTotalTime=10&key=a113485b-d4f1-0856-8faf-50ba913f04eb
 
## Получасовой детальный отчет 

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/reports/delivery/halfHourDetailed |
| --- | --- |

### Параметры запроса

| **Параметры** | **Описание** |
| --- | --- |
| department | Подразделения (Код или ИД) (department={code="005"}). Если не указан, отчет будет построен для всех подразделений (Чейн) |
| --- | --- |
| dateFrom | Дата начала отчета (DD.MM.YYYY или YYYY-MM-DD) |
| --- | --- |
| dateTo | Дата окончания отчета |
| --- | --- |

### Что в ответе


```json
<report>
<rows>
<row>
<!--время (каждые полчаса)-->
<halfHourDate>01.04.2014 10:00</halfHourDate>
<metrics>
<metric>
<!--среднее кол-во блюд на чек-->
<avgDishAmountPerReceipt>3.500</avgDishAmountPerReceipt>
<!--средний чек-->
<avgReceipt>635.00</avgReceipt>
<!--тип доставки-->
<deliveryType>COURIER</deliveryType>
<!--кол-во блюд-->
<dishAmount>7.000</dishAmount>
<!--кол-во заказов-->
<orderCount>2.00</orderCount>
</metric>
<metric>
<avgDishAmountPerReceipt>3.000</avgDishAmountPerReceipt>
<avgReceipt>226.00</avgReceipt>
<deliveryType>PICKUP</deliveryType>
<dishAmount>6.000</dishAmount>
<orderCount>2.00</orderCount>
</metric>
</metrics>
</row>...</rows>
</report>
```


### Пример вызова

https://localhost:9080/resto/api/reports/delivery/halfHourDetailed?department={code="5"}&dateFrom=01.04.2014&dateTo=30.04.2014&key=d34ab6bd-1515-f22e-d02d-92d2a682a512

****

## Отчет по регионам 

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/reports/delivery/regions |
| --- | --- |

### Параметры запроса

| **Параметры** | **Описание** |
| --- | --- |
| department | Подразделения (Код или ИД) (department={code="005"}). Если не указан, отчет будет построен для всех подразделений (Чейн) |
| --- | --- |
| dateFrom | Дата начала отчета (DD.MM.YYYY или YYYY-MM-DD) |
| --- | --- |
| dateTo | Дата окончания отчета |
| --- | --- |

### Что в ответе


```json
<report>
<rows>
<row>
<!--среднее время доставки-->
<averageDeliveryTime>18.41</averageDeliveryTime>
<!--процент доставленных заказов-->
<deliveredOrdersPercent>100.00</deliveredOrdersPercent>
<!--максимальное кол-во заказов в день-->
<maxOrderCountDay>142.00</maxOrderCountDay>
<!--общее кол-во заказов-->
<orderCount>2336.00</orderCount>
<!--регион-->
<region>G1</region>
</row>
</rows>
</report>
```


### Пример вызова

| https://localhost:9080/resto/api/reports/delivery/regions?department={code="5"}&dateFrom=01.04.2014&dateTo=30.04.2014&key=08c12b43-3b43-6493-c758-3ee1e6f2a978 |
| --- |

****

## Отчет по регионам

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/reports/delivery/loyalty |
| --- | --- |

### Параметры запроса
| **Параметры** | **Описание** |
| --- | --- |
| department | Подразделения (Код или ИД) (department={code="005"}). Если не указан, отчет будет построен для всех подразделений (Чейн) |
| --- | --- |
| dateFrom | Дата начала отчета (DD.MM.YYYY или YYYY-MM-DD) |
| --- | --- |
| dateTo | Дата окончания отчета |
| --- | --- |
| metricType | Тип метрики (AVERAGE - среднее, MINIMUM- минимальное значение, MAXIMUM - максимальное значение |
| --- | --- |
### Что в ответе


```json
<report>
<rows>
<row>
<!--дата-->
<date>01.04.2014</date>
<!--тип метрики-->
<metricType>AVERAGE</metricType>
<!--кол-во новых гостей-->
<newGuestCount>58.00</newGuestCount>
<!--среднее кол-во заказов на гостя-->
<orderCountPerGuest>1.08</orderCountPerGuest>
<regions>
<region>
<!--кол-во заказов-->
<orderCount>61.00</orderCount>
<!--регион-->
<region>G1</region>
</region>
<region>
<orderCount>153.00</orderCount>
</region>
</regions>
<totalOrderCount>214.00</totalOrderCount
</row>
...
</rows>
</report>
```


### Пример вызова

| https://localhost:9080/resto/api/reports/delivery/loyalty?department={code="5"}&dateFrom=01.04.2014&dateTo=30.04.2014&metricType=AVERAGE&key=23d49457-025c-f23c-35dd-8e32eceef8a4 |
| --- |

****

* [Отчет по складским операциям](/articles/api-documentations/otchety-v1/a/v1.APIотчетов-Отчетпоскладскимоперациям)
* [Параметры запроса](/articles/api-documentations/otchety-v1/a/h3_2063281844)
* [Что в ответе](/articles/api-documentations/otchety-v1/a/h3_397569361)
* [Пресеты отчетов по складским операциям](/articles/api-documentations/otchety-v1/a/h2__1976728320)
* [Что в ответе](/articles/api-documentations/otchety-v1/a/h3_501454233)
* [Пример запроса](/articles/api-documentations/otchety-v1/a/h3_107858276)
* [Расход продуктов по продажам](/articles/api-documentations/otchety-v1/a/v1.APIотчетов-Расходпродуктовпопродажам)
* [Параметры запроса](/articles/api-documentations/otchety-v1/a/h3__6462416)
* [Что в ответе](/articles/api-documentations/otchety-v1/a/h3__390094491)
* [Пример запроса](/articles/api-documentations/otchety-v1/a/h3_2111503716)
* [Отчет по выручке](/articles/api-documentations/otchety-v1/a/v1.APIотчетов-Отчетповыручке)
* [Параметры запроса](/articles/api-documentations/otchety-v1/a/h3_642632569)
* [Что в ответе](/articles/api-documentations/otchety-v1/a/h3_875618913)
* [Пример запроса](/articles/api-documentations/otchety-v1/a/h3_1387997121)
* [План по выручке за день](/articles/api-documentations/otchety-v1/a/h2_228385197)
* [Параметры запроса](/articles/api-documentations/otchety-v1/a/h3_1718516096)
* [Что в ответе](/articles/api-documentations/otchety-v1/a/h3__722715718)
* [Пример запроса](/articles/api-documentations/otchety-v1/a/h3__523120185)
* [Отчет о вхождении товара в блюдо](/articles/api-documentations/otchety-v1/a/v1.APIотчетов-Отчетовхождениитоваравблюдо)
* [Параметры запроса](/articles/api-documentations/otchety-v1/a/h3_771325741)
* [Что в ответе](/articles/api-documentations/otchety-v1/a/h3_868823442)
* [Пример запроса](/articles/api-documentations/otchety-v1/a/h3__1446432940)
* [XSD Отчеты](/articles/api-documentations/otchety-v1/a/h2_1048369972)

## Отчет по складским операциям

Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**reports/storeOperations** |
| --- | --- |

### Параметры запроса

| Название | Значение | Описание |
| --- | --- | --- |
| dateFrom | DD.MM.YYYY | Начальная дата |
| dateTo | DD.MM.YYYY | Конечная дата |
| stores | GUID | Список складов, по которым строится отчет. Если null или empty, строится по всем складам. |
| documentTypes | См. раздел "Расшифровки кодов базовых типов - Типы документов" | Типы документов, которые следует включать. Если null или пуст, включаются все документы. |
| productDetalization | Boolean | Если истина, отчет включает информацию по товарам, но не включает дату. Если ложь - отчет включает каждый документ одной строкой и заполняет суммы документов |
| showCostCorrections | Boolean | Включать ли коррекции себестоимости. Данная опция учитывается только если задан фильтр по типам документов. В противном случае коррекции включаются. |
| presetId | GUID | Id преднастроенного отчета. Если указан, то все настройки, кроме дат, игнорируются. |

### Что в ответе

Структура *storeReportItemDto* (см. XSD Отчет по складским операциям)

### Пример запроса

Параметры передаются явно

| https://localhost:8080/resto/api/reports/storeOperations?key=1ac6b9a3-19a0-7c60-e23b-124dd70d75da&dateFrom=01.09.2014&dateTo=09.09.2014&productDetalization=false&showCostCorrections=false&documentTypes=SALES\_DOCUMENT&documentTypes=INCOMING\_INVOICE&stores=1239d270-1bbe-f64f-b7ea-5f00518ef508&stores=93c5cc1f-4c80-4bea-9100-70053a10e37a |
| --- |

Передается presetId преднастроенного отчета в iikoOffice

| https://localhost:8080/resto/api/reports/storeOperations?key=1ac6b9a3-19a0-7c60-e23b-124dd70d75da&dateFrom=01.12.2014&dateTo=17.12.2014&presetId=bf8886b3-a765-6535-37e4-873bce201482 |
| --- |


```

```


##  Пресеты отчетов по складским операциям

Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**reports/storeReportPresets** |
| --- | --- |

### Что в ответе

Структура *storeReportPresets* (см. XSD Пресеты отчетов по складским операциям)

### Пример запроса

| https://localhost:8080/resto/api/reports/storeReportPresets?key=1ac6b9a3-19a0-7c60-e23b-124dd70d75da |
| --- |

## Расход продуктов по продажам

Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**reports/productExpense** |
| --- | --- |

### Параметры запроса

| Название | Значение | Описание |
| --- | --- | --- |
| department | GUID | Подразделение |
| dateFrom | DD.MM.YYYY | Начальная дата |
| dateTo | DD.MM.YYYY | Конечная дата |
| hourFrom | hh | Час начала интервала выборки в сутках (по умолчанию -1, все время) |
| hourTo | hh | Час окончания интервала выборки в сутках (по умолчанию -1, все время) |

### Что в ответе

Структура *dayDishValue* (см. XSD Расход продуктов по продажам)

### Пример запроса

| https://localhost:8080/resto/api/reports/productExpense?key=1ac6b9a3-19a0-7c60-e23b-124dd70d75da&department=49023e1b-6e3a-6c33-0133-ce1f6f5000b&dateFrom=01.12.2014&dateTo=17.12.2014&hourFrom=12&hourTo=15 |
| --- |

## Отчет по выручке

Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**reports/sales** |
| --- | --- |

### Параметры запроса

| Название | Значение | Описание |
| --- | --- | --- |
| department | GUID | Подразделение |
| dateFrom | DD.MM.YYYY | Начальная дата |
| dateTo | DD.MM.YYYY | Конечная дата |
| hourFrom | hh | Час начала интервала выборки в сутках (по умолчанию -1, все время), по умолчанию -1 |
| hourTo | hh | Час окончания интервала выборки в сутках (по умолчанию -1, все время), по умолчанию -1 |
| dishDetails | Boolean | Включать ли разбивку по блюдам (true/false), по умолчанию false |
| allRevenue | Boolean | Фильтрация по типам оплат (true - все типы, false - только выручка), по умолчанию true |

###  

### Что в ответе

Структура *dayDishValue* (см. XSD Отчет по выручке)

### Пример запроса

| https://localhost:8080/resto/api/reports/sales?key=1ac6b9a3-19a0-7c60-e23b-124dd70d75da&department=49023e1b-6e3a-6c33-0133-cce1f6f5000b&dateFrom=01.12.2014&dateTo=17.12.2014&hourFrom=12&hourTo=15&dishDetails=true&allRevenue=false |
| --- |

###  


```

```


## План по выручке за день

Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**reports/monthlyIncomePlan** |
| --- | --- |

### Параметры запроса

| Название | Значение | Описание |
| --- | --- | --- |
| *department* | GUID | Подразделение |
| *dateFrom* | DD.MM.YYYY | Начальная дата |
| *dateTo* | DD.MM.YYYY | Конечная дата |

###  

### Что в ответе

Структура budgetPlanItemDtoes (см. XSD План по выручке за день)

### Пример запроса

| https://localhost:8080/resto/api/reports/monthlyIncomePlan?key=05e04d9e-26db-a5a2-ba2b-68af4e8a5ed4&department=49023e1b-6e3a-6c33-0133-cce1f6f5000b&dateFrom=01.12.2014&dateTo=18.12.2014 |
| --- |

### 


```
 
```


##  Отчет о вхождении товара в блюдо

Версия iiko: 3.9

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/**reports**/**ingredientEntry** |
| --- | --- |

### Параметры запроса

| Название | Значение | Описание |
| --- | --- | --- |
| department | GUID | Подразделение |
| date | DD.MM.YYYY | На какую дату |
| product | DD.MM.YYYY | Id продукта |
| productArticle | Строка | Артикул продукта (приоритет поиска:*productArticle, product*) |
| includeSubtree | Boolean | Включать ли в отчет строки поддеревьев (по умолчанию false) |

###  

### Что в ответе

Структура ingredientEntryDtoes (см. XSD Отчет о вхождении товара в блюдо)

### Пример запроса

| https://localhost:8080/resto/api/reports/ingredientEntry?key=05e04d9e-26db-a5a2-ba2b-68af4e8a5ed4&date=01.12.2014&product=2c3ab3e1-266d-4667-b344-98b6c194a305&department=49023e1b-6e3a-6c33-0133-cce1f6f5000b&includeSubtree=false |
| --- |

## 

## XSD Отчеты
[+] [XSD Отчет о вхождении товара в блюдо](javascript:void%280%29)
 [-] [XSD Отчет о вхождении товара в блюдо](javascript:void%280%29)
 
```
 %%CH%PRE0%%
```

 [+] [XSD Отчет по выручке](javascript:void%280%29)
 [-] [XSD Отчет по выручке](javascript:void%280%29)
 
```
 %%CH%PRE1%%
```

 [+] [XSD Отчет по складским операциям](javascript:void%280%29)
 [-] [XSD Отчет по складским операциям](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```

 [+] [XSD План по выручке за день](javascript:void%280%29)
 [-] [XSD План по выручке за день](javascript:void%280%29)
 
```
 %%CH%PRE3%%
```

 [+] [XSD Пресеты отчетов по складским операциям](javascript:void%280%29)
 [-] [XSD Пресеты отчетов по складским операциям](javascript:void%280%29)
 
```
 %%CH%PRE4%%
```

 [+] [XSD Расход продуктов по продажам](javascript:void%280%29)
 [-] [XSD Расход продуктов по продажам](javascript:void%280%29)
 
```
 %%CH%PRE5%%
```

 
##  

##


* [Поля OLAP-отчета](/articles/api-documentations/olap-otchety-v2/a/id-ПоляOLAP-отчета-ПоляOLAP-отчета)
* [Параметры запроса](/articles/api-documentations/olap-otchety-v2/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/olap-otchety-v2/a/h3__1412816402)
* [Пример запроса](/articles/api-documentations/olap-otchety-v2/a/h3__232688264)
* [Ответ](/articles/api-documentations/olap-otchety-v2/a/h3_592227717)
* [Общая информация (General info)](/articles/api-documentations/olap-otchety-v2/a/h2_584103350)
* [Тело запроса](/articles/api-documentations/olap-otchety-v2/a/h3_1150399349)
* [Фильтры](/articles/api-documentations/olap-otchety-v2/a/h2__1986441144)
* [Фильтр по значению](/articles/api-documentations/olap-otchety-v2/a/h3__391585873)
* [Фильтр по диапазону](/articles/api-documentations/olap-otchety-v2/a/h3__1715677954)
* [Фильтр по дате](/articles/api-documentations/olap-otchety-v2/a/h3__951638809)
* [Фильтр по дате и времени](/articles/api-documentations/olap-otchety-v2/a/h3_37586638)

##  Поля OLAP-отчета

Версия iiko: 4.1

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | **https://host:port/resto/api/v2**/reports/olap/columns |
| --- | --- |

### Параметры запроса

| Параметры | Описание |
| --- | --- |
| reportType | Тип отчета:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"><li><span style="font-size: 12pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">SALES - По продажам </span></span></li><li><span style="font-size: 12pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">TRANSACTIONS - По транзакциям </span></span></li><li><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;"><span style="font-size: 12pt;">DELIVERIES - По доставкам</span> </span></li></ul> |

### Что в ответе

Json структура списка полей с информацией по возможностям фильтрации, агрегации и группировки.

Устаревшие поля (deprecated) не выводятся.

### Структура списка полей 


```json
"FieldName": {
  "name": "StringValue",
  "type": "StringValue",
  "aggregationAllowed": booleanValue,
  "groupingAllowed": booleanValue,
  "filteringAllowed": booleanValue,
  "tags": [
    "StringValue1",
    "StringValue2",
    ...,
    "StringValueN",
  ]
}
```


| Название | Значение | Описание |
| --- | --- | --- |
| 
```
FieldName 
```
 | Строка | Название колонки отчета. Именно это название используется для получения данных отчета |
| 
```
name 
```
 | Строка | Название колонки отчета в iikoOffice. Справочная информация. |
| type | Строка | Тип поля. Возможны следующие значения:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">ENUM - Перечислимые значения </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">STRING - Строка </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">ID - Внутренний идентификатор объекта в iiko (начиная с 5.0) </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">DATETIME - Дата и время </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">INTEGER - Целое </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">PERCENT - Процент (от 0 до 1) </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">DURATION_IN_SECONDS - Длительность в секундах </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">AMOUNT - Количество </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">MONEY - Денежная сумма </span></span></li></ul> |
| 
```
aggregationAllowed

```
 | true/false | Если true, то по данной колонке можно агрегировать данные |
| 
```
groupingAllowed

```
 | true/false | Если true, то по данной колонке можно группировать данные |
| 
```
filteringAllowed

```
 | true/false | Если true, то по данной колонке можно фильтровать данные |
| 
```
tags

```
 | Список строк | Список категорий отчета, к которому относится данное поле. Справочная информация. Соответствует списку в верхнем правом углу конструктора отчета в iikoOffice. |

###  Пример запроса

https://localhost:8080/resto/api/v2/reports/olap/columns?key=5b119afe-9468-ab68-7d56-c71495e39ee4&reportType=SALES

### Ответ 


```json
{
  "PercentOfSummary.ByCol": {
    "name": "% по столбцу",
    "type": "PERCENT",
    "aggregationAllowed": true,
    "groupingAllowed": false,
    "filteringAllowed": false,
    "tags": [
      "Оплата"
    ]
  },
  "PercentOfSummary.ByRow": {
    "name": "% по строке",
    "type": "PERCENT",
    "aggregationAllowed": true,
    "groupingAllowed": false,
    "filteringAllowed": false,
    "tags": [
      "Оплата"
    ]
  },
  "Delivery.Email": {
    "name": "e-mail доставки",
    "type": "STRING",
    "aggregationAllowed": false,
    "groupingAllowed": true,
    "filteringAllowed": true,
    "tags": [
      "Доставка",
      "Клиент доставки"
    ]
  }
}
```


## Общая информация (General info)

Версия iiko: 4.1

| ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | **https://host:port/resto/api/v2/****reports/olap** |
| --- | --- |

Content-type: Application/json; charset=utf-8

###  Тело запроса


```json
{
  "reportType": "EnumValue",
  "buildSummary": "true",
  "groupByRowFields": [
    "groupByRowFieldName1",
    "groupByRowFieldName2",
    ...,
    "groupByRowFieldNameN"
  ],
  "groupByColFields": [
    "groupByColFieldName1",
    "groupByColFieldName2",
    ...,
    "groupByColFieldNameL"
  ],
  "aggregateFields": [
    "AggregateFieldName1",
    "AggregateFieldName2",
    ...,
    "AggregateFieldNameM"
  ],
  "filters": {
    filter1,
    filter2,
    ...
    filterK
  }
}
```


| Название | Значение | Описание |
| --- | --- | --- |
| 
```
reportType

```
 | SALES<br><br>TRANSACTIONS<br><br>DELIVERIES | Тип отчета:<br><ul style="margin: 10px 0px 0px; padding-left: 22px;"><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">SALES - По продажам </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">TRANSACTIONS - По проводками </span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">DELIVERIES - По доставкам </span></span></li></ul> |
| 
```
buildSummary
```
 | true/false | Параметр появился в **Version(iiko) 5.3.4.** Считать ли итоговые значения. Необязательное, до версии 9.1.2 по умолчанию true, с версии 9.1.2 по умолчанию false. |
| 
```
groupByRowFields 
```
 | Список полей для группировки по строкам | Имена полей, по которым доступна группировка. Список полей можно получить через метод **reports**/**olap**/**columns**, как элементы данного списка используются поля FieldName из возвращаемой **reports**/**olap**/**columns** структуры. Для указания в данном списке доступны поля, у которых **groupingAllowed** = **true** |
| 
```
groupByColFields 
```
 | Список полей для группировки по столбцам | Необязательный. Имена полей, по которым доступна группировка. Список полей можно получить через метод **reports**/**olap**/**columns**, как элементы данного списка используются поля FieldName из возвращаемой **reports**/**olap**/**columns** структуры. Для указания в данном списке доступны поля, у которых **groupingAllowed** = **true** |
| 
```
aggregateFields 
```
 | Список полей для агрегации | Имена полей, по которым доступна агрегация. Список полей можно получить через метод **reports**/**olap**/**columns**, как элементы данного списка используются поля FieldName из возвращаемой **reports**/**olap**/**columns** структуры. Для указания в данном списке доступны поля, у которых **filteringAllowed**= **true** |
| 
```
filters 
```
 | Список фильтров | См. описание структуры фильтров. Для указания в данном списке доступны поля, у которых **filteringAllowed** = **true** |

| ![Information](/resources/Storage/api-documentations/info.png) | Поля агрегации, учитывающие начальный остаток товара и денежный остаток (StartBalance.Amount, StartBalance.Money, FinalBalance.Amount, FinalBalance.Money) вычисляются суммированием всей таблицы проводок **за все время** работы системы (всей базы данных) без каких-либо оптимизаций. То есть, такой запрос может выполняться очень долго и замедлять работу сервера.<br>Если начальный остаток необходим, оставляйте в этом OLAP-запросе только те поля группировки, по которым он действительно необходим (как правило, это Account.Name и Product.Name), и вызывайте такой запрос **как можно реже** и в **не рабочее** время.<br><br>В 5.2 добавлено API для быстрого получения остатков: Отчеты по балансам. Во всех случаях рекомендуется пользоваться им вместо OLAP.<br><br>В 5.5 OLAP-отчеты с остатками оптимизированы с использованием балансовых таблиц ATransactionSum, ATransactionBalance, при условии, что применяются группировки и фильтры по полям из этих таблиц, см. признак StartBalanceOptimizable в описании полей.<br><br>То есть, правильно составленный запрос приведет к суммированию не всей таблицы проводок, а только лишь открытого периода. Обратите особое внимание на то, что оптимизировано только поле Account.Name (счет "текущей" стороны проводки, в том числе склад), а не Store (первый попавшийся "склад" проводки, взятый из: левой, правой части проводки, строки документа или самого документа). |
| --- | --- |

## Фильтры

###  Фильтр по значению 


```json
"FieldName": {
"filterType": "filterTypeEnum",
"values": ["Value1","Value2",...,"ValueN"]
}
```


Работает для полей с типами:

* ENUM
* STRING

| Название | Значение | Описание |
| --- | --- | --- |
| 
```
FieldName

```
 | Имя поля для фильтрации | Поле FieldName из возвращаемой **reports**/**olap**/**columns** структуры |
| 
```
filterType

```
 | IncludeValues / ExcludeValues | IncludeValues - в фильтрации участвуют только перечисленные значения поля<br><br>ExcludeValues - в фильтрации участвуют значения поля, за исключением перечисленных |
| 
```
values 
```
 | Список значений поля | В зависимости от типа поля, это могут быть или enum из Расшифровки кодов базовых типов или текстовое значение поля |


```json
"DeletedWithWriteoff": {
"filterType": "ExcludeValues",
"values": ["DELETED_WITH_WRITEOFF","DELETED_WITHOUT_WRITEOFF"]
},
"OrderDeleted": {
"filterType": "IncludeValues",
"values": ["NOT_DELETED"]
}
```


###  Фильтр по диапазону 


```json
"FieldName": {
"filterType": "Range",
"from": Value1,
"to": Value2,
"includeLow": booleanValue,
"includeHigh": booleanValue
}
```


Работает для полей с типами:

* INTEGER
* PERCENT
* AMOUNT
* MONEY

| Название | Значение | Описание |
| --- | --- | --- |
| 
```
FieldName

```
 | Имя поля для фильтрации | Поле FieldName из возвращаемой **reports**/**olap**/**columns** структуры |
| 
```
filterType

```
 | Range | Фильтр по диапазону значений |
| from | Нижняя граница диапазона | Значение в формате, соответствующем типу поля |
| to | Верхняя граница диапазона | Значение в формате, соответствующем типу поля |
| includeLow | true/false | Необязательное, по умолчанию true<br><br>true - нижняя граница диапазона включается в фильтр<br><br>false - нижняя граница диапазона не включается в фильтр |
| includeHigh | true/false | Необязательное, по умолчанию false<br><br>true - верхняя граница диапазона включается в фильтр<br><br>false - верхняя граница диапазона не включается в фильтр |


```json
"SessionNum": {
"filterType": "Range",
"from": 758,
"to": 760,
"includeHigh": true
}
```


###  Фильтр по дате 


```json
"FieldName": {
"filterType": "DateRange",
"periodType": "periodTypeEnum",
"from": "fromDateTime",
"to": "toDateTime",
"includeLow": booleanValue,
"includeHigh": booleanValue
}
```


Работает для полей с типами:

* DATETIME
* DATE

| Название | Значение | Описание |
| --- | --- | --- |
| 
```
FieldName 
```
 | Имя поля для фильтрации | Поле FieldName из возвращаемой **reports**/**olap**/**columns** структуры |
| 
```
filterType

```
 | DateRange | Фильтр по диапазону значений |
| 
```
periodType

```
 | CUSTOM - вручную<br><br>OPEN\_PERIOD - текущий открытый период<br><br>TODAY - сегодня<br><br>YESTERDAY - вчера<br><br>CURRENT\_WEEK - текущая неделя<br><br>CURRENT\_MONTH - текущий месяц<br><br>CURRENT\_YEAR - текущий год<br><br>LAST\_WEEK - прошлая неделя<br><br>LAST\_MONTH - прошлый месяц<br><br>LAST\_YEAR - прошлый год | Если период CUSTOM, то период задается вручную, используются поля from, to, includeLow, includeHigh<br><br>Для остальных типов периода данные параметры игнорируются (можно не использовать), кроме параметра from, его передача обязательна, его значение может быть любым. |
| from | Начальная дата | Дата в формате yyyy-MM-dd'T'HH:mm:ss.SSS |
| to | Конечная дата | Дата в формате yyyy-MM-dd'T'HH:mm:ss.SSS |
| includeLow | true/false | Необязательное, по умолчанию **true**<br><br>true - нижняя граница диапазона включается в фильтр<br><br>false - нижняя граница диапазона не включается в фильтр |
| includeHigh | true/false | Необязательное, по умолчанию **false**<br>true - верхняя граница диапазона включается в фильтр. Внимание: включение верхней границы имеет смысл только у полей, выдающих **округленную** **ДАТУ**, а не **ДАТУ**-**ВРЕМЯ**.<br><br>false - верхняя граница диапазона не включается в фильтр |

| ![Information](/resources/Storage/api-documentations/info.png) | В OLAP-отчете по проводкам ("reportType": "TRANSACTIONS") для фильтрации по \*дате\* рекомендуется использовать поле DateTime.DateTyped(или DateTime.Typed — но это дата-время)<br><br>В OLAP-отчете по продажам, а также доставкам используется поле OpenDate.Typed.<br><br>В 4.1 вместо отсутствующих полей OpenDate.Typed и DateTime.DateTyped используются поля OpenDate и DateTime.OperDayFilter соответственно.<br><br>Начиная с 5.5, каждый OLAP-запрос должен содержать фильтр по дате |
| --- | --- |


```json
"OpenDate.Typed": {
"filterType": "DateRange",
"periodType": "CUSTOM",
"from": "2014-01-01T00:00:00.000",
"to": "2014-01-03T00:00:00.000" 
}
```


### Фильтр по дате и времени


```xml
"filters": { 
"OpenDate.Typed": { 
"filterType": "DateRange", 
"periodType": "CUSTOM", 
"from": "2018-09-04", 
"to": "2018-09-04", 
"includeLow": true, 
"includeHigh": true 
},
"OpenTime": {
"filterType": "DateRange",
"periodType": "CUSTOM",
"from": "2018-09-04T01:00:00.000",
"to": "2018-09-04T23:00:00.000",
"includeLow": true,
"includeHigh": true
}
}
```


#### Ответ


```json
{
  "data": [
    {
      "GroupFieldName1": "Value11",
      "GroupFieldName2": "Value12",
       ...,
      "GroupFieldNameN": "Value1N",
      "AggregateFieldName1": "Value11",
      "AggregateFieldName1": "Value12",
       ...,
      "AggregateFieldNameM": "Value1M"
    },
    ...,
    {
      "GroupFieldName1": "ValueK1",
      "GroupFieldName2": "ValueK2",
       ...,
      "GroupFieldNameN": "ValueKN",
      "AggregateFieldName1": "ValueK1",
      "AggregateFieldName1": "ValueK2",
       ...,
      "AggregateFieldNameM": "ValueKM"
    }
  ],
  "summary": [
   [
      {
         
      },
      {
        "AggregateFieldName1": "TotalValue1",
        "AggregateFieldName2": "TotalValue2",
        ...,
        "AggregateFieldNameM": "TotalValueM"
      }
    ],
    [
      {
        "GroupFieldName1": "Value11"
      },
      {
        "AggregateFieldName1": "TotalValue11",
        "AggregateFieldName2": "TotalValue12",
        ...,
        "AggregateFieldNameM": "TotalValue1M"
      }
    ],
    ...,
   [
      {
        "GroupFieldName1": "Value1",
        ...
        "GroupFieldNameN": "ValueN",
      },
      {
        "AggregateFieldName1": "TotalValue11",
        "AggregateFieldName2": "TotalValue12",
        ...,
        "AggregateFieldNameM": "TotalValue1M"
      }
   ],
   ...
  ]
}
```


| Название | Значение | Описание |
| --- | --- | --- |
| data | Данные отчета | Линейные данные отчета (построчно), одна запись внутри блока соответствует одной строке в гриде iikoOffice |
| summary | Промежуточные и общие итоги по отчету | Список блоков, состоящих из двух структур.<br><ol style="margin: 10px 0px 0px; padding-left: 22px;"><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">В первой структуре - список полей, по которым собраны промежуточные итоги, в качестве элементов этой структуры представлены поля, которые используются для группировки. Количество элементов в структуре отличается и может быть: </span></span><ol style="padding-left: 22px;"><li><span style="font-size: 10pt;"><span style="line-height: 1.42857; font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">пустым - это значит, что во втором блоке представлены общие итоги по отчету</span></span></li><li><span style="font-size: 10pt;"><span style="line-height: 1.42857; font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">список полей группировки, по которым собраны промежуточные итоги. Список имеет длину от 1 до числа полей группировки. Поля добавляются к списку в порядке их следования в запросе.&#160;</span></span></li></ol></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">Во второй - собственно промежуточные итоги. В качестве элементов данной структуры представлены поля, которые используются для агрегации. Количество элементов этой структуры фиксировано и равно количеству полей для агрегации.</span></span></li><li><span style="font-size: 10pt;"><span style="font-family: &quot;Segoe UI&quot;, Frutiger, &quot;Frutiger Linotype&quot;, &quot;Dejavu Sans&quot;, &quot;Helvetica Neue&quot;, Arial, sans-serif;">При параметре запроса <em>summary = false (olap, olap_presetId). </em>&quot;summary&quot;: [ ] будет пустой. C <strong>Version (iiko) 5.3</strong></span> </span></li></ol> |

## 

## 

##

* [Балансы по счетам, контрагентам и подразделениям](/articles/api-documentations/otchety-vv2/a/h2_1559205636)
* [Параметры запроса](/articles/api-documentations/otchety-vv2/a/h3__998506674)
* [Что в ответе](/articles/api-documentations/otchety-vv2/a/h3_1491674086)
* [Пример запроса и результата](/articles/api-documentations/otchety-vv2/a/h3_1561844723)
* [Остатки на складах](/articles/api-documentations/otchety-vv2/a/h2_2138999405)
* [Параметры запроса](/articles/api-documentations/otchety-vv2/a/h3__397291684)
* [Что в ответе](/articles/api-documentations/otchety-vv2/a/h3_501454233)
* [Пример запроса и результата](/articles/api-documentations/otchety-vv2/a/h3_1387997121)
* [Получение обновлений состояния на 3 регистре](/articles/api-documentations/otchety-vv2/a/APIОтчетпобалансуна3регистреЕГАИС%28акцизныемарки%29-Получениеобновленийсостоянияна3регистре)
* [Параметры запроса](/articles/api-documentations/otchety-vv2/a/APIОтчетпобалансуна3регистреЕГАИС%28акцизныемарки%29-Параметры)
* [Пример запроса и результат](/articles/api-documentations/otchety-vv2/a/h3__1082861155)

## Балансы по счетам, контрагентам и подразделениям

Версия iiko: 5.2

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/reports/balance/counteragents |
| --- | --- |

### Параметры запроса

| Параметр | Описание |
| --- | --- |
| **timestamp** | учетная-дата время отчета в формате yyyy-MM-dd'T'HH:mm:ss (обязательный) |
| **account** | id счета для фильтрации (необязательный, можно указать несколько) |
| **counteragent** | id контрагента для фильтрации (необязательный, можно указать несколько) |
| **department** | id подразделения для фильтрации (необязательный, можно указать несколько) |

### **Что в ответе**

Возвращает денежные балансы по указанным счетам, контрагентам и подразделениям на заданную учетную дату-время.

См. ниже пример результата.

### **Пример запроса и результата**

**Запрос**

https://localhost:9080/resto/api/v2/reports/balance/counteragents?key=88e98be8-89c4-766b-a319-dc6d1f3b8cec&timestamp=2016-10-19T23:10:10
[+] [Результат](javascript:void%280%29)
 [-] [Результат](javascript:void%280%29)
 
```
 %%CH%PRE0%%
```


## Остатки на складах

Версия iiko: 5.2

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/reports/balance/stores |
| --- | --- |

### Параметры запроса

| Параметр | Описание |
| --- | --- |
| **timestamp** | учетная-дата время отчета в формате yyyy-MM-dd'T'HH:mm:ss (обязательный) |
| **department** | id подразделения для фильтрации (необязательный, можно указать несколько) |
| **store** | id склада для фильтрации (необязательный, можно указать несколько) |
| **product** | id элемента номенклатуры для фильтрации (необязательный, можно указать несколько) |

### **Что в ответе**

Возвращает количественные (amount) и денежные (sum) остатки товаров (product) на складах (store) на заданную учетную дату-время.

См. ниже пример результата.

### **Пример запроса и результата**

**Запрос**

https://localhost:9080/resto/api/v2/reports/balance/stores?key=88e98be8-89c4-766b-a319-dc6d1f3b8cec&timestamp=2016-10-18T23:10:10

**Результат**

**
Код

```
[
    {
        "store": "657ded9f-a1a3-416c-91a4-5a2fc78e8a36",
        "product": "f464e4d4-cf9c-49a2-9e18-1227b41a3801",
        "amount": 123,
        "sum": 64083
    },
    {
        "store": "1239d270-1bbe-f64f-b7ea-5f00518ef508",
        "product": "c6d6c2f2-7e48-4ac9-84ca-1f566c3a941e",
        "amount": 29.45,
        "sum": 1159.3
    },
    {
        "store": "1239d270-1bbe-f64f-b7ea-5f00518ef508",
        "product": "f464e4d4-cf9c-49a2-9e18-1227b41a3801",
        "amount": 15,
        "sum": 1221
    }
]
```
**

# Отчет по балансу на 3 регистре ЕГАИС (акцизные марки)

## Получение обновлений состояния на 3 регистре

Версия iiko: 7.4

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/reports/egais/marks/list |
| --- | --- |

### Параметры запроса

| **Название** | **Тип данных** | **Обязательный** | **Описание** |
| --- | --- | --- | --- |
| **fsRarId** | List&lt;String&gt; | Нет, по умолчанию<br><br>возвращаются данные для всех организаций. | Список РАР-идентификаторов организаций, баланс которых запрашивается |
| **revisionFrom** | int | Нет, по умолчанию -1 | Номер ревизии, начиная с которой необходимо отфильтровать сущности.<br><br>Не включающий саму ревизию, т.е. ревизия объекта &gt; revisionFrom. |

### **Пример запроса и результат**

**Запрос**

https://localhost:8080/resto/api/v2/reports/egais/marks/list?fsRarId=030000455388&fsRarId=030000455399&revisionFrom=100
 [+] [Пример результата](javascript:void%280%29)
 [-] [Пример результата](javascript:void%280%29)
 
```
 %%CH%PRE2%%
```

 
**Описание полей**

| **Поле** | **Тип данных** | **Описание** |
| **revision** | int | Ревизия, по которую (включительно) выданы данные |
| **fullUpdate** | Boolean | true - пакет является "полным обновлением", то есть, клиент должен удалить все имеющие данные, не перечисленные явно.<br><br>false - пакет является "частичным обновлением", клиент должен заменить закешированные записи с теми же ключами. |
| **marksByBRegId** | Map&lt;String, EgaisBRegDto&gt; | Название вложенного поля - BRegId - Идентификатор Справки Б (Справки 2)<br><br>Значение вложенного поля:<br> <br><br> <br><br>| Поле | Тип данных | Описание |<br>| --- | --- | --- |<br>| **dateTo** | Дата в формате yyyy-MM-dd'T'HH:mm:ss.SSS | Дата-время актуальности состояния:<br><ul><li><span style="font-size: 10pt;">MAX_DATE, если марка еще не списана</span></li><li><p><span style="font-size: 10pt;">Дата-время списания + MAX_MARK_KEEP_DAYS дней, если списана документом, находящимся в нередактируемом статусе</span></p></li><li><span style="font-size: 10pt;">Дата-время удаления последнего известного EgaisMarkTableItem (информация о движении акцизной марки) (для отсутствующих марок).</span></li></ul> | |
| --- | --- | --- |
| **marksWrittenOff** | Map&lt;String, EgasMarkStateDto&gt; | Множество акцизных марок, списанных с баланса организации.<br><br>Название вложенного поля - полный текст акцизной марки.<br><br>Значения вложенного поля:<br> <br><br> <br><br>| Параметр | Тип, формат | Описание |<br>| --- | --- | --- |<br>| **dateTo** | Дата в формате yyyy-MM-dd'T'HH:mm:ss.SSS | Дата-время актуальности состояния:<br><ul><li><span style="font-size: 10pt;">MAX_DATE, если марка еще не списана</span></li><li><p><span style="font-size: 10pt;">Дата-время списания + MAX_MARK_KEEP_DAYS дней, если списана документом, находящимся в нередактируемом статусе</span></p></li><li><span style="font-size: 10pt;">Дата-время удаления последнего известного EgaisMarkTableItem (информация о движении акцизной марки) (для отсутствующих марок).</span></li></ul> | |
| --- | --- | --- |


# Примеры вызова OLAP-отчетов по продажам
 [+] [Выручка по типам оплат](javascript:void%280%29)
 [-] [Выручка по типам оплат](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/reports/olap?key=99939171-551a-f54b-5163-366e773c40ac |
| --- | --- |

#### Тело запроса


Код

```

{
  "reportType": "SALES",
  "groupByRowFields": [
    "PayTypes",
    "OpenDate"
  ],
  "aggregateFields": [
    "GuestNum",
    "DishSumInt",
    "DishDiscountSumInt",
    "UniqOrderId"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "ExcludeValues",
      "values": ["DELETED_WITH_WRITEOFF","DELETED_WITHOUT_WRITEOFF"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}
```


#### Ответ


Код

```

{
  "data": [
    {
      "DishDiscountSumInt": 0,
      "DishSumInt": 1600,
      "GuestNum": 2,
      "OpenDate": "2014.01.01",
      "PayTypes": "(без оплаты)",
      "UniqOrderId": 2
    },
    {
      "DishDiscountSumInt": 0,
      "DishSumInt": 1835,
      "GuestNum": 3,
      "OpenDate": "2014.01.02",
      "PayTypes": "(без оплаты)",
      "UniqOrderId": 3
    },
    {
      "DishDiscountSumInt": 179786.5,
      "DishSumInt": 190460,
      "GuestNum": 179,
      "OpenDate": "2014.01.01",
      "PayTypes": "Наличные",
      "UniqOrderId": 189
    },
    {
      "DishDiscountSumInt": 274268,
      "DishSumInt": 285355,
      "GuestNum": 263,
      "OpenDate": "2014.01.02",
      "PayTypes": "Наличные",
      "UniqOrderId": 278
    },
    {
      "DishDiscountSumInt": 6735,
      "DishSumInt": 6735,
      "GuestNum": 5,
      "OpenDate": "2014.01.01",
      "PayTypes": "безналичный расчет",
      "UniqOrderId": 5
    },
    {
      "DishDiscountSumInt": 5050,
      "DishSumInt": 5050,
      "GuestNum": 5,
      "OpenDate": "2014.01.02",
      "PayTypes": "безналичный расчет",
      "UniqOrderId": 5
    }
  ],
  "summary": [
    [
      {
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 3435,
        "GuestNum": 5,
        "UniqOrderId": 5
      }
    ],
    [
      {
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035,
        "GuestNum": 457,
        "UniqOrderId": 482
      }
    ],
    [
      {
        "OpenDate": "2014.01.02",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 1835,
        "GuestNum": 3,
        "UniqOrderId": 3
      }
    ],
    [
      {
        "OpenDate": "2014.01.01",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 1600,
        "GuestNum": 2,
        "UniqOrderId": 2
      }
    ],
    [
      {
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 179786.5,
        "DishSumInt": 190460,
        "GuestNum": 179,
        "UniqOrderId": 189
      }
    ],
    [
      {
        "OpenDate": "2014.01.02",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 274268,
        "DishSumInt": 285355,
        "GuestNum": 263,
        "UniqOrderId": 278
      }
    ],
    [
      {
        "OpenDate": "2014.01.02",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 5050,
        "DishSumInt": 5050,
        "GuestNum": 5,
        "UniqOrderId": 5
      }
    ],
    [
      {
        "OpenDate": "2014.01.01",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 6735,
        "DishSumInt": 6735,
        "GuestNum": 5,
        "UniqOrderId": 5
      }
    ],
    [
      {
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 454054.5,
        "DishSumInt": 475815,
        "GuestNum": 442,
        "UniqOrderId": 467
      }
    ],
    [
      {
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 11785,
        "DishSumInt": 11785,
        "GuestNum": 10,
        "UniqOrderId": 10
      }
    ]
  ]
}
```

 
```


```

 [+] [Выручка за блюда по кассам](javascript:void%280%29)
 [-] [Выручка за блюда по кассам](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/reports/olap?key=99939171-551a-f54b-5163-366e773c40ac |
| --- | --- |

#### Тело запроса


Код

```

{
  "reportType": "SALES",
  "groupByRowFields": [
    "DishName",
    "OpenDate",
    "CashRegisterName"
  ],
  "aggregateFields": [
    "DishSumInt",
    "DishDiscountSumInt"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}

```


#### Ответ


```json
{
  "data": [
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 227.5,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 459.76,
      "DishName": "Dish_Name",
      "DishSumInt": 650,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 195,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 102.92,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 390,
      "DishName": "Dish_Name",
      "DishSumInt": 390,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 390,
      "DishName": "Dish_Name",
      "DishSumInt": 390,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 227.5,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 165,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 700,
      "DishName": "Dish_Name",
      "DishSumInt": 700,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 70,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 355.88,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 450,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 900,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 450,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 450,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 337.5,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 756,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1280,
      "DishName": "Dish_Name",
      "DishSumInt": 1280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1280,
      "DishName": "Dish_Name",
      "DishSumInt": 1280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60,
      "DishName": "Dish_Name",
      "DishSumInt": 60,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 119.96,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 860,
      "DishName": "Dish_Name",
      "DishSumInt": 860,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 403.56,
      "DishName": "Dish_Name",
      "DishSumInt": 630,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 630,
      "DishName": "Dish_Name",
      "DishSumInt": 630,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 315,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 410.29,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 514.1,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 94.9,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 690,
      "DishName": "Dish_Name",
      "DishSumInt": 690,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 172.5,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 940,
      "DishName": "Dish_Name",
      "DishSumInt": 940,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 470,
      "DishName": "Dish_Name",
      "DishSumInt": 470,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 940,
      "DishName": "Dish_Name",
      "DishSumInt": 1410,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 470,
      "DishName": "Dish_Name",
      "DishSumInt": 470,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 760,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1520,
      "DishName": "Dish_Name",
      "DishSumInt": 1520,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 165,
      "DishName": "Dish_Name",
      "DishSumInt": 165,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 165,
      "DishName": "Dish_Name",
      "DishSumInt": 165,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 350,
      "DishName": "Dish_Name",
      "DishSumInt": 350,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1578.8,
      "DishName": "Dish_Name",
      "DishSumInt": 1800,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1445.89,
      "DishName": "Dish_Name",
      "DishSumInt": 1500,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2700,
      "DishName": "Dish_Name",
      "DishSumInt": 2700,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 315,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 840,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 508.24,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 355.88,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegis 2000 terName": "Касса Одинцово ",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 860,
      "DishName": "Dish_Name",
      "DishSumInt": 860,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 165,
      "DishName": "Dish_Name",
      "DishSumInt": 165,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 344.89,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 840,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 315,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 840,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 550,
      "DishName": "Dish_Name",
      "DishSumInt": 550,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1100,
      "DishName": "Dish_Name",
      "DishSumInt": 1100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1100,
      "DishName": "Dish_Name",
      "DishSumInt": 1100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 550,
      "DishName": "Dish_Name",
      "DishSumInt": 550,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2721.98,
      "DishName": "Dish_Name",
      "DishSumInt": 2750,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 550,
      "DishName": "Dish_Name",
      "DishSumInt": 550,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1100,
      "DishName": "Dish_Name",
      "DishSumInt": 1100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2200,
      "DishName": "Dish_Name",
      "DishSumInt": 2200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 125,
      "DishName": "Dish_Name",
      "DishSumInt": 125,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 125,
      "DishName": "Dish_Name",
      "DishSumInt": 125,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 225,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 215.25,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 402.16,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60,
      "DishName": "Dish_Name",
      "DishSumInt": 60,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 780,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 135,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02 2000 "
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 148.66,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 860,
      "DishName": "Dish_Name",
      "DishSumInt": 860,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1290,
      "DishName": "Dish_Name",
      "DishSumInt": 1290,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 510,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1530,
      "DishName": "Dish_Name",
      "DishSumInt": 1530,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 510,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1530,
      "DishName": "Dish_Name",
      "DishSumInt": 1530,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 832.78,
      "DishName": "Dish_Name",
      "DishSumInt": 1020,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1020,
      "DishName": "Dish_Name",
      "DishSumInt": 1020,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 510,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 690,
      "DishName": "Dish_Name",
      "DishSumInt": 690,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1050,
      "DishName": "Dish_Name",
      "DishSumInt": 1050,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 350,
      "DishName": "Dish_Name",
      "DishSumInt": 350,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 520,
      "DishName": "Dish_Name",
      "DishSumInt": 520,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60,
      "DishName": "Dish_Name",
      "DishSumInt": 60,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 70,
      "DishName": "Dish_Name",
      "DishSumInt": 70,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 154.67,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 380,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 760,
      "DishName": "Dish_Name",
      "DishSumInt": 760,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 380,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 380,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 520,
      "DishName": "Dish_Name",
      "DishSumInt": 520,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2160,
      "DishName": "Dish_Name",
      "DishSumInt": 2430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1350,
      "DishName": "Dish_Name",
      "DishSumInt": 1350,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1350,
      "DishName": "Dish_Name",
      "DishSumInt": 1350,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 3700.25,
      "DishName": "Dish_Name",
      "DishSumInt": 3780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 810,
      "DishName": "Dish_Name",
      "DishSumInt": 810,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 810,
      "DishName": "Dish_Name",
      "DishSumInt": 810,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterN 2000 ame": "Касса Подольск",
      "DishDiscountSumInt": 995.62,
      "DishName": "Dish_Name",
      "DishSumInt": 1080,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 858.43,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1500,
      "DishName": "Dish_Name",
      "DishSumInt": 1500,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1200,
      "DishName": "Dish_Name",
      "DishSumInt": 1200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1080,
      "DishName": "Dish_Name",
      "DishSumInt": 1080,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1350,
      "DishName": "Dish_Name",
      "DishSumInt": 1350,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1350,
      "DishName": "Dish_Name",
      "DishSumInt": 1350,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 47.35,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 70,
      "DishName": "Dish_Name",
      "DishSumInt": 70,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 70,
      "DishName": "Dish_Name",
      "DishSumInt": 70,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 275,
      "DishName": "Dish_Name",
      "DishSumInt": 330,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 380.25,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 127.5,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300.87,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1290,
      "DishName": "Dish_Name",
      "DishSumInt": 1290,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1290,
      "DishName": "Dish_Name",
      "DishSumInt": 1290,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 860,
      "DishName": "Dish_Name",
      "DishSumInt": 860,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1290,
      "DishName": "Dish_Name",
      "DishSumInt": 1290,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 457.5,
      "DishName": "Dish_Name",
      "DishSumInt": 610,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 610,
      "DishName": "Dish_Name",
      "DishSumInt": 610,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 610,
      "DishName": "Dish_Name",
      "DishSumInt": 610,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1674.26,
      "DishName": "Dish_Name",
      "DishSumInt": 1830,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 273.04,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 356.25,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 350,
      "DishName": "Dish_Name",
      "DishSumInt": 375,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 656.71,
      "DishName": "Dish_Name",
      "DishSumInt": 675,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 75,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 112.5,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 75,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 700,
      "DishName": "Dish_Name",
      "DishSumInt": 700,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 315,
      "DishName": "Dish_Name",
      "DishSumInt": 350,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 331.13,
      "DishName": "Dish_Name",
      "DishSumInt": 350,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 884.39,
      "DishName": "Dish_Name",
      "DishSumInt": 980,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 330,
      "DishName": "Dish_Name",
      "DishSumInt": 440,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 330,
      "DishName": "Dish_Name",
      "DishSumInt": 330,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 587.21,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 330,
      "DishName": "Dish_Name",
      "DishSumInt": 330,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 85.85,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 720,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 642.16,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 131.48,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 315,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1015.01,
      "DishName": "Dish_Name",
      "DishSumInt": 1110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 740,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1110,
      "DishName": "Dish_Name",
      "DishSumInt": 1110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 740,
      "DishName": "Dish_Name",
      "DishSumInt": 740,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1364.38,
      "DishName": "Dish_Name",
      "DishSumInt": 1480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 182.6,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1000,
      "DishName": "Dish_Name",
      "DishSumInt": 1000,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 500,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1000,
      "DishName": "Dish_Name",
      "DishSumInt": 1000,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "Dis 2000 hName": "Кроненбург 1664 Бланк 0,5",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1113.1,
      "DishName": "Dish_Name",
      "DishSumInt": 1300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 585,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 189.9,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 780,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 715,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 780,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 459.64,
      "DishName": "Dish_Name",
      "DishSumInt": 520,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 37.56,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 50,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 113.94,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 4355.56,
      "DishName": "Dish_Name",
      "DishSumInt": 4800,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 3200,
      "DishName": "Dish_Name",
      "DishSumInt": 3200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 6302.44,
      "DishName": "Dish_Name",
      "DishSumInt": 6400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1600,
      "DishName": "Dish_Name",
      "DishSumInt": 1600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 980,
      "DishName": "Dish_Name",
      "DishSumInt": 1600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 408.24,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 870,
      "DishName": "Dish_Name",
      "DishSumInt": 870,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 870,
      "DishName": "Dish_Name",
      "DishSumInt": 870,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 290,
      "DishName": "Dish_Name",
      "DishSumInt": 290,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 290,
      "DishName": "Dish_Name",
      "DishSumInt": 290,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1385.85,
      "DishName": "Dish_Name",
      "DishSumInt": 2220,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 740,
      "DishName": "Dish_Name",
      "DishSumInt": 740,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2893.26,
      "DishName": "Dish_Name",
      "DishSumInt": 2960,
      "OpenDate": "2014.01.02"
    },
    {
      " 2000 CashRegisterName": "Касса Егорьевск",
      "DishDiscountSumInt": 740,
      "DishName": "Dish_Name",
      "DishSumInt": 740,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 740,
      "DishName": "Dish_Name",
      "DishSumInt": 740,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2837.21,
      "DishName": "Dish_Name",
      "DishSumInt": 2960,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 510,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 157.5,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 138.44,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 73.28,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 106.3,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 70,
      "DishName": "Dish_Name",
      "DishSumInt": 70,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 108.5,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 26.83,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1079.62,
      "DishName": "Dish_Name",
      "DishSumInt": 1100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 135.41,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 275,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 418.82,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 900,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 900,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 450,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1800,
      "DishName": "Dish_Name",
      "DishSumInt": 1800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 900,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 351.76,
      "DishName": "Dish_Name",
      "DishSumInt": 650,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2600,
      "DishName": "Dish_Name",
      "DishSumInt": 2600,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1300,
      "DishName": "Dish_Name",
      "DishSumInt": 1300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 650,
      "DishName": "Dish_Name",
      "DishSumInt": 650,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 650,
      "DishName": "Dish_Name",
      "DishSumInt": 650,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2600,
      "DishName": "Dish_Name",
      "DishSumInt": 2600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 192.5,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 700,
      "DishName": "Dish_Name",
      "DishSumInt": 700,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2100,
      "DishName": "Dish_Name",
      "DishSumInt": 2100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 684.15,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 722.65,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 780,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 436.8,
      "DishName": "Dish_Name",
      "DishSumInt": 520,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 176.77,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 840,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 18.75,
      "DishName": "Dish_Name",
      "DishSumInt": 25,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 9100,
      "DishName": "Dish_Name",
      "DishSumInt": 9100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2600,
      "DishName": "Dish_Name",
      "DishSumInt": 2600,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 3900,
      "DishName": "Dish_Name",
      "DishSumInt": 3900,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2600,
      "DishName": "Dish_Name",
      "DishSumInt": 2600,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 16900,
      "DishName": "Dish_Name",
      "DishSumInt": 18200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1300,
      "DishName": "Dish_Name",
      "DishSumInt": 1300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 5200,
      "DishName": "Dish_Name",
      "DishSumInt": 5200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 5200,
      "DishName": "Dish_Name",
      "DishSumInt": 5200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 18.75,
      "DishName": "Dish_Name",
      "DishSumInt": 25,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1500,
      "DishName": "Dish_Name",
      "DishSumInt": 1500,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 519.12,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 245.9,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 158.13,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1406.75,
      "DishName": "Dish_Name",
      "DishSumInt": 1440,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 960,
      "DishName": "Dish_Name",
      "DishSumInt": 960,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 421.46,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 960,
      "DishName": "Dish_Name",
      "DishSumInt": 960,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1360,
      "DishName": "Dish_Name",
      "DishSumInt": 1360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 680,
      "DishName": "Dish_Name",
      "DishSumInt": 680,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2040,
      "DishName": "Dish_Name",
      "DishSumInt": 2040,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 680,
      "DishName": "Dish_Name",
      "DishSumInt": 680,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 56.25,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 550,
      "DishName": "Dish_Name",
      "DishSumInt": 550,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1320,
      "DishName": "Dish_Name",
      "DishSumInt": 1320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 75,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscoun 2000 tSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 30,
      "DishName": "Dish_Name",
      "DishSumInt": 30,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 969.73,
      "DishName": "Dish_Name",
      "DishSumInt": 1080,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 83.9,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 264,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 83.9,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 500,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1196.63,
      "DishName": "Dish_Name",
      "DishSumInt": 1250,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 125,
      "DishName": "Dish_Name",
      "DishSumInt": 125,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 50,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 502.5,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 860,
      "DishName": "Dish_Name",
      "DishSumInt": 860,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1586.76,
      "DishName": "Dish_Name",
      "DishSumInt": 1710,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1710,
      "DishName": "Dish_Name",
      "DishSumInt": 1710,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 1140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1140,
      "DishName": "Dish_Name",
      "DishSumInt": 1140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 222.92,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 285.39,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 127.5,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 510,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 141.79,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 203.54,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 321.25,
      "DishName": "Dish_Name",
      "DishSumInt": 2000400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 148.09,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 380,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 430,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 243.97,
      "DishName": "Dish_Name",
      "DishSumInt": 430,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 105,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 105,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 500,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 800,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 595.74,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 79.46,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20,
      "DishName": "Dish_Name",
      "DishSumInt": 20,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 40,
      "DishName": "Dish_Name",
      "DishSumInt": 40,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.01"
    },
    {
      "Cas 2000 hRegisterName": "Касса Егорьевск",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 198.01,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 65,
      "DishName": "Dish_Name",
      "DishSumInt": 65,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 94.7,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 50,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 400,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 50,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 327.54,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 414.57,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 45,
      "DishName": "Dish_Name",
      "DishSumInt": 45,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 36.88,
      "DishName": "Dish_Name",
      "DishSumInt": 45,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 45,
      "DishName": "Dish_Name",
      "DishSumInt": 45,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 75,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 61.48,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 110,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90.16,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230.63,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 109.18,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 750,
      "DishName": "Dish_Name",
      "DishSumInt": 750,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 750,
      "DishName": "Dish_Name",
      "DishSumInt": 750,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 750,
      "DishName": "Dish_Name",
      "DishSumInt": 750,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 750,
      "DishName": "Dish_Name",
      "DishSumInt": 750,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 990,
      "DishName": "Dish_Name",
      "DishSumInt": 990,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 990,
      "DishName": "Dish_Name",
      "DishSumInt": 990,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1200,
      "DishName": "Dish_Name",
      "DishSumInt": 1200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1800,
      "DishName": "Dish_Name",
      "DishSumInt": 1800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscoun 2000 tSumInt": 890,
      "DishName": "Dish_Name",
      "DishSumInt": 890,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 500,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 650,
      "DishName": "Dish_Name",
      "DishSumInt": 650,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1080,
      "DishName": "Dish_Name",
      "DishSumInt": 1080,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 110,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 110,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 330,
      "DishName": "Dish_Name",
      "DishSumInt": 330,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 110,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 905.33,
      "DishName": "Dish_Name",
      "DishSumInt": 1100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 304.69,
      "DishName": "Dish_Name",
      "DishSumInt": 330,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 440,
      "DishName": "Dish_Name",
      "DishSumInt": 440,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 247.77,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 262.34,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 50,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 11.67,
      "DishName": "Dish_Name",
      "DishSumInt": 25,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 25,
      "DishName": "Dish_Name",
      "DishSumInt": 25,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 304.58,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 680,
      "DishName": "Dish_Name",
      "DishSumInt": 680,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 224.31,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 370,
      "DishName": "Dish_Name",
      "DishSumInt": 370,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1140,
      "DishName": "Dish_Name",
      "DishSumInt": 1140,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "Op 2000 enDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1120,
      "DishName": "Dish_Name",
      "DishSumInt": 1120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 135,
      "DishName": "Dish_Name",
      "DishSumInt": 135,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 694.1,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 34.73,
      "DishName": "Dish_Name",
      "DishSumInt": 55,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 55,
      "DishName": "Dish_Name",
      "DishSumInt": 55,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 110,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 37.81,
      "DishName": "Dish_Name",
      "DishSumInt": 55,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 230,
      "DishName": "Dish_Name",
      "DishSumInt": 230,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 474.33,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 375,
      "DishName": "Dish_Name",
      "DishSumInt": 400,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 785.61,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 263.29,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 868.75,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 109.14,
      "DishName": "Dish_Name",
      "DishSumInt": 115,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 960,
      "DishName": "Dish_Name",
      "DishSumInt": 960,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 676.73,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 390,
      "DishName": "Dish_Name",
      "DishSumInt": 3902000,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 390,
      "DishName": "Dish_Name",
      "DishSumInt": 390,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 571.78,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 474.73,
      "DishName": "Dish_Name",
      "DishSumInt": 780,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 650,
      "DishName": "Dish_Name",
      "DishSumInt": 650,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 670,
      "DishName": "Dish_Name",
      "DishSumInt": 670,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 464.03,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 720,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 51.85,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 113.47,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 480,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 263.67,
      "DishName": "Dish_Name",
      "DishSumInt": 330,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 260,
      "DishName": "Dish_Name",
      "DishSumInt": 260,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 130,
      "DishName": "Dish_Name",
      "DishSumInt": 130,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 630,
      "DishName": "Dish_Name",
      "DishSumInt": 630,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 90,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 233.88,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 376.17,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 155.74,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 265.41,
      "DishName": "Dish_Name",
      "DishSumInt": 270,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2000,
      "DishName": "Dish_Name",
      "DishSumInt": 2000,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 320,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 160,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 630,
      "DishName": "Dish_Name",
      "DishSumInt": 630,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1439.79,
      "DishName": "Dish_Name",
      "DishSumInt": 1470,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "D 2000 ishSumInt": 560,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 816.49,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 375,
      "DishName": "Dish_Name",
      "DishSumInt": 375,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 75,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 51.56,
      "DishName": "Dish_Name",
      "DishSumInt": 75,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 358.75,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 750,
      "DishName": "Dish_Name",
      "DishSumInt": 750,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 250,
      "DishName": "Dish_Name",
      "DishSumInt": 250,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 150,
      "DishName": "Dish_Name",
      "DishSumInt": 150,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 600,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 290,
      "DishName": "Dish_Name",
      "DishSumInt": 290,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 812.29,
      "DishName": "Dish_Name",
      "DishSumInt": 870,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 290,
      "DishName": "Dish_Name",
      "DishSumInt": 290,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 100,
      "DishName": "Dish_Name",
      "DishSumInt": 100,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 380,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1288.95,
      "DishName": "Dish_Name",
      "DishSumInt": 1520,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 487.83,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 522.5,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 570,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 500,
      "DishName": "Dish_Name",
      "DishSumInt": 500,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 4250,
      "DishName": "Dish_Name",
      "DishSumInt": 4420,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1615,
      "DishName": "Dish_Name",
      "DishSumInt": 2040,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1700,
      "DishName": "Dish_Name",
      "DishSumInt": 1700,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1870,
      "DishName": "Dish_Name",
      "DishSumInt": 2040,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 7674.17,
      "DishName": "Dish_Name",
      "DishSumInt": 7820,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 595,
      "DishName": "Dish_Name",
      "DishSumInt": 680,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1360,
      "DishName": "Dish_Name",
      "DishSumInt": 1360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1020,
      "DishName": "Dish_Name",
      "DishSumInt": 1020,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 3552.28,
      "DishName": "Dish_Name",
      "DishSumInt": 3740,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 110,
      "DishName": "Dish_Name",
      "DishSumInt": 110,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 300,
      "DishName": "Dish_Name",
      "DishSumInt": 300,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 720,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 184.29,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 290,
      "DishName": "Dish_Name",
      "DishSumInt": 290,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 290,
      "DishName": "Dish_Name",
      "DishSumInt": 290,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1118.27,
      "DishName": "Dish_Name",
      "DishSumInt": 1160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 450,
      "DishName": "Dish_Name",
      "DishSumInt": 450,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 30,
      "DishName": "Dish_Name",
      "DishSumInt": 30,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 15,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 15,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 22.5,
      "DishName": "Dish_Name",
      "DishSumInt": 30,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 30,
      "DishName": "Dish_Name",
      "DishSumInt": 30,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 15,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 6.74,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 82.5,
      "DishName": "Dish_Name",
      "DishSumInt": 90,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 30,
      "DishName": "Dish_Name",
      "DishSumInt": 30,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 45,
      "DishName": "Dish_Name",
      "DishSumInt": 45,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 30,
      "DishName": "Dish_Name",
      "DishSumInt": 30,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 10,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 15,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 15,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 11.52,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 37.5,
      "DishName": "Dish_Name",
      "DishSumInt": 45,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 10.95,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 15,
      "DishName": "Dish_Name",
      "DishSumInt": 15,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 175.3,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 45,
      "DishName": "Dish_Name",
      "DishSumInt": 45,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60,
      "DishName": "Dish_Name",
      "DishSumInt": 60,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 140,
      "OpenDate": "2014.01.02"
    },
    {
      "Cash 2000 RegisterName": "Касса Подольск",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 880,
      "DishName": "Dish_Name",
      "DishSumInt": 880,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 435,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 580,
      "DishName": "Dish_Name",
      "DishSumInt": 580,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1160,
      "DishName": "Dish_Name",
      "DishSumInt": 1160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 720,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 6480,
      "DishName": "Dish_Name",
      "DishSumInt": 6480,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 720,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 649.12,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 270,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 720,
      "DishName": "Dish_Name",
      "DishSumInt": 720,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 900,
      "DishName": "Dish_Name",
      "DishSumInt": 900,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 840,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 560,
      "DishName": "Dish_Name",
      "DishSumInt": 560,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 316.67,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540.96,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 297.84,
      "DishName": "Dish_Name",
      "DishSumInt": 380,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 190,
      "DishName": "Dish_Name",
      "DishSumInt": 190,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 468.56,
      "DishName": "Dish_Name",
      "DishSumInt": 570,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 440,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 640,
      "DishName": "Dish_Name",
      "DishSumInt": 640,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 140,
      "DishName": "Dish_Name",
      "DishSumInt": 160,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 495,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 154.1,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 248.93,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 540,
      "DishName": "Dish_Name",
      "DishSumInt": 540,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 210,
      "DishName": "Dish_Name",
      "DishSumInt": 210,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 581.67,
      "DishName": "Dish_Name",
      "DishSumInt": 630,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 361.8,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 460,
      "DishName": "Dish_Name",
      "DishSumInt": 460,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 920,
      "DishName": "Dish_Name",
      "DishSumInt": 9200020,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 220,
      "DishName": "Dish_Name",
      "DishSumInt": 220,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 840,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 288.75,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 660,
      "DishName": "Dish_Name",
      "DishSumInt": 660,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 342.15,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 340,
      "DishName": "Dish_Name",
      "DishSumInt": 340,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 170,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 170,
      "DishName": "Dish_Name",
      "DishSumInt": 510,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 80,
      "DishName": "Dish_Name",
      "DishSumInt": 80,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishName": "Dish_Name",
      "DishSumInt": 0,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 50,
      "DishName": "Dish_Name",
      "DishSumInt": 50,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 188.11,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 68.11,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 55.93,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 480,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 188.11,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 320,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 55.93,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 200,
      "DishName": "Dish_Name",
      "DishSumInt": 200,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 600,
      "DishName": "Dish_Name",
      "DishSumInt": 800,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 180,
      "DishName": "Dish_Name",
      "DishSumInt": 180,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 360,
      "DishName": "Dish_Name",
      "DishSumInt": 360,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60,
      "DishName": "Dish_Name",
      "DishSumInt": 60,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 120,
      "DishName": "Dish_Name",
      "DishSumInt": 120,
      "OpenDate": "2014.01.01"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 240,
      "DishName": "Dish_Name",
      "DishSumInt": 240,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 420,
      "DishName": "Dish_Name",
      "DishSumInt": 420,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 280,
      "DishName": "Dish_Name",
      "DishSumInt": 280,
      "OpenDate": "2014.01.02"
    }
  ],
  "summary": [
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1514.39,
        "DishSumInt": 1610
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1766.13,
        "DishSumInt": 1820
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 3296.76,
        "DishSumInt": 3420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2280,
        "DishSumInt": 2850
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 403.56,
        "DishSumInt": 630
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 233.88,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1720,
        "DishSumInt": 1720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 11.52,
        "DishSumInt": 15
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1500,
        "DishSumInt": 1500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 858.43,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2695.74,
        "DishSumInt": 3200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 682.5,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300.87,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 273.04,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1407.54,
        "DishSumInt": 1440
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 119.96,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 656.71,
        "DishSumInt": 675
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90.16,
        "DishSumInt": 110
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 192.5,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 158.13,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 85.85,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3182.6,
        "DishSumInt": 3250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1079.62,
        "DishSumInt": 1100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1530,
        "DishSumInt": 1530
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1020,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 519.12,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 520,
        "DishSumInt": 520
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 980,
        "DishSumInt": 980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 467.5,
        "DishSumInt": 510
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 991.79,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 108.5,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 684.15,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 109.14,
        "DishSumInt": 115
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3510,
        "DishSumInt": 3510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 5200,
        "DishSumInt": 5200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1350,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1015,
        "DishSumInt": 1160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1740,
        "DishSumInt": 1740
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1000,
        "DishSumInt": 1000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 135,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2600,
        "DishSumInt": 2600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 7200,
        "DishSumInt": 7200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1113.1,
        "DishSumInt": 1300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 885.85,
        "DishSumInt": 1120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 474.33,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 785.61,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2000,
        "DishSumInt": 2000
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1808.64,
        "DishSumInt": 1980
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 501.56,
        "DishSumInt": 525
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 610,
        "DishSumInt": 610
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1300,
        "DishSumInt": 1300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2893.26,
        "DishSumInt": 2960
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1385.85,
        "DishSumInt": 2220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 750,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 229.18,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 969.73,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1070.63,
        "DishSumInt": 1140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 455,
        "DishSumInt": 455
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 21.74,
        "DishSumInt": 30
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1575,
        "DishSumInt": 1620
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1698.27,
        "DishSumInt": 1740
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1740,
        "DishSumInt": 1740
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1483.03,
        "DishSumInt": 1620
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2800,
        "DishSumInt": 2800
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSu 2000 mInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 18.75,
        "DishSumInt": 25
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 263.67,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 680,
        "DishSumInt": 680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5339.39,
        "DishSumInt": 5920
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 870,
        "DishSumInt": 870
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1419.39,
        "DishSumInt": 1620
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 810,
        "DishSumInt": 810
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1736.8,
        "DishSumInt": 1820
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 157.5,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1666.8,
        "DishSumInt": 1820
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1600,
        "DishSumInt": 1600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540.96,
        "DishSumInt": 570
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 10,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 670,
        "DishSumInt": 670
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 655.3,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 358.75,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 812.29,
        "DishSumInt": 870
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 750,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 6442.78,
        "DishSumInt": 6630
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 403.56,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "O 2000 penDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1439.79,
        "DishSumInt": 1470
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 810,
        "DishSumInt": 810
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 968.24,
        "DishSumInt": 980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 520,
        "DishSumInt": 520
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3351.76,
        "DishSumInt": 3660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 83.9,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 310.16,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 34.73,
        "DishSumInt": 55
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1000,
        "DishSumInt": 1000
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1200,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 858.75,
        "DishSumInt": 1000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 455,
        "DishSumInt": 520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3600,
        "DishSumInt": 3600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 696.67,
        "DishSumInt": 760
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 748.66,
        "DishSumInt": 800
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5590,
        "DishSumInt": 5590
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1497.36,
        "DishSumInt": 1710
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1696.63,
        "DishSumInt": 1750
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 225
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 890,
        "DishSumInt": 890
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1828.62,
        "DishSumInt": 2040
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3870,
        "DishSumInt": 3870
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2217.65,
        "DishSumInt": 2300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1199.33,
        "DishSumInt": 1300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2148,
        "DishSumInt": 2600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2734.64,
        "DishSumInt": 2860
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3360,
        "DishSumInt": 3360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 135.33,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 9871.98,
        "DishSumInt": 9900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2090.03,
        "DishSumInt": 2200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 520,
        "DishSumInt": 520
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2225.36,
        "DishSumInt": 2500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 63.45,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2415,
        "DishSumInt": 2520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 18.75,
        "DishSumInt": 25
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3416.98,
        "DishSumInt": 3600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 480,
        "D 2000 ishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 550,
        "DishSumInt": 550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3439.28,
        "DishSumInt": 3800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 9336.32,
        "DishSumInt": 10360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 127.5,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 433.54,
        "DishSumInt": 460
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1907.21,
        "DishSumInt": 1980
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5358.43,
        "DishSumInt": 5400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1360,
        "DishSumInt": 1360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 290,
        "DishSumInt": 290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 700,
        "DishSumInt": 700
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 26.83,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 721.25,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 30,
        "DishSumInt": 30
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1740,
        "DishSumInt": 1740
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1160,
        "DishSumInt": 1160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 34.73,
        "DishSumInt": 55
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 202.81,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 514.1,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 210
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 79.46,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 219.46,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1400,
        "DishSumInt": 1400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1296.77,
        "DishSumInt": 1400
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 387.77,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegiste 2000 rName": "Касса Подольск",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 315,
        "DishSumInt": 350
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 700,
        "DishSumInt": 700
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 884.39,
        "DishSumInt": 980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 109.14,
        "DishSumInt": 115
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 622.92,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 747.5,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1064.89,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1272.15,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 390,
        "DishSumInt": 390
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 370
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1015.01,
        "DishSumInt": 1110
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1380,
        "DishSumInt": 1380
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 730.05,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1260,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 370
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 464.03,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 601.15,
        "DishSumInt": 630
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3329.79,
        "DishSumInt": 3360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3403.6,
        "DishSumInt": 3640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1200,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt 2000 ": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 176.3,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 51.56,
        "DishSumInt": 75
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 109.18,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230.63,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 408.24,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 82.5,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1540,
        "DishSumInt": 1540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 595.74,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1350,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 965.32,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 315,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1400,
        "DishSumInt": 1400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1520,
        "DishSumInt": 1520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 188.11,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 890,
        "DishSumInt": 890
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3892.78,
        "DishSumInt": 4080
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2550,
        "DishSumInt": 2550
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 11.52,
        "DishSumInt": 15
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 316.67,
        "DishSumInt": 380
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 3300,
        "DishSumInt": 3300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1980,
        "DishSumInt": 1980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 119.96,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 350,
        "DishSumInt": 350
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2580,
        "DishSumInt": 2580
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2340,
        "DishSumInt": 2340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 327.54,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1099.12,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 512.15,
        "DishSumInt": 680
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 680,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 495,
        "DishSumInt": 550
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 4882.64,
        "DishSumInt": 5460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 3200,
        "DishSumInt": 3200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 980,
        "DishSumInt": 1600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2194.03,
        "DishSumInt": 2470
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 548.66,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 263.67,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 224.31,
        "DishSumInt": 370
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 370
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1900,
        "DishSumInt": 1900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 978.62,
        "DishSumInt": 1190
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 850,
        "DishSumInt": 850
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2664.12,
        "DishSumInt": 2800
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 995.62,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 1140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1350,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3440,
        "DishSumInt": 3440
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2150,
        "DishSumInt": 2150
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 79.46,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 715,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 290,
        "DishSumInt": 290
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1710,
        "DishSumInt": 1710
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3495.74,
        "DishSumInt": 4000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 756,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 867.54,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 188.11,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 499.96,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 740,
        "DishSumInt": 740
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2284.26,
        "DishSumInt": 2440
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1067.5,
        "DishSumInt": 1220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 694.7,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 125,
        "DishSumInt": 125
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "Open 2000 Date": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 37.56,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 109.14,
        "DishSumInt": 115
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1459.29,
        "DishSumInt": 1530
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1800,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2600,
        "DishSumInt": 2600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 135.41,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2600,
        "DishSumInt": 2600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1520,
        "DishSumInt": 1520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 571.78,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 11445.87,
        "DishSumInt": 11880
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 18.75,
        "DishSumInt": 25
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1280,
        "DishSumInt": 1280
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1305.88,
        "DishSumInt": 1400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 940,
        "DishSumInt": 940
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 355.88,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 470,
        "DishSumInt": 470
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 455,
        "DishSumInt": 455
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 501.56,
        "DishSumInt": 525
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1800,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 920,
        "DishSumInt": 920
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 773.64,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1035,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1826.51,
        "DishSumInt": 2340
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 165.85,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1299.81,
        "DishSumInt": 1380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 154.67,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3058.03,
        "DishSumInt": 3240
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1972.29,
        "DishSumInt": 2030
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 157.5,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1157.56,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 459.76,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 649.12,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 65,
        "DishSumInt": 65
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1140,
        "DishSumInt": 1140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 21.74,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 184.29,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2310.02,
        "DishSumInt": 2530
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 210
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2015.25,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 980,
        "DishSumInt": 980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3343.5,
        "DishSumInt": 4050
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 690,
        "DishSumInt": 690
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 172.5,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 194.9,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 154.67,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 344.89,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 355.88,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 135,
        "DishSumInt": 135
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5760,
        "DishSumInt": 5760
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 740
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 55.93,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": 2000"2014.01.02"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 195,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 9100,
        "DishSumInt": 9100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 988.31,
        "DishSumInt": 1040
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 880,
        "DishSumInt": 880
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2721.98,
        "DishSumInt": 2750
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1145.9,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2019.12,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 273.94,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 436.48,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 940,
        "DishSumInt": 1410
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1000,
        "DishSumInt": 1000
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 663.54,
        "DishSumInt": 690
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 370
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 390,
        "DishSumInt": 390
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 800
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1192.15,
        "DishSumInt": 1700
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 198.01,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3439.12,
        "DishSumInt": 3600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 760
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5280,
        "DishSumInt": 5280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 9155.56,
        "DishSumInt": 9600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 740,
        "DishSumInt": 740
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 9682.44,
        "DishSumInt": 10400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2837.21,
        "DishSumInt": 2960
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 150
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 275,
        "DishSumInt": 330
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSum 2000 Int": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 880,
        "DishSumInt": 880
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 16900,
        "DishSumInt": 18200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 315,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 150
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3040,
        "DishSumInt": 3040
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1600,
        "DishSumInt": 1600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 740,
        "DishSumInt": 740
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 18.75,
        "DishSumInt": 25
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 680,
        "DishSumInt": 680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1360,
        "DishSumInt": 1360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 520,
        "DishSumInt": 520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 520,
        "DishSumInt": 520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 81.88,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 459.57,
        "DishSumInt": 495
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 154.1,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2125.85,
        "DishSumInt": 2960
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1040,
        "DishSumInt": 1040
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 7210.47,
        "DishSumInt": 7400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 550,
        "DishSumInt": 550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 375,
        "DishSumInt": 375
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 4200,
        "DishSumInt": 4200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 30,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 342.15,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 440,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 165
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 61.48,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1158.43,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 165
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 265.41,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 165
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 215.25,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 337.5,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 550,
        "DishSumInt": 550
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 405,
        "DishSumInt": 585
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 527.77,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 350,
        "DishSumInt": 350
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 474.73,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 390,
        "DishSumInt": 390
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 106.3,
        "DishSumInt": 210
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 748.11,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1135.93,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1884.04,
        "DishSumInt": 2040
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1620,
        "DishSumInt": 1620
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 350,
        "DishSumInt": 350
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 855,
        "DishSumInt": 1035
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 676.73,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 960,
        "DishSumInt": 960
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 290,
        "DishSumInt": 290
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1322.5,
        "DishSumInt": 1380
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2100,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 700,
        "DishSumInt": 700
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 141.79,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 905.29,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 514.1,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountS 2000 umInt": 980,
        "DishSumInt": 980
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 157.5,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 370
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 421.46,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1110,
        "DishSumInt": 1110
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 3235.01,
        "DishSumInt": 3700
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2104.38,
        "DishSumInt": 2220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1406.75,
        "DishSumInt": 1440
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1350,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 285.39,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 870,
        "DishSumInt": 870
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 304.69,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1102.29,
        "DishSumInt": 1160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 18.75,
        "DishSumInt": 25
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1520,
        "DishSumInt": 2280
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 25,
        "DishSumInt": 25
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 194.9,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3121.8,
        "DishSumInt": 3220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 154.67,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 470,
        "DishSumInt": 470
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1650.02,
        "DishSumInt": 1870
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2820,
        "DishSumInt": 3290
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1631.67,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 203.54,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 694.1,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 375,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 263.29,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1868.31,
        "DishSumInt": 1920
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 904.29,
        "DishSumInt": 960
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 408.24,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1033.56,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01. 2000 01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 390,
        "DishSumInt": 390
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 130
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 420.16,
        "DishSumInt": 440
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1320,
        "DishSumInt": 1320
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1720,
        "DishSumInt": 1720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1280,
        "DishSumInt": 1280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 105,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2880,
        "DishSumInt": 2880
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1520,
        "DishSumInt": 1520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 6.74,
        "DishSumInt": 15
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 175,
        "DishSumInt": 175
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1800,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 864.12,
        "DishSumInt": 1000
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 594.7,
        "DishSumInt": 650
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 68.11,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 83.9,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 315,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 46800,
        "DishSumInt": 48100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 182.6,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 887.9,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 705.88,
        "DishSumInt": 800
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSum 2000 Int": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 4760,
        "DishSumInt": 4760
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1674.26,
        "DishSumInt": 1830
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1320,
        "DishSumInt": 1320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3748.21,
        "DishSumInt": 3840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 37.5,
        "DishSumInt": 45
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 5130,
        "DishSumInt": 5400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 6315.87,
        "DishSumInt": 6480
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 304.58,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 680,
        "DishSumInt": 680
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1078.13,
        "DishSumInt": 1150
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 56.25,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 700,
        "DishSumInt": 700
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 177.56,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2100,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 690,
        "DishSumInt": 690
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 980,
        "DishSumInt": 980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 390,
        "DishSumInt": 390
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 440,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1436.51,
        "DishSumInt": 1950
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2040,
        "DishSumInt": 2040
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 5200,
        "DishSumInt": 5200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 3900,
        "DishSumInt": 3900
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 47.35,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1968.75,
        "DishSumInt": 2520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        2000"DishDiscountSumInt": 330,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 690,
        "DishSumInt": 690
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 402.5,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 920,
        "DishSumInt": 920
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3700.25,
        "DishSumInt": 3780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2160,
        "DishSumInt": 2430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 192.5,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 25,
        "DishSumInt": 25
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3316.73,
        "DishSumInt": 3360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 440,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 67.5,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 920,
        "DishSumInt": 920
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2201.8,
        "DishSumInt": 2300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 51.85,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 913.47,
        "DishSumInt": 1000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 275,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1520,
        "DishSumInt": 1520
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 760
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 106.3,
        "DishSumInt": 210
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1100,
        "DishSumInt": 1100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 440,
        "DishSumInt": 440
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1440,
        "DishSumInt": 1440
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1410,
        "DishSumInt": 1880
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 715,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1001.67,
        "DishSumInt": 1050
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1410,
        "DishSumInt": 1410
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 487.83,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 112.5,
        "DishSumInt": 150
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 675,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 10.95,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegi 2000 sterName": "Касса Домодедово",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 165
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 105,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1840,
        "DishSumInt": 1840
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1324.58,
        "DishSumInt": 1360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 410.29,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1680,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 673.97,
        "DishSumInt": 860
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 26.52,
        "DishSumInt": 30
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1360,
        "DishSumInt": 1360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 11.67,
        "DishSumInt": 25
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 7674.17,
        "DishSumInt": 7820
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 960,
        "DishSumInt": 960
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 4250,
        "DishSumInt": 4420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 960,
        "DishSumInt": 960
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 6324.69,
        "DishSumInt": 6600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 370,
        "DishSumInt": 370
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 45,
        "DishSumInt": 45
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 94.9,
        "DishSumInt": 100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 740,
        "DishSumInt": 740
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1364.38,
        "DishSumInt": 1480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 338.09,
        "DishSumInt": 380
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 832.78,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 105,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 105,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 222.92,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 18838,
        "DishSumInt": 20000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 264,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1234.1,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1054.1,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2869.28,
        "DishSumInt": 3230
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 247.77,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 541.45,
        "DishSumInt": 585
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 587.21,
        "DishSumInt": 660
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 112.5,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1578.8,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1445.89,
        "DishSumInt": 1500
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3500,
        "DishSumInt": 3990
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 30,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 275,
        "DishSumInt": 330
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1020,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1020,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 508.24,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1144.29,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1704.31,
        "DishSumInt": 1850
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1121.25,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1280,
        "DishSumInt": 1280
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2900,
        "DishSumInt": 2900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 30,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1200,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2920000,
        "DishSumInt": 290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 870,
        "DishSumInt": 870
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 350,
        "DishSumInt": 350
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 390,
        "DishSumInt": 390
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 102.92,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 227.5,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1100,
        "DishSumInt": 1100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 918.01,
        "DishSumInt": 1040
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1370.42,
        "DishSumInt": 1560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 581.67,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 315,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 262.34,
        "DishSumInt": 460
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 23976.45,
        "DishSumInt": 25160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 687.26,
        "DishSumInt": 910
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1120,
        "DishSumInt": 1120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 690,
        "DishSumInt": 690
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1415.25,
        "DishSumInt": 1500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1920,
        "DishSumInt": 1920
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 131.48,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3840,
        "DishSumInt": 3840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 263.67,
        "DishSumInt": 330
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 25,
        "DishSumInt": 25
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 73.28,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1636.73,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 350
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1680,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2250,
        "DishSumInt": 2250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1093.5,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 810,
        "DishSumInt": 810
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1318.82,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 440,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1350,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 4050,
        "DishSumInt": 4050
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 113.47,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 11.67,
        "DishSumInt": 25
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 960,
        "DishSumInt": 960
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 4251.76,
        "DishSumInt": 4550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3900,
        "DishSumInt": 3900
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 330
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2200,
        "DishSumInt": 2200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 550,
        "DishSumInt": 550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 155.74,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1533.97,
        "DishSumInt": 1720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 94.7,
        "DishSumInt": 150
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 459.64,
        "DishSumInt": 520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 189.9,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 61.48,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 673.94,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 375,
        "DishSumInt": 675
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3165.02,
        "DishSumInt": 3300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 380,
        "DishSumInt": 380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 47.35,
        "DishSumInt": 75
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 110,
        "DishSumInt": 110
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 905.33,
        "DishSumInt": 1100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1320,
        "DishSumInt": 1320
      }
    ],
    [
      {
        "DishNa 2000 me": "Сэндвич ролл с угрём"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 960,
        "DishSumInt": 960
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2400,
        "DishSumInt": 2400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1200,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1696.63,
        "DishSumInt": 1750
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 148.09,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 890,
        "DishSumInt": 890
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 868.75,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 502.5,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 908.09,
        "DishSumInt": 950
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 105,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3280.52,
        "DishSumInt": 3430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5576.76,
        "DishSumInt": 6270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 290,
        "DishSumInt": 290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 450,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 18200,
        "DishSumInt": 18200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 125,
        "DishSumInt": 125
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 125,
        "DishSumInt": 125
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 28600,
        "DishSumInt": 29900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 243.97,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2580,
        "DishSumInt": 2580
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2160,
        "DishSumInt": 2160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 707.9,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 361.8,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 150
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 682.6,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2500,
        "DishSumInt": 2500
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1582.5,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 520,
        "DishSumInt": 520
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1360,
        "DishSumInt": 1360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 850,
        "DishSumInt": 850
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 474.58,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 510
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3400,
        "DishSumInt": 3400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 816.49,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2366.75,
        "DishSumInt": 2400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 4860,
        "DishSumInt": 4860
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1381.46,
        "DishSumInt": 1440
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 321.25,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2755,
        "DishSumInt": 2900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 402.16,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 722.65,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 880,
        "DishSumInt": 880
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 436.8,
        "DishSumInt": 520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 3552.28,
        "DishSumInt": 3740
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1870,
        "DishSumInt": 2040
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 848.13,
        "DishSumInt": 920
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 356.25,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 7920,
        "DishSumInt": 7920
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 595,
        "DishSumInt": 680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1615,
        "DishSumInt": 2040
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }2000
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 156.25,
        "DishSumInt": 175
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 47.35,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 165,
        "DishSumInt": 165
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3438.27,
        "DishSumInt": 3480
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1548.75,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1160,
        "DishSumInt": 1160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 4355.56,
        "DishSumInt": 4800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 6302.44,
        "DishSumInt": 6400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 810,
        "DishSumInt": 810
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 947.26,
        "DishSumInt": 1170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 315,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 155.74,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2069.79,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 445.41,
        "DishSumInt": 450
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1260,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 376.17,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 522.5,
        "DishSumInt": 570
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 630,
        "DishSumInt": 630
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1260,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 492.34,
        "DishSumInt": 690
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 690
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": " 2000 2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1300,
        "DishSumInt": 1300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 5368.82,
        "DishSumInt": 5400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1500,
        "DishSumInt": 1500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 245.9,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 130,
        "DishSumInt": 130
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 190,
        "DishSumInt": 190
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 714.03,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 8151.76,
        "DishSumInt": 8450
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1400,
        "DishSumInt": 1400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1140,
        "DishSumInt": 1140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 468.56,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1110,
        "DishSumInt": 1110
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 594.31,
        "DishSumInt": 740
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 990,
        "DishSumInt": 990
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 670,
        "DishSumInt": 670
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1220,
        "DishSumInt": 1710
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2280,
        "DishSumInt": 2280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1413.63,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 70,
        "DishSumInt": 70
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2000430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 170,
        "DishSumInt": 170
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 3000,
        "DishSumInt": 3000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 176.77,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 150
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 414.57,
        "DishSumInt": 450
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 36.88,
        "DishSumInt": 45
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 750,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1980,
        "DishSumInt": 1980
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 840,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2307.16,
        "DishSumInt": 2460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 75,
        "DishSumInt": 75
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 750,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1280,
        "DishSumInt": 1280
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 750,
        "DishSumInt": 750
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 150
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 990,
        "DishSumInt": 990
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 175.3,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 990,
        "DishSumInt": 990
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 6571.98,
        "DishSumInt": 6600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 80,
        "DishSumInt": 80
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 3300,
        "DishSumInt": 3300
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1635,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 780,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 672.16,
        "DishSumInt": 780
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 440
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1196.63,
        "DishSumInt": 1250
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1350,
        "DishSumInt": 1350
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1100,
        "DishSumInt": 1100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1100,
        "DishSumInt": 1100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 290,
        "DishSumInt": 290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 56.25,
        "DishSumInt": 75
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1118.27,
        "DishSumInt": 1160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 60,
        "DishSumInt": 60
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 250,
        "DishSumInt": 250
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 187.5,
        "DishSumInt": 195
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 700,
        "DishSumInt": 700
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 800,
        "DishSumInt": 800
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1200,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 760,
        "DishSumInt": 760
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 125,
        "DishSumInt": 125
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 275,
        "DishSumInt": 350
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 642.16,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 475
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 138.44,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 138.44,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 237.54,
        "DishSumInt": 275
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 73.28,
        "DishSumInt": 80
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 990,
        "DishSumInt": 990
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2415,
        "DishSumInt": 2520
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 15,
        "DishSumInt": 15
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 48.45,
        "DishSumInt": 60
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 10,
        "DishSumInt": 15
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1530,
        "DishSumInt": 1530
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 990,
        "DishSumInt": 990
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 917.21,
        "DishSumInt": 990
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 260,
        "DishSumInt": 260
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 640,
        "DishSumInt": 640
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 150,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 55.93,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 570,
        "DishSumInt": 570
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1586.76,
        "DishSumInt": 1710
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 37.81,
        "DishSumInt": 55
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1135.3,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 340,
        "DishSumInt": 340
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 330,
        "DishSumInt": 330
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 380.25,
        "DishSumInt": 510
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 211.72,
        "DishSumInt": 240
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 198.01,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 125,
        "DishSumInt": 125
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1376.49,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2696.77,
        "DishSumInt": 2800
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 495,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 560
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 248.93,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1096.49,
        "DishSumInt": 1120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 148.66,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 720,
        "DishSumInt": 720
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 51.85,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 30,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 288.75,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 920,
        "DishSumInt": 920
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 460,
        "DishSumInt": 460
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 113.94,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 90,
        "DishSumInt": 90
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1200,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1800,
        "DishSumInt": 1800
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 55,
        "DishSumInt": 55
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 22.5,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 350,
        "DishSumInt": 375
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 844.04,
        "DishSumInt": 1200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 300,
        "DishSumInt": 300
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 428.11,
        "DishSumInt": 480
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 704.89,
        "DishSumInt": 720
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 730.05,
        "DishSumInt": 840
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1219.21,
        "DishSumInt": 1275
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 860,
        "DishSumInt": 860
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1129.29,
        "DishSumInt": 1275
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 510,
        "DishSumInt": 510
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 430,
        "DishSumInt": 430
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1050,
        "DishSumInt": 1050
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 360,
        "DishSumInt": 360
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 2348.5,
        "DishSumInt": 2550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1260,
        "DishSumInt": 1260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 14201.45,
        "DishSumInt": 14620
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 9775,
        "DishSumInt": 10540
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 435,
        "DishSumInt": 580
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 192.5,
        "DishSumInt": 220
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 18.75,
        "DishSumInt": 25
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 660,
        "DishSumInt": 660
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 280,
        "DishSumInt": 280
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1080,
        "DishSumInt": 1080
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 952.34,
        "DishSumInt": 1380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 6480,
        "DishSumInt": 6480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 297.84,
        "DishSumInt": 380
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 220,
        "DishSumInt": 220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 540,
        "DishSumInt": 540
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 25,
        "DishSumInt": 30
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 610,
        "DishSumInt": 610
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1700,
        "DishSumInt": 1700
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1020,
        "DishSumInt": 1020
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 457.5,
        "DishSumInt": 610
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 30,
        "DishSumInt": 30
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 100,
        "DishSumInt": 100
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 37.5,
        "DishSumInt": 45
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 714.03,
        "DishSumInt": 750
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 500,
        "DishSumInt": 500
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 11.67,
        "DishSumInt": 25
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 127.5,
        "DishSumInt": 170
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 105,
        "DishSumInt": 140
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1290,
        "DishSumInt": 1290
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2600,
        "DishSumInt": 2600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 2700,
        "DishSumInt": 2700
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 550,
        "DishSumInt": 550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 550,
        "DishSumInt": 550
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 420,
        "DishSumInt": 420
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 210,
        "DishSumInt": 210
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1680,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 180,
        "DishSumInt": 180
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 331.13,
        "DishSumInt": 350
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 140,
        "DishSumInt": 140
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 900,
        "DishSumInt": 900
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 670,
        "DishSumInt": 670
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 160,
        "DishSumInt": 160
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 418.82,
        "DishSumInt": 450
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 230,
        "DishSumInt": 230
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1858.75,
        "DishSumInt": 2000
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 0
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 227.5,
        "DishSumInt": 260
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.0 e30 1.01"
      },
      {
        "DishDiscountSumInt": 585,
        "DishSumInt": 780
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 560,
        "DishSumInt": 560
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 120,
        "DishSumInt": 120
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 240,
        "DishSumInt": 240
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 351.76,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 580,
        "DishSumInt": 580
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1593.63,
        "DishSumInt": 1980
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 650,
        "DishSumInt": 650
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 480,
        "DishSumInt": 480
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 50,
        "DishSumInt": 50
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 4445.89,
        "DishSumInt": 4500
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1878.8,
        "DishSumInt": 2100
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 40,
        "DishSumInt": 40
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20,
        "DishSumInt": 20
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 320,
        "DishSumInt": 320
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 270,
        "DishSumInt": 270
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 200,
        "DishSumInt": 200
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 700,
        "DishSumInt": 700
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 750,
        "DishSumInt": 750
      }
    ],
    [
      {
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 2250,
        "DishSumInt": 2250
      }
    ],
    [
      {
        "DishName": "Dish_Name"
      },
      {
        "DishDiscountSumInt": 1680,
        "DishSumInt": 1680
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 600,
        "DishSumInt": 600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 400,
        "DishSumInt": 400
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "DishName": "Dish_Name",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 1288.95,
        "DishSumInt": 1520
      }
    ]
  ]
}
```

 [+] [Почасовая выручка](javascript:void%280%29)
 [-] [Почасовая выручка](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/reports/olap?key=99939171-551a-f54b-5163-366e773c40ac |
| --- | --- |

#### Тело запроса


Код

```

{
  "reportType": "SALES",
  "groupByRowFields": [
    "OpenDate",
    "HourClose"
  ],
  "aggregateFields": [
    "GuestNum",
    "DishSumInt",
    "DishDiscountSumInt",
    "UniqOrderId"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}

```


#### Ответ


Код

```

{
  "data": [
    {
      "DishDiscountSumInt": 1892.5,
      "DishSumInt": 1950,
      "GuestNum": 5,
      "HourClose": "16",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 5
    },
    {
      "DishDiscountSumInt": 31815.75,
      "DishSumInt": 34700,
      "GuestNum": 34,
      "HourClose": "17",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 34
    },
    {
      "DishDiscountSumInt": 34505,
      "DishSumInt": 37245,
      "GuestNum": 30,
      "HourClose": "18",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 31
    },
    {
      "DishDiscountSumInt": 24276.5,
      "DishSumInt": 25315,
      "GuestNum": 22,
      "HourClose": "19",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 27
    },
    {
      "DishDiscountSumInt": 41170,
      "DishSumInt": 44870,
      "GuestNum": 39,
      "HourClose": "20",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 41
    },
    {
      "DishDiscountSumInt": 31906.25,
      "DishSumInt": 32480,
      "GuestNum": 30,
      "HourClose": "21",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 31
    },
    {
      "DishDiscountSumInt": 20135.5,
      "DishSumInt": 21415,
      "GuestNum": 25,
      "HourClose": "22",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 26
    },
    {
      "DishDiscountSumInt": 820,
      "DishSumInt": 820,
      "GuestNum": 1,
      "HourClose": "23",
      "OpenDate": "2014.01.01",
      "UniqOrderId": 1
    },
    {
      "DishDiscountSumInt": 175,
      "DishSumInt": 375,
      "GuestNum": 1,
      "HourClose": "10",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 1
    },
    {
      "DishDiscountSumInt": 12167.5,
      "DishSumInt": 12400,
      "GuestNum": 9,
      "HourClose": "11",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 9
    },
    {
      "DishDiscountSumInt": 9342.5,
      "DishSumInt": 9520,
      "GuestNum": 11,
      "HourClose": "12",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 12
    },
    {
      "DishDiscountSumInt": 17672.5,
      "DishSumInt": 20035,
      "GuestNum": 20,
      "HourClose": "13",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 21
    },
    {
      "DishDiscountSumInt": 26517.5,
      "DishSumInt": 27000,
      "GuestNum": 27,
      "HourClose": "14",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 29
    },
    {
      "DishDiscountSumInt": 21980,
      "DishSumInt": 22500,
      "GuestNum": 21,
      "HourClose": "15",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 22
    },
    {
      "DishDiscountSumInt": 19632.5,
      "DishSumInt": 21500,
      "GuestNum": 20,
      "HourClose": "16",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 22
    },
    {
      "DishDiscountSumInt": 29853,
      "DishSumInt": 31140,
      "GuestNum": 27,
      "HourClose": "17",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 28
    },
    {
      "DishDiscountSumInt": 27009,
      "DishSumInt": 28060,
      "GuestNum": 27,
      "HourClose": "18",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 27
    },
    {
      "DishDiscountSumInt": 16019,
      "DishSumInt": 18485,
      "GuestNum": 19,
      "HourClose": "19",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 21
    },
    {
      "DishDiscountSumInt": 20790,
      "DishSumInt": 20790,
      "GuestNum": 19,
      "HourClose": "20",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 21
    },
    {
      "DishDiscountSumInt": 53772,
      "DishSumInt": 55075,
      "GuestNum": 42,
      "HourClose": "21",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 44
    },
    {
      "DishDiscountSumInt": 24387.5,
      "DishSumInt": 25360,
      "GuestNum": 28,
      "HourClose": "22",
      "OpenDate": "2014.01.02",
      "UniqOrderId": 29
    }
  ],
  "summary": [
    [
      {
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 279318,
        "DishSumInt": 292240,
        "GuestNum": 271,
        "UniqOrderId": 286
      }
    ],
    [
      {
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035,
        "GuestNum": 457,
        "UniqOrderId": 482
      }
    ],
    [
      {
        "HourClose": "20",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 41170,
        "DishSumInt": 44870,
        "GuestNum": 39,
        "UniqOrderId": 41
      }
    ],
    [
      {
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 186521.5,
        "DishSumInt": 198795,
        "GuestNum": 186,
        "UniqOrderId": 196
      }
    ],
    [
      {
        "HourClose": "21",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 31906.25,
        "DishSumInt": 32480,
        "GuestNum": 30,
        "UniqOrderId": 31
      }
    ],
    [
      {
        "HourClose": "20",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 20790,
        "DishSumInt": 20790,
        "GuestNum": 19,
        "UniqOrderId": 21
      }
    ],
    [
      {
        "HourClose": "10",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 175,
        "DishSumInt": 375,
        "GuestNum": 1,
        "UniqOrderId": 1
      }
    ],
    [
      {
        "HourClose": "21",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 53772,
        "DishSumInt": 55075,
        "GuestNum": 42,
        "UniqOrderId": 44
      }
    ],
    [
      {
        "HourClose": "16",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 1892.5,
        "DishSumInt": 1950,
        "GuestNum": 5,
        "UniqOrderId": 5
      }
    ],
    [
      {
        "HourClose": "15",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 21980,
        "DishSumInt": 22500,
        "GuestNum": 21,
        "UniqOrderId": 22
      }
    ],
    [
      {
        "HourClose": "17",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 31815.75,
        "DishSumInt": 34700,
        "GuestNum": 34,
        "UniqOrderId": 34
      }
    ],
    [
      {
        "HourClose": "16",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 19632.5,
        "DishSumInt": 21500,
        "GuestNum": 20,
        "UniqOrderId": 22
      }
    ],
    [
      {
        "HourClose": "18",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 34505,
        "DishSumInt": 37245,
        "GuestNum": 30,
        "UniqOrderId": 31
      }
    ],
    [
      {
        "HourClose": "17",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 29853,
        "DishSumInt": 31140,
        "GuestNum": 27,
        "UniqOrderId": 28
      }
    ],
    [
      {
        "HourClose": "22",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 20135.5,
        "DishSumInt": 21415,
        "GuestNum": 25,
        "UniqOrderId": 26
      }
    ],
    [
      {
        "HourClose": "18",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 27009,
        "DishSumInt": 28060,
        "GuestNum": 27,
        "UniqOrderId": 27
      }
    ],
    [
      {
        "HourClose": "23",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 820,
        "DishSumInt": 820,
        "GuestNum": 1,
        "UniqOrderId": 1
      }
    ],
    [
      {
        "HourClose": "11",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 12167.5,
        "DishSumInt": 12400,
        "GuestNum": 9,
        "UniqOrderId": 9
      }
    ],
    [
      {
        "HourClose": "22",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 24387.5,
        "DishSumInt": 25360,
        "GuestNum": 28,
        "UniqOrderId": 29
      }
    ],
    [
      {
        "HourClose": "12",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 9342.5,
        "DishSumInt": 9520,
        "GuestNum": 11,
        "UniqOrderId": 12
      }
    ],
    [
      {
        "HourClose": "13",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 17672.5,
        "DishSumInt": 20035,
        "GuestNum": 20,
        "UniqOrderId": 21
      }
    ],
    [
      {
        "HourClose": "14",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 26517.5,
        "DishSumInt": 27000,
        "GuestNum": 27,
        "UniqOrderId": 29
      }
    ],
    [
      {
        "HourClose": "19",
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 24276.5,
        "DishSumInt": 25315,
        "GuestNum": 22,
        "UniqOrderId": 27
      }
    ],
    [
      {
        "HourClose": "19",
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 16019,
        "DishSumInt": 18485,
        "GuestNum": 19,
        "UniqOrderId": 21
      }
    ]
  ]
}
```

 [+] [Выручка по категориям блюд](javascript:void%280%29)
 [-] [Выручка по категориям блюд](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/reports/olap?key=99939171-551a-f54b-5163-366e773c40ac |
| --- | --- |
#### Тело запроса


Код

```


{
  "reportType": "SALES",
  "groupByRowFields": [
    "DishCategory"
  ],
  "aggregateFields": [
    "GuestNum",
    "DishSumInt",
    "DishDiscountSumInt",
    "UniqOrderId"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}

```


#### Ответ 


Код

```


{
  "data": [
    {
      "DishCategory": null,
      "DishDiscountSumInt": 8967.73,
      "DishSumInt": 9900,
      "GuestNum": 88,
      "UniqOrderId": 93
    },
    {
      "DishCategory": "Без скидки",
      "DishDiscountSumInt": 80296.57,
      "DishSumInt": 84800,
      "GuestNum": 86,
      "UniqOrderId": 87
    },
    {
      "DishCategory": "Со скидкой",
      "DishDiscountSumInt": 376575.2,
      "DishSumInt": 396335,
      "GuestNum": 425,
      "UniqOrderId": 449
    }
  ],
  "summary": [
    [
      {
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035,
        "GuestNum": 457,
        "UniqOrderId": 482
      }
    ],
    [
      {
        "DishCategory": "Без скидки"
      },
      {
        "DishDiscountSumInt": 80296.57,
        "DishSumInt": 84800,
        "GuestNum": 86,
        "UniqOrderId": 87
      }
    ],
    [
      {
        "DishCategory": "Со скидкой"
      },
      {
        "DishDiscountSumInt": 376575.2,
        "DishSumInt": 396335,
        "GuestNum": 425,
        "UniqOrderId": 449
      }
    ],
    [
      {
        "DishCategory": null
      },
      {
        "DishDiscountSumInt": 8967.73,
        "DishSumInt": 9900,
        "GuestNum": 88,
        "UniqOrderId": 93
      }
    ]
  ]
}
```

 
[+] Выручка станций по дням
 [-] [Выручка станций по дням](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/reports/olap?key=b785c815-f06d-947c-3fb5-3052a2df7fd8 |
| --- | --- |

#### Тело запроса


Код

```


{
  "reportType": "SALES",
  "groupByRowFields": [
    "PayTypes",
    "OpenDate"
  ],
  "groupByColFields": [
    "CashRegisterName"
  ],
  "aggregateFields": [
    "DishSumInt",
    "DishDiscountSumInt"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}

```


#### Ответ


Код

```

{
  "data": [
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishSumInt": 890,
      "OpenDate": "2014.01.01",
      "PayTypes": "(без оплаты)"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishSumInt": 710,
      "OpenDate": "2014.01.01",
      "PayTypes": "(без оплаты)"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishSumInt": 70,
      "OpenDate": "2014.01.02",
      "PayTypes": "(без оплаты)"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 0,
      "DishSumInt": 1765,
      "OpenDate": "2014.01.02",
      "PayTypes": "(без оплаты)"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 66981.5,
      "DishSumInt": 73535,
      "OpenDate": "2014.01.01",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 23976.25,
      "DishSumInt": 24900,
      "OpenDate": "2014.01.01",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 6048.75,
      "DishSumInt": 6315,
      "OpenDate": "2014.01.01",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 48925,
      "DishSumInt": 50345,
      "OpenDate": "2014.01.01",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 33855,
      "DishSumInt": 35365,
      "OpenDate": "2014.01.01",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 115178,
      "DishSumInt": 119185,
      "OpenDate": "2014.01.02",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 16770,
      "DishSumInt": 18045,
      "OpenDate": "2014.01.02",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 20695,
      "DishSumInt": 22530,
      "OpenDate": "2014.01.02",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60780,
      "DishSumInt": 61645,
      "OpenDate": "2014.01.02",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 60845,
      "DishSumInt": 63950,
      "OpenDate": "2014.01.02",
      "PayTypes": "Наличные"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 5220,
      "DishSumInt": 5220,
      "OpenDate": "2014.01.01",
      "PayTypes": "безналичный расчет"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1515,
      "DishSumInt": 1515,
      "OpenDate": "2014.01.01",
      "PayTypes": "безналичный расчет"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1110,
      "DishSumInt": 1110,
      "OpenDate": "2014.01.02",
      "PayTypes": "безналичный расчет"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 1450,
      "DishSumInt": 1450,
      "OpenDate": "2014.01.02",
      "PayTypes": "безналичный расчет"
    },
    {
      "CashRegisterName": "Cash_Register_Name",
      "DishDiscountSumInt": 2490,
      "DishSumInt": 2490,
      "OpenDate": "2014.01.02",
      "PayTypes": "безналичный расчет"
    }
  ],
  "summary": [
    [
      {
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 3435
      }
    ],
    [
      {
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035
      }
    ],
    [
      {
        "OpenDate": "2014.01.02",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 1835
      }
    ],
    [
      {
        "OpenDate": "2014.01.01",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 1600
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 6330,
        "DishSumInt": 6330
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 2490,
        "DishSumInt": 2490
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 710
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 1450,
        "DishSumInt": 1450
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 2490,
        "DishSumInt": 2490
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 1515,
        "DishSumInt": 1515
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 115178,
        "DishSumInt": 119185
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name"
      },
      {
        "DishDiscountSumInt": 29708.75,
        "DishSumInt": 31810
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 66981.5,
        "DishSumInt": 73535
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 1765
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 1765
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name"
      },
      {
        "DishDiscountSumInt": 112195,
        "DishSumInt": 116245
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name"
      },
      {
        "DishDiscountSumInt": 94700,
        "DishSumInt": 99315
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 182159.5,
        "DishSumInt": 192720
      }
    ],
    [
      {
        "OpenDate": "2014.01.02",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 5050,
        "DishSumInt": 5050
      }
    ],
    [
      {
        "OpenDate": "2014.01.01",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 6735,
        "DishSumInt": 6735
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 20695,
        "DishSumInt": 22530
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 5220,
        "DishSumInt": 5220
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 6048.75,
        "DishSumInt": 6315
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 40746.25,
        "DishSumInt": 42945
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 1110,
        "DishSumInt": 1110
      }
    ],
    [
      {
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 454054.5,
        "DishSumInt": 475815
      }
    ],
    [
      {
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 179786.5,
        "DishSumInt": 190460
      }
    ],
    [
      {
        "OpenDate": "2014.01.02",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 274268,
        "DishSumInt": 285355
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 16770,
        "DishSumInt": 18045
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 23976.25,
        "DishSumInt": 24900
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 26743.75,
        "DishSumInt": 28845
      }
    ],
    [
      {
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 11785,
        "DishSumInt": 11785
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 890
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 70
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 33855,
        "DishSumInt": 35365
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 60780,
        "DishSumInt": 61645
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 960
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 48925,
        "DishSumInt": 50345
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.02",
        "PayType 351 s": "Наличные"
      },
      {
        "DishDiscountSumInt": 60845,
        "DishSumInt": 63950
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 94700,
        "DishSumInt": 99315
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name"
      },
      {
        "DishDiscountSumInt": 40746.25,
        "DishSumInt": 43655
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "Наличные"
      },
      {
        "DishDiscountSumInt": 109705,
        "DishSumInt": 111990
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "PayTypes": "безналичный расчет"
      },
      {
        "DishDiscountSumInt": 2965,
        "DishSumInt": 2965
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name"
      },
      {
        "DishDiscountSumInt": 188489.5,
        "DishSumInt": 200010
      }
    ],
    [
      {
        "CashRegisterName": "Cash_Register_Name",
        "OpenDate": "2014.01.01",
        "PayTypes": "(без оплаты)"
      },
      {
        "DishDiscountSumInt": 0,
        "DishSumInt": 710
      }
    ]
  ]
}
0

```

 [+] [Выручка по дням](javascript:void%280%29)
 [-] [Выручка по дням](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | https://localhost:8080/resto/api/v2/reports/olap?key=b785c815-f06d-947c-3fb5-3052a2df7fd8 |
| --- | --- |

#### Тело запроса


Код

```


{
  "reportType": "SALES",
  "groupByRowFields": [
    "OpenDate"
  ],
  "aggregateFields": [
    "GuestNum",
    "DishSumInt",
    "DishDiscountSumInt",
    "UniqOrderId"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}

```


#### **Ответ**


Код

```


{
  "data": [
    {
      "DishDiscountSumInt": 186521.5,
      "DishSumInt": 198795,
      "GuestNum": 186,
      "OpenDate": "2014.01.01",
      "UniqOrderId": 196
    },
    {
      "DishDiscountSumInt": 279318,
      "DishSumInt": 292240,
      "GuestNum": 271,
      "OpenDate": "2014.01.02",
      "UniqOrderId": 286
    }
  ],
  "summary": [
    [
      {
        "OpenDate": "2014.01.02"
      },
      {
        "DishDiscountSumInt": 279318,
        "DishSumInt": 292240,
        "GuestNum": 271,
        "UniqOrderId": 286
      }
    ],
    [
      {
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035,
        "GuestNum": 457,
        "UniqOrderId": 482
      }
    ],
    [
      {
        "OpenDate": "2014.01.01"
      },
      {
        "DishDiscountSumInt": 186521.5,
        "DishSumInt": 198795,
        "GuestNum": 186,
        "UniqOrderId": 196
      }
    ]
  ]
}
```

 [+] [Выручка по официантам](javascript:void%280%29)
 [-] [Выручка по официантам](javascript:void%280%29)
 | ![POST Request](/resources/Storage/api-documentations/http_request_post.png) | 
```
https://localhost:8080/resto/api/v2/reports/olap?key=b785c815-f06d-947c-3fb5-3052a2df7fd8 
```
 |
| --- | --- |

#### Запрос


```json
{
  "reportType": "SALES",
  "groupByRowFields": [
    "WaiterName"
  ],
  "aggregateFields": [
    "DishSumInt",
    "DishDiscountSumInt"
  ],
  "filters": {
    "OpenDate": {
      "filterType": "DateRange",
      "periodType": "CUSTOM",
      "from": "2014-01-01T00:00:00.000", 
      "to": "2014-01-03T00:00:00.000" 
    },
  "DeletedWithWriteoff": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    },
   "OrderDeleted": {
      "filterType": "IncludeValues",
      "values": ["NOT_DELETED"]
    }
  }
}
```


#### Ответ


```json
{
  "data": [
    {
      "DishDiscountSumInt": 36186.25,
      "DishSumInt": 38475,
      "WaiterName": "Water_Name"
      
    },
    {
      "DishDiscountSumInt": 29935,
      "DishSumInt": 31445,
      "WaiterName": "Water_Name"
      
    },
    {
      "DishDiscountSumInt": 76610,
      "DishSumInt": 78970,
      "WaiterName": "Water_Name"
      
    },
    {
      "DishDiscountSumInt": 119425,
      "DishSumInt": 129130,
      "WaiterName": "Water_Name"
      
    },
    {
      "DishDiscountSumInt": 139081.5,
      "DishSumInt": 145085,
      "WaiterName": "Water_Name"
      
    },
    {
      "DishDiscountSumInt": 29708.75,
      "DishSumInt": 31810,
      "WaiterName": "Water_Name"
      
    },
    {
      "DishDiscountSumInt": 34893,
      "DishSumInt": 36120,
      "WaiterName": "Water_Name"
      
    }
    
  ],
  "summary": [
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 29935,
        "DishSumInt": 31445
        
      }
      
    ],
    [
      {
        
        
      },
      {
        "DishDiscountSumInt": 465839.5,
        "DishSumInt": 491035
        
      }
      
    ],
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 29708.75,
        "DishSumInt": 31810
        
      }
      
    ],
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 34893,
        "DishSumInt": 36120
        
      }
      
    ],
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 36186.25,
        "DishSumInt": 38475
        
      }
      
    ],
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 139081.5,
        "DishSumInt": 145085
        
      }
      
    ],
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 119425,
        "DishSumInt": 129130
        
      }
      
    ],
    [
      {
        "WaiterName": "Water_Name"
        
      },
      {
        "DishDiscountSumInt": 76610,
        "DishSumInt": 78970
        
      }
      
    ]
    
  ]
}
```


 
```


```


* [Список преднастроенных не удаленных отчетов (конфигураций)](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/h2__1074633278)
* [Список преднастроенных не удаленных отчетов (конфигураций), отфильтрованных по типу OLAP-отчетов](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/h2__2011681203)
* [Параметры запроса](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/h3__998506674)
* [Получение отчета по сохраненной конфигурации (по ИД)](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/h2__1520457598)
* [Параметры запроса](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/h3__1602332892)
* [Пример запроса](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/h3_1387997121)
* [Тело ответа](/articles/api-documentations/prednastroennye-olap-otchety-vv2/a/id-ПреднастроенныеOLAP-отчеты-ResponseBody)

## Список преднастроенных не удаленных отчетов (конфигураций)

Версия iiko: 4.2

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/reports/olap/presets |
| --- | --- |

## Список преднастроенных не удаленных отчетов (конфигураций), отфильтрованных по типу OLAP-отчетов

Версия iiko: 4.2

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/reports/olap/presets/{presetType} |
| --- | --- |

### Параметры запроса

| Параметр | Описание |
| --- | --- |
| **presetType** | [**stock**, **sales**, **transactions**, **deliveries**]- типы OLAP-отчетов (контроль хранения остатков, продажи, проводки, доставка) |

## 

## Получение отчета по сохраненной конфигурации (по ИД)

Версия iiko: 4.2

| ![GET Request](/resources/Storage/api-documentations/http_request_get.png) | https://host:port/resto/api/v2/reports/olap/byPresetId/{presetId} |
| --- | --- |

### Параметры запроса

| Параметр | Описание |
| --- | --- |
| presetId | UUID пресета (обязательный) |
| summary | Boolean. Вычислять итоговое значение. По умолчанию выставлен в true.<br><br>С Version (iiko) 5.3 |
| dateFrom | дата в формате YYYY-MM-DDThh:mm:ss (необязательный, включена в период) |
| dateTo | дата в формате YYYY-MM-DDThh:mm:ss (необязательный, не включена в период) |
| key | Токен |

Формат сохраненных конфигураций отчетов при обновлении iiko может измениться. Соответственно меняются поля возвращаемого отчета.

Чтобы получать отчет всегда в одном и том же формате, следует передавать полученную из **/v2/reports/olap/presets** конфигурацию в API OLAP-отчетов: **/v2/reports/olap**
Поля агрегации, учитывающие начальный остаток товара и денежный остаток (StartBalance.Amount, StartBalance.Money, FinalBalance.Amount, FinalBalance.Money) вычисляются суммированием всей таблицы проводок **за все время** работы системы (всей базы данных) без каких-либо оптимизаций. То есть, такой запрос может выполняться очень долго и замедлять работу сервера.
Если начальный остаток необходим, оставляйте в этом OLAP-запросе только те поля группировки, по которым он действительно необходим (как правило, это Store и Product.Name), и вызывайте такой запрос **как можно реже** и в **не рабочее** время.
В 5.2 добавлено API для быстрого получения остатков: Отчеты по балансам.

В 5.5 отчеты с остатками оптимизированы с использованием балансовых таблиц ATransactionSum, ATransactionBalance, при условии, что применяются группировки и фильтры по полям из этих таблиц, см. признак StartBalanceOptimizable в описании полей.

### Пример запроса

https://host:port/resto/api/v2/reports/olap/byPresetId/c80230c5-5d47-41d2-a055-367742db889d?key=5c2d45fd-5008-b18e-7f7f-cdc18a088cfd&dateFrom=2025-01-01&dateTo=2025-01-31

### Тело ответа


Код

```
[{
  "id" : "UUID",
   "name" : "Name",
  "reportType": "EnumValue",
  "groupByRowFields": [
    "groupByRowFieldName1",
    "groupByRowFieldName2",
    ...,
    "groupByRowFieldNameN"
  ],
  "groupByColFields": [
    "groupByColFieldName1",
    "groupByColFieldName2",
    ...,
    "groupByColFieldNameL"
  ],
  "aggregateFields": [
    "AggregateFieldName1",
    "AggregateFieldName2",
    ...,
    "AggregateFieldNameM"
  ],
  "filters": {
    filter1,
    filter2,
    ...
    filterK
  }
}
,
...
...
...
]
```





API Specifications - все полное описание сохранено в ФАЙЛЕ API Specifications iiko docs.json - ИЗУЧАЙ ЭТОТ ФАЙЛ!







