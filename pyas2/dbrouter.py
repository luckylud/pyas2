

class Pyas2dbRouter:
    """
    A router to control all database operations on models in the
    pyas2 application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read pyas2 models go to pyas2 db.
        """
        if model._meta.app_label == 'pyas2':
            return 'pyas2'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write pyas2 models go to pyas2 db.
        """
        if model._meta.app_label == 'pyas2':
            return 'pyas2'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the pyas2 app is involved.
        """
        if obj1._meta.app_label == 'pyas2' or\
                obj2._meta.app_label == 'pyas2':
                return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the pyas2 app only appears in the 'pyas2'
        database.
        """
        if app_label == 'pyas2':
            return db == 'pyas2'
        return None
