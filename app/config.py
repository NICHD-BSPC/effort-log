import os
import yaml
import dotenv

dotenv.load_dotenv()


class Config(object):

    basedir = os.path.abspath(os.path.dirname(__file__))

    SECRET_KEY = os.environ.get("SECRET_KEY") or "unknown"
    DATABASE_PATH = os.environ.get("DOCKER_DATABASE")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

    PROJECTS_PATH = os.path.join(basedir, "projects.yaml")
    PERSONNEL_PATH = os.path.join(basedir, "personnel.yaml")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # These are loaded into the environment with dotenv.load_dotenv() above.
    def get(var):
        return os.environ.get(var, "")

    DISABLE_LDAP = bool(int(get("DISABLE_LDAP")))
    LDAP_BIND_USER_DN = get("LDAP_BIND_USER_DN")
    LDAP_BIND_USER_PASSWORD = get("LDAP_BIND_USER_PASSWORD")
    LDAP_CERT = get("LDAP_BIND_USER_DN")
    LDAP_HOST = get("LDAP_HOST")
    try:
        LDAP_PORT = int(get("LDAP_PORT"))
    except ValueError:
        LDAP_PORT = 0
    LDAP_BASE_DN = get("LDAP_BASE_DN")
    LDAP_GROUP_DN = get("LDAP_GROUP_DN")
    LDAP_USER_RDN_ATTR = get("LDAP_USER_RDN_ATTR")
    LDAP_USER_LOGIN_ATTR = get("LDAP_USER_LOGIN_ATTR")
    LDAP_USER_SEARCH_SCOPE = get("LDAP_USER_SEARCH_SCOPE")
    ADMIN_USERS = get("ADMIN_USERS")
    LDAP_USE_SSL = get("LDAP_USE_SSL")
    LDAP_CERT = get("LDAP_CERT")
