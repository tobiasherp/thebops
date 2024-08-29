import os, sys
import locale
import gettext

# Change this variable to your app name!
#  The translation files will be under 
#  @LOCALE_DIR@/@LANGUAGE@/LC_MESSAGES/@APP_NAME@.mo
#
APP_NAME = __package__

# This is ok for maemo. Not sure in a regular desktop:
#
APP_DIR = os.path.join(sys.prefix, 'share')
LOCALE_DIR = os.path.join(APP_DIR, 'locale')


# Now we need to choose the language. We will provide a list, and gettext
# will use the first translation available in the list
#
#  In maemo it is in the LANG environment variable
#  (on desktop is usually LANGUAGES)
#
#  q: is this pathsep (';' on Windows etc.), ---------.
#     or is it a literal ':'?                         |
DEFAULT_LANGUAGES = os.environ.get('LANG', '').split(':')
# <http://docs.python.org/2/library/gettext.html#gettext.bindtextdomain> says:
# ... where languages is searched for in the environment variables
#     LANGUAGE, LC_ALL, LC_MESSAGES, and LANG respectively
DEFAULT_LANGUAGES += ['en_US']

# Try to get the languages from the default locale
languages = []
lc, encoding = locale.getdefaultlocale()
if lc:
    languages = [lc]

# Concat all languages (env + default locale), 
#  and here we have the languages and location of the translations
#
languages += DEFAULT_LANGUAGES
mo_location = LOCALE_DIR

# Lets tell those details to gettext
#  (nothing to change here for you)
gettext.install(True)
gettext.bindtextdomain(APP_NAME,
                       mo_location)
gettext.textdomain(APP_NAME)
language = gettext.translation(APP_NAME,
                               mo_location,
                               languages=languages,
                               fallback=True)

# And now in your modules you can do:
#
# import i18n
# _ = i18n.language.gettext
#

