from shared.utils.log import Logger

logger = Logger('print', print_log=True)
logger.info('info poruka')
logger.warning('warning poruka')
logger.error('error poruka')

logger2 = Logger('file.size', print_log=True, filename='datoteka.log')
# while True:
#     logger2.info('info poruka')
#     logger2.warning('warning poruka')
#     logger2.error('error poruka')

logger3 = Logger('file2.size', print_log=True, filename='datoteka2.log',
                 depends_on=Logger.DEPENDS_ON_SIZE, max_file_size='200kb')
# while True:
#     logger3.info('info poruka')
#     logger3.warning('warning poruka')
#     logger3.error('error poruka')

logger4 = Logger('file4.size', print_log=True, filename='datoteka3.log',
                 depends_on=Logger.DEPENDS_ON_SIZE, max_file_size='100kb',
                 max_files=3, rotate=True)
while True:
    logger4.info('info poruka')
    logger4.warning('warning poruka')
    logger4.error('error poruka')
