"""
Variant Explorer - быстрый анализ генетических вариантов
Для BIOCAD × Genotek интенсив
"""

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# Настройка страницы
st.set_page_config(
    page_title="Variant Explorer",
    page_icon="🧬",
    layout="wide"
)

# Заголовок
st.title("🧬 Variant Explorer")
st.markdown("*Быстрый анализ клинической значимости генетических вариантов*")

# Боковая панель с информацией
with st.sidebar:
    st.markdown("## 📖 О инструменте")
    st.markdown("""
    Анализирует генетические варианты (rs-идентификаторы) используя:
    - **ClinVar** - клиническая значимость
    - **gnomAD** - популяционные частоты
    - **dbSNP** - аннотация варианта
    
    *Данные агрегируются через MyVariant.info API*
    """)
    
    st.markdown("## 🧪 Примеры для тестирования")
    st.code("""
    rs429358   (APOE, Alzheimer's)
    rs1801133  (MTHFR, homocysteine)
    rs113488022 (BRAF, cancer)
    rs121913529 (TP53, Li-Fraumeni)
    """)
    
    st.markdown("---")
    st.caption(f"API запросов сегодня: {datetime.now().strftime('%Y-%m-%d')}")

# Основное поле ввода
variant_id = st.text_input(
    "Введите rs-идентификатор варианта:",
    placeholder="Пример: rs429358",
    help="Формат: rs + число (например, rs429358)"
)

def query_myvariant(rs_id):
    """Запрос к MyVariant.info API"""
    url = f"https://myvariant.info/v1/variant/{rs_id}"
    
    # Параметры для получения всех аннотаций
    params = {
        'fields': 'clinvar,dbsnp,gnomad_exome,genomic'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ошибка API: {e}")
        return None

def parse_clinical_significance(clinvar_data):
    """Парсинг клинической значимости"""
    if not clinvar_data:
        return "Нет данных"
    
    # Стандартизированные категории ClinVar
    categories = {
        'pathogenic': '🔴 Патогенный',
        'likely_pathogenic': '🟠 Вероятно патогенный',
        'uncertain': '🟡 Неопределенная значимость',
        'likely_benign': '🟢 Вероятно доброкачественный',
        'benign': '✅ Доброкачественный',
        'drug_response': '💊 Связан с ответом на лекарства',
        'risk_factor': '⚠️ Фактор риска'
    }
    
    significance = clinvar_data.get('clinical_significance', '')
    
    for key, value in categories.items():
        if key in significance.lower():
            return value
    
    return f"ℹ️ {significance if significance else 'Не классифицирован'}"

def create_info_card(data, variant_name):
    """Создание карточки с информацией"""
    
    # Извлечение данных
    clinvar = data.get('clinvar', {})
    dbsnp = data.get('dbsnp', {})
    gnomad = data.get('gnomad_exome', {})
    
    # Основная информация
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📋 Основная информация")
        st.markdown(f"**Вариант:** `{variant_name}`")
        
        # Ген из dbsnp или clinvar
        gene = dbsnp.get('gene', {}).get('name', 
                clinvar.get('gene', {}).get('symbol', 'Неизвестен'))
        st.markdown(f"**Ген:** {gene}")
        
        # Тип варианта
        variant_type = dbsnp.get('variant_type', 'Не указан')
        st.markdown(f"**Тип:** {variant_type}")
    
    with col2:
        st.markdown("### 🏥 Клиническая значимость")
        significance = parse_clinical_significance(clinvar)
        st.markdown(f"**Значимость:** {significance}")
        
        # Условия/заболевания
        conditions = clinvar.get('conditions', [])
        if conditions:
            st.markdown("**Связанные состояния:**")
            for cond in conditions[:3]:
                st.markdown(f"- {cond.get('name', 'Неизвестно')}")
    
    with col3:
        st.markdown("### 🌍 Популяционные частоты (gnomAD)")
        if gnomad:
            af = gnomad.get('af', 0)
            if af:
                for key in af:
                    st.markdown(f"**{key}:** {af[key]:.4f} ({af[key]*100:.2f}%)")
            
            # Популяционные подгруппы
            populations = {
                'Европа': gnomad.get('af_eas', 0),
                'Азия': gnomad.get('af_nfe', 0),
                'Африка': gnomad.get('af_afr', 0)
            }
            
            for pop, freq in populations.items():
                if freq > 0:
                    st.markdown(f"- {pop}: {freq:.4f} ({freq*100:.2f}%)")
        else:
            st.markdown("*Нет данных в gnomAD*")
    
    return {
        'gene': gene,
        'significance': significance,
        'conditions': [cond.get('name', '') for cond in conditions[:3]]
    }

def show_clinical_trials(gene):
    """Поиск клинических исследований по гену (доп. фича)"""
    url = "https://clinicaltrials.gov/api/query/study_fields"
    
    params = {
        'expr': f'AREA[Condition]{gene}|AREA[InterventionName]{gene}',
        'fields': 'NCTId,BriefTitle,OverallStatus',
        'fmt': 'json',
        'min_rnk': 1,
        'max_rnk': 5
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            studies = data.get('StudyFieldsResponse', {}).get('StudyFields', [])
            
            if studies:
                st.markdown("### 🔬 Актуальные клинические исследования")
                for study in studies[:3]:
                    nct_id = study.get('NCTId', [''])[0]
                    title = study.get('BriefTitle', [''])[0]
                    status = study.get('OverallStatus', [''])[0]
                    
                    st.markdown(f"**{title}**")
                    st.markdown(f"ID: {nct_id} | Статус: {status}")
                    st.caption(f"[Подробнее](https://clinicaltrials.gov/ct2/show/{nct_id})")
    except:
        pass

# Основная логика
if variant_id:
    with st.spinner(f"🔍 Анализ варианта {variant_id}..."):
        data = query_myvariant(variant_id)
        
        if data and data.get('_id'):
            st.success(f"✅ Успешно загружены данные для {variant_id}")
            
            # Основная информация
            info = create_info_card(data, variant_id)
            
            # Дополнительные секции
            st.markdown("---")
            
            # Сырые данные (для разработчиков)
            with st.expander("📊 Подробные данные API"):
                st.json(data)
            
            # Поиск клинических исследований
            if info.get('gene') and info['gene'] != 'Неизвестен':
                show_clinical_trials(info['gene'])
            
            # Интерпретационная заметка
            st.markdown("---")
            st.markdown("### 💡 Интерпретационная заметка")
            
            if "патоген" in info['significance'].lower():
                st.warning("""
                🧬 **Внимание:** Этот вариант ассоциирован с заболеванием.
                
                **Рекомендации:**
                - Консультация генетика
                - Семейное консультирование при необходимости
                - Мониторинг клинических проявлений
                """)
            elif "доброкачествен" in info['significance'].lower():
                st.info("""
                ✅ **Хорошая новость:** Вариант классифицируется как доброкачественный.
                
                Клинической значимости не имеет, не требует дополнительного наблюдения.
                """)
            else:
                st.info("""
                📊 **Требуется дополнительный анализ:** Вариант имеет неопределенную клиническую значимость.
                
                Рекомендуется поиск литературы и консультация с экспертом.
                """)
            
        else:
            st.error(f"❌ Вариант {variant_id} не найден в базах данных")
            st.markdown("""
            **Возможные причины:**
            - Неправильный формат (нужно rs + число)
            - Редкий вариант, отсутствующий в публичных базах
            - Проблемы с соединением с API
            """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <small>
        Данные предоставлены MyVariant.info API | 
        Сделано для BIOCAD × Genotek интенсив 🧬
    </small>
</div>
""", unsafe_allow_html=True)