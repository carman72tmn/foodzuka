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
                'is_marketing_consented': ['реклама', 'рекламная рассылка', 'смс'],
                'is_system_notifications_consented': ['уведомления системы'],
                'birthday': ['дата рождения', 'день рождения', 'родился'],
                'gender': ['пол']
            }
            
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
                
                for col_name, row_val in row.items():
                    field_name = col_map.get(col_name)
                    if not field_name or pd.isna(row_val):
                        continue
                    
                    val_str = str(row_val).strip()
                    
                    # Специальная обработка для колонки телефона (может содержать адреса и несколько номеров)
                    if field_name == 'phone':
                        # Разделяем по ; , или переводу строки
                        parts = re.split(r'[;;\n]', val_str)
                        for p in parts:
                            p = p.strip()
                            if not p: continue
                            
                            # Пытаемся понять, это телефон или адрес
                            # Если много цифр - скорее телефон. Если много букв - скорее адрес.
                            digits = re.sub(r'\D', '', p)
                            if len(digits) >= 6 and (p.startswith('+') or p.startswith('7') or p.startswith('8') or re.match(r'^\d', p)):
                                clean_phone = digits
                                if clean_phone.startswith('8'):
                                    clean_phone = '7' + clean_phone[1:]
                                if not item.get('phone'):
                                    item['phone'] = clean_phone
                                else:
                                    additional_phones.append(clean_phone)
                            else:
                                additional_addresses.append(p)
                    else:
                        item[field_name] = row_val
                
                if item.get('phone'):
                    # Сохраняем дополнительные телефоны и адреса в заметки, если они есть
                    notes_parts = []
                    if additional_phones:
                        notes_parts.append(f"Доп. телефоны: {', '.join(additional_phones)}")
                    if additional_addresses:
                        notes_parts.append(f"Доп. адреса: {', '.join(additional_addresses)}")
                    
                    if notes_parts:
                        existing_notes = str(item.get('notes', '')) if item.get('notes') else ""
                        item['notes'] = (existing_notes + "\n" + "\n".join(notes_parts)).strip()
                    
                    # Если есть основной адрес из колонки Адрес, объединяем его
                    if additional_addresses and not item.get('address'):
                        item['address'] = additional_addresses[0]
                        
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
