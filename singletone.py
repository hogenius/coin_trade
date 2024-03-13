class SingletonInstane:
  __instance = None

  @classmethod
  def __getInstance(cls):
    return cls.__instance

  @classmethod
  def Instance(cls, *args, **kargs):
    cls.__instance = cls(*args, **kargs)
    cls.Instance = cls.__getInstance
    return cls.__instance