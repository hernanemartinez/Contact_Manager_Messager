from csv_reader import CSVManager
from entities import Contacto
from system import LogMngr
from entities import Contacto
from system_messenger import LogMngr
from system import StringCoder
from dao import DAO
from csv_reader import CSVManager
from entities import Contacto
from system import LogMngr

import sys
import logging
import locale
import sqlite3 as sqlite
#from pysqlite2 import dbapi2 as sqlite
import logging
#import unicodecsv as csv
import csv
import smtplib
import sys
import logging
import locale
import chardet

'''
The encoding class definition
'''
class StringCoder():

    '''
    Decodes the data that comes from the CSV file and transforms it to UNICODE
    '''
    def encode(self, stringValue):
        #TODO: We need a better way to transform the data to unicode. Currently it just replaces the conflicting chars or leaves it as it is.
        coding = str(chardet.detect(stringValue)["encoding"])
        try:
            valor = unicode(stringValue, coding)
        except:
            valor = stringValue

        return valor

'''
The system management classes goes here.
'''
class LogMngr():

    logger = None

    '''
    Constructor initializes the base logging configuration.
    '''
    def __init__(self, logger_name):

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        #fh = logging.StreamHandler() #this is to print it in the common console.
        fh = logging.FileHandler('importing_database_data.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    '''
    Prints INFO kind of data.
    '''
    def info(self, valor):
        self.logger.info(valor)

    '''
    Prints ERRORS kind of data.
    '''
    def error(self, valor):
        self.logger.info(valor)

    '''
    Prints DEBUG kind of data.
    '''
    def debug(self, valor):
        self.logger.debug(valor)

class Importer():
    '''
    This class imports contacts into the SQLite database; it manages different data structures.
    '''

    def import_Linkedin_Csv_Contacts(dataFile):
        '''Just loads the database with the CSV data obtained from linkedin. It serves their data structure.'''

        from dao import DAO
        log = LogMngr("Importer.import_linkedin_csv_contacts")

        if (dataFile!=None):
            log.info("Processing the CSV file exported from LinkedIn (c) 2016 -> " + str(dataFile))

            dao = DAO()
            csvMng = CSVManager()

            #iterates over the list of contacts and instroduces it into the database.
            dao.open_connection()

            log.info("Database connection online.")
            contactos = csvMng.getContactos(str(dataFile))

            #TODO: Classify the contact; analize its data and tag it or typify it.
            for conta in contactos:
                #TODO: perform updates, when the record already exists.
                result = dao.exec_new_single_contacto(conta) #inserts new data.

                if (result == dao.SQLITE_CONSTRAINT_UNIQUE):
                    result = dao.exec_upd_single_contacto(conta) #updates the same record with new data.

            dao.close_connection()
            log.info("Database connection closed.")

            log = None

            return True

        else:
            log.error("Datafile name to import laking.")
            log = None

            return False

class MailingManager:

    server = smtplib.SMTP('smtp.gmail.com:587') #TODO Replace this for a parameter extracted from a configuration file or some other thing.

    #System controllers: logs and others
    log = LogMngr("mailing_manager")

    def login(self, username, password):
        '''This allows the entire app to login'''
        try:
            #This is an example of Google Mail:
            self.server.ehlo()
            self.server.starttls()
            self.server.login(username,password)

            self.log.info( "Usuario " + username + " conectado.")

        except:
            self.log.error("""Error: el usuario, password o servidor son erroneos.""")

    def sendMail(self, mensaje, remitente, destinatario, asunto):
        '''Sends a mail to a given account.'''
        #Message basic and standard template.
        msg = "\r\n".join([
          "From: " + remitente,
          "To: " + destinatario,
          "Subject: " + asunto,
          "",
          mensaje
          ])

        try:

            self.server.sendmail(remitente, destinatario, msg)

            log.info( "Correo enviado a " + destinatario + ".")

        except:
            log.error("""Error: el mensaje no pudo enviarse.
            Compruebe que sendmail se encuentra instalado en su sistema""")

    def logOout(self):
        '''Logs out from the user mail account'''
        self.server.quit()

class CSVManager():

    logger = logging.getLogger()

    '''
    Just reads the passed as parameter filename and prints its contents out of the box. - This is just for checking the file structure and show it to the user, purposes.
    '''
    def read_csv_print(self, file_name):
        with open(file_name, 'rb') as f: #watch it: this file HAS to be a CSV file...
            reader = csv.reader(f)
            try:
                for row in reader:
                    print row[1] + " " + row[3] + " e-mail: " + row[5] + " compania: " + row[29] + " posicion (job title): " + row[31]
            except (IndexError):
                print "Minor Error: Index out of bounds (end of file unexpectedly reached)."

    '''
    returns a set with all the data extracted from the CSV; this set is an object suitable for the database.
    '''
    def getContactos(self, file_name):

        contactos = set()

        with open(file_name , 'rb') as f:
            reader = csv.reader(f)
            try:
                for row in reader:

                    if (row[1] == "First Name"):
                        continue

                    conta = Contacto()

                    conta.setNombre(row[1])
                    conta.setApellido(row[3])
                    conta.setEmail(row[5])
                    conta.setCompania(row[29])
                    conta.setPosicion(row[31])

                    contactos.add(conta)

            except (IndexError):
                self.logger.error("Minor Error: Index out of bounds (end of file unexpectedly reached).")

        return contactos



class DAO (object):

    SQLITE_CONSTRAINT_UNIQUE = 2067
    SQLITE_CONSTRAINT = 19
    SQLITE_ERROR = 1
    SQLITE_OK = 0

    log = LogMngr("database_transactions")

    '''
    Updates a contact with new data into the database
    '''
    def exec_upd_single_contacto(self, contacto):

        try:

            result = self.cursor.execute("update contactos set nombre = ?, apellido = ?, email = ?, compania = ?, posicion = ?, tipo = ? where email = ?", (contacto.getNombre(), contacto.getApellido(), contacto.getEmail(), contacto.getCompania(), contacto.getPosicion(), contacto.getTipo(), contacto.getEmail()))
            self.connection.commit()

        except sqlite.IntegrityError as er:
            self.log.error("Database Error: " + str(er.args))
            if (str(er.message)[:6]=="UNIQUE"):
                return self.SQLITE_CONSTRAINT_UNIQUE #Unique constraint failed.
            else:
                return self.SQLITE_CONSTRAINT

        except sqlite.Error as er:
            self.log.error("Database Error: " + er.message)
            self.log.error("The database insert failed with contacto: " + contacto.getNombre() + " " + contacto.getApellido())
            self.connection.rollback()
            return self.SQLITE_ERROR #SQLite error or missing database

        return self.SQLITE_OK #sqlite OK! yey!

    '''
    Inserts a new contact into the database
    '''
    def exec_new_single_contacto(self, contacto):

        try:

            result = self.cursor.execute("insert into contactos (nombre, apellido, email, compania, posicion, tipo) values (?, ?, ?, ?, ?, ?)", (contacto.getNombre(), contacto.getApellido(), contacto.getEmail(), contacto.getCompania(), contacto.getPosicion(), contacto.getTipo(),))
            self.connection.commit()

        except sqlite.IntegrityError as er:
            self.log.error("Database Error: " + str(er.args))
            if (str(er.message)[:6]=="UNIQUE"):
                return self.SQLITE_CONSTRAINT_UNIQUE #Unique constraint failed.
            else:
                return self.SQLITE_CONSTRAINT

        except sqlite.Error as er:
            self.log.error("Database Error: " + er.message)
            self.log.error("The database insert failed with contacto: " + contacto.getNombre() + " " + contacto.getApellido())
            self.connection.rollback()
            return 1 #SQLite error or missing database

        return 0 #sqlite OK! yey!

    def exec_delete_tipo_contacto(self, tipo):
        '''
        Deletes all the contacto's records with the given tipo.
        '''
        try:

            self.cursor.execute("delete from contactos where tipo=?", (str(tipo),))
            self.connection.commit()

        except:
            self.log.error("The database deletion by TIPO failed with TIPO: " + str(tipo))
            self.connection.rollback()
            return False

        return True

    def exec_get_contacto_exists_byCompania(self, compania):
        '''
        Returns one, single sub categoria by its URL
        '''
        self.cursor.execute("select * from contactos where compania=?", (compania,))
        return self.cursor.fetchone()

    def exec_get_contactos_exists_byEmail(self, email):
        '''
        Returns one, single contacto by its URL
        '''
        self.cursor.execute("select * from contactos where email=?", (email,))
        result = self.cursor.fetchone()

        self.log.debug("search ---- " + str(result))
        return result

    def exec_get_all_contactos(self):
        '''
        Returns every categoria that is in place (full scan)
        '''
        self.log.debug("Fetching...")
        self.cursor.execute("select id, nombre, apellido, email, compania, posicion, tipo from contactos")

        return self.cursor.fetchall()

    def open_connection(self):
        '''
        Sets the due connections to the data stores.
        '''

        self.log.debug("Initiating database")
        # Initializes the connection to SQLite (and creates the due tables)
        self.connection = sqlite.connect('./contactos.db')
        self.connection.text_factory = str

        self.cursor = self.connection.cursor()

        #Creates the database TABLES, if there is NONE
        self.cursor.execute('CREATE TABLE IF NOT EXISTS contactos ' \
                    '(id INTEGER PRIMARY KEY, nombre varchar(40), apellido varchar(40), email varchar(140) UNIQUE, compania varchar(140), posicion varchar(140), tipo varchar(40))')

        self.log.debug("Database, READY to throw operations at her.")

    def close_connection(self):
        '''
        Closes the database connection to avoid issues related to the connectivity.
        '''
        self.log.debug("Database offline.")
        self.cursor.close()

class Contacto():
    '''
    The entity of "Contactos" in the database; one instance = one row.
    '''

    nombre = ""
    apellido = ""
    email = ""
    compania = ""
    posicion = ""
    tipo = ""

    scoder = StringCoder()

    #setters y getters.
    def getNombre(self):
        return self.nombre
    def setNombre(self, valor):
        self.nombre = self.scoder.encode(str(valor))

    def getApellido(self):
        return self.apellido
    def setApellido(self, valor):
        self.apellido = self.scoder.encode(str(valor))

    def getEmail(self):
        return self.email
    def setEmail(self, valor):
        self.email = self.scoder.encode(str(valor))

    def getCompania(self):
        return self.compania
    def setCompania(self, valor):
        self.compania = self.scoder.encode(str(valor))

    def getPosicion(self):
        return self.posicion
    def setPosicion(self, valor):
        self.posicion = self.scoder.encode(str(valor))

    def getTipo(self):
        return self.tipo
    def setTipo(self, valor):
        self.tipo = self.scoder.encode(str(valor))

'''
This imports the CSV into the SQLite database.
'''
if __name__ == "__main__":

    log = LogMngr("import_database")

    if (len(sys.argv) > 1):
        log.info("Processing the CSV file exported from LinkedIn (c) 2016 -> " + str(sys.argv[1]))

        dao = DAO()
        csvMng = CSVManager()

        #iterates over the list of contacts and instroduces it into the database.
        dao.open_connection()

        log.info("Database connection online.")
        contactos = csvMng.getContactos(str(sys.argv[1]))

        #TODO: Classify the contact; analize its data and tag it or typify it.
        for conta in contactos:
            #TODO: perform updates, when the record already exists.
            result = dao.exec_new_single_contacto(conta) #inserts new data.

            if (result == dao.SQLITE_CONSTRAINT_UNIQUE):
                result = dao.exec_upd_single_contacto(conta) #updates the same record with new data.

        dao.close_connection()
        log.info("Database connection closed.")