class Container:
   'Class for docker container'

   def __init__(self, id, name, image=None, network=None, running=False):
      self.id = id
      self.name = name
      self.image = image
      self.network = network
      self.running = running
