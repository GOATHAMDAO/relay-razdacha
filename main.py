from runner.runner import Runner
from utils.constants import logo, PROJECT, TG_CHANNEL
from utils.utils import load_private_key, load_recipients
from loguru import logger
import sys

# Настройка логгера
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    colorize=True
)


def main():
    # Выводим логотип и информацию о проекте
    logger.opt(raw=True, colors=True).info(logo)
    logger.opt(raw=True, colors=True).info(PROJECT)
    
    # Ссылка на телеграм канал
    logger.opt(raw=True, colors=True).info(
        f"\n<yellow>════════════════════════════════════════════════════════════════</yellow>\n"
        f"<cyan>  📢 Подписывайся на канал: </cyan><light-blue>{TG_CHANNEL}</light-blue>\n"
        f"<yellow>════════════════════════════════════════════════════════════════</yellow>\n\n"
    )

    try:
        # Загружаем данные
        private_key = load_private_key()
        recipients = load_recipients()

        logger.info(f"✅ Загружен приватный ключ")
        logger.info(f"✅ Загружено {len(recipients)} адресов получателей\n")

        # Создаём и запускаем раннер
        runner = Runner(private_key, recipients)
        runner.run_interface()

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {e}")
        logger.info("Убедитесь, что файлы private_key.txt и recipients.txt находятся в папке user_data/")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

