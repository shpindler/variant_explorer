# 1. Установить зависимости
```bash
pip install -r requirements.txt
```
# 2. Запустить приложение
```bash
streamlit run app.py
```
# Приложение откроется в браузере на http://localhost:8501

# Альтернативно запуск через Docker
```bash
docker build -t variant-explorer .
docker run -p 8501:8501 variant-explorer
```