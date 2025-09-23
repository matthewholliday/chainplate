from ..data.data_service import DataService
import traceback

class LoggingService:

    @staticmethod
    def log_message(level: str, message: str):
        try:
            data_service = DataService()
            data_service.insert_log(level, message)
        except Exception as e:
            print(f"error while attempting to log message: {e} {traceback.format_tb(e.__traceback__)}")
        finally:
            data_service.close()

    @staticmethod
    def log_info(message: str):
        LoggingService.log_message("INFO", message)
    
    @staticmethod
    def log_warning(message: str):
        LoggingService.log_message("WARNING", message)  

    @staticmethod
    def log_error(message: str):
        LoggingService.log_message("ERROR", message)


