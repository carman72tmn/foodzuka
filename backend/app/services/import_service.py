"""
Сервис для импорта клиентов из файлов XML и XLSX
"""
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from lxml import etree
import io
import os

logger = logging.getLogger(__name__)

class ImportService:
    @staticmethod
    def parse_xlsx(file_path: str) -> List[Dict[str, Any]]:
        """Парсинг XLSX файла"""
        try:
            logger.info(f"Reading XLSX file: {file_path}")
            # Сначала читаем без заголовков чтобы найти строку с заголовками
            df_raw = pd.read_excel(file_path, header=None)
            logger.info(f"Raw XLSX read. Rows: {len(df_raw)}")
            
            header_row_idx = 0
            # Ищем строку, содержащую как минимум 2 ключевых слова (телефон, имя и т.д.)
            for idx, row in df_raw.iterrows():
                row_str = " ".join([str(c).lower() for c in row if not pd.isna(c)])
                matches = [kw for kw in ['телефон', 'имя отчество', 'email', 'фамилия', 'номер карты'] if kw in row_str]
                if len(matches) >= 2:
                    header_row_idx = idx
                    logger.info(f"Found header at row {idx} with matches {matches}: {row_str}")
                    break
            
            # Если не нашли по 2 совпадениям, пробуем хотя бы одно, но исключая "клиенты доставки"
            if header_row_idx == 0:
                for idx, row in df_raw.iterrows():
                    row_str = " ".join([str(c).lower() for c in row if not pd.isna(c)])
                    if any(kw in row_str for kw in ['телефон', 'email', 'фамилия']) and 'клиенты доставки' not in row_str:
                        header_row_idx = idx
                        logger.info(f"Fallback: Found header at row {idx}: {row_str}")
                        break
            
            # Перечитываем с правильным заголовком
            df = pd.read_excel(file_path, skiprows=header_row_idx)
            logger.info(f"XLSX file read successfully with header at {header_row_idx}. Rows: {len(df)}")
            
            df.columns = [str(c).strip().lower() for c in df.columns]
            logger.info(f"Detected columns: {list(df.columns)}")
            
            # Маппинг колонок (более широкий список ключевых слов)
            mapping_rules = {
                'name': ['имя отчество', 'имя', 'клиент', 'наименование'],
                'surname': ['фамилия'],
                'email': ['email', 'электронная почта', 'почта'],
                'phone': ['№ телефона', 'номер телефона', 'телефон', 'phone', 'контактный'],
                'address': ['адрес'],
                'card_number': ['номер карты', 'карта', 'номер дисконтной'],
                'registration_source': ['источник регистрации'],
                'registration_date': ['дата регистрации'],
                'is_high_risk': ['высокий риск', 'статус риск'],
                'is_synced_to_iiko_cards': ['синхронизирован с iiko', 'iiko.cards'],
                'is_system_notifications_consented': ['уведомления о статусах', 'статусы доставки'],
                'is_loyalty_messages_consented': ['сообщения системы лояльности'],
                'is_marketing_consented': ['реклама', 'рекламная рассылка', 'смс'],
                'birthday': ['дата рождения', 'день рождения', 'родился'],
                'gender': ['пол'],
                'last_order_date': ['дата последнего заказа', 'последний заказ']
            }
            
            # Порядок столбцов из ТЗ (если заголовки не распознаются или для принудительного маппинга)
            tz_column_order = [
                'name', 'surname', 'email', 'phone', 'address', 'card_number',
                'registration_source', 'registration_date', 'is_high_risk',
                'is_synced_to_iiko_cards', 'is_system_notifications_consented',
                'is_loyalty_messages_consented', 'is_marketing_consented',
                'birthday', 'gender', 'last_order_date'
            ]
            
            col_map = {}
            for field, keywords in mapping_rules.items():
                for col in df.columns:
                    if any(kw in col for kw in keywords):
                        col_map[col] = field
                        logger.info(f"Mapped column '{col}' to field '{field}'")
                        break
            
            result = []
            import re
            
            for i, row in df.iterrows():
                item = {}
                additional_phones = []
                additional_addresses = []

                # Если колонок много и заголовки не совпали идеально, используем маппинг по позиции
                if len(df.columns) >= 4 and len(col_map) < 4:
                    if i == 0:
                        logger.info("Using positional mapping as fallback for XLSX")
                        for idx, field in enumerate(tz_column_order):
                            if idx < len(df.columns):
                                col_map[df.columns[idx]] = field

                for col_name, row_val in row.items():
                    field_name = col_map.get(col_name)
                    if not field_name or pd.isna(row_val):
                        continue
                    
                    val_str = str(row_val).strip()
                    
                    # Обработка телефона (может быть несколько через ;)
                    if field_name == 'phone':
                        # Разделяем по ;
                        parts = re.split(r'[;;\n]', val_str)
                        phones_in_row = []
                        for p in parts:
                            p = p.strip()
                            if not p: continue
                            digits = re.sub(r'\D', '', p)
                            if len(digits) >= 6:
                                if digits.startswith('8'):
                                    digits = '7' + digits[1:]
                                phones_in_row.append(digits)
                            else:
                                additional_addresses.append(p)
                        
                        if phones_in_row:
                            item['phone'] = phones_in_row[0]
                            if len(phones_in_row) > 1:
                                additional_phones.extend(phones_in_row[1:])
                    
                    # Обработка адреса (может быть несколько через ;)
                    elif field_name == 'address':
                        parts = val_str.split(';')
                        addresses_in_row = [p.strip() for p in parts if p.strip()]
                        if addresses_in_row:
                            item['address'] = addresses_in_row[0]
                            if len(addresses_in_row) > 1:
                                additional_addresses.extend(addresses_in_row[1:])
                    
                    # Обработка булевых значений
                    elif field_name.startswith('is_'):
                        low_val = val_str.lower()
                        item[field_name] = low_val in ['true', 'yes', '1', 'да', '+', 'v', 'x', 'checked']
                    
                    # Все остальные поля
                    else:
                        item[field_name] = row_val
                
                if item.get('phone'):
                    # Сохраняем списки для последующей обработки в задаче
                    if additional_phones:
                        item['additional_phones'] = additional_phones
                    if additional_addresses:
                        item['additional_addresses'] = additional_addresses
                    
                    result.append(item)
            
            logger.info(f"Successfully parsed {len(result)} customers")
            return result
        except Exception as e:
            logger.error(f"Error parsing XLSX: {e}")
            raise e

    @staticmethod
    def parse_xml(file_path: str) -> List[Dict[str, Any]]:
        """Парсинг XML файла"""
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            result = []
            # Ищем элементы, похожие на клиентов (обычно <Customer> или <item>)
            customers = root.xpath('//Customer') or root.xpath('//item') or root.getchildren()
            
            for cust in customers:
                item = {}
                for child in cust.getchildren():
                    tag = child.tag.lower()
                    text = child.text
                    
                    if 'phone' in tag or 'телефон' in tag:
                        item['phone'] = text
                    elif 'name' in tag or 'имя' in tag:
                        item['name'] = text
                    elif 'surname' in tag or 'фамилия' in tag:
                        item['surname'] = text
                    elif 'email' in tag:
                        item['email'] = text
                    elif 'card' in tag or 'карта' in tag:
                        item['card_number'] = text
                    elif 'gender' in tag or 'пол' in tag:
                        item['gender'] = text
                    elif 'birthday' in tag or 'рождения' in tag:
                        item['birthday'] = text
                
                if item.get('phone'):
                    phone = str(item['phone']).replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
                    if phone.startswith('8'):
                        phone = '7' + phone[1:]
                    item['phone'] = phone
                    result.append(item)
            
            return result
        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            raise e

import_service = ImportService()
